# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Đức Duy
**Nhóm:** C401-F2
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai text chunk có cosine similarity cao nghĩa là các vector embedding của chúng gần như cùng hướng trong không gian nhiều chiều, có nghĩa là chúng mang nội dung hoặc ý nghĩa tương tự nhau, độc lập với độ dài của từng văn bản.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi muốn trả hàng và hoàn tiền."
- Sentence B: "Tôi muốn gửi yêu cầu hoàn trả sản phẩm."
- Tại sao tương đồng: Cả hai đều muốn thực hiện cùng một thao tác (trả lại đồ đã mua và lấy lại tiền), từ vựng đồng nghĩa nên embedding phản ánh chung một ý nghĩa từ nội dung.

**Ví dụ LOW similarity:**
- Sentence A: "Thời tiết hôm nay thật đẹp."
- Sentence B: "Tiền hoàn về ví ShopeePay mất bao lâu?"
- Tại sao khác: Hai câu nói về hai lĩnh vực hoàn toàn không liên quan (thời tiết và dịch vụ tài chính/TMĐT).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Bởi vì cosine similarity chỉ đo góc giữa 2 vector mà bỏ qua yếu tố độ lớn (magnitude/chiều dài vector). Trong NLP, độ dài văn bản không quan trọng bằng ngữ nghĩa, một đoạn trích dài và một câu ngắn tóm tắt hoàn toàn có thể mang chung nghĩa. 

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 22.11`
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Trình bày phép tính:* `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 24.75` 
> *Đáp án:* 25 chunks. (Số lượng chunks tăng lên)
> *Tại sao muốn overlap nhiều hơn:* Tránh việc các thông tin quan trọng bị cắt đứt giữa hai chunk cạnh nhau, overlap giúp duy trì bối cảnh (context) liền mạch giữa cuối chunk này và đầu chunk kia.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Chính sách & Hỗ trợ khách hàng Shopee (Ví dụ: Trả hàng, Hoàn tiền, Đồng kiểm)

**Tại sao nhóm chọn domain này?**
> Domain này chứa các thông tin FAQ có cấu trúc rất rõ ràng, tính thực tiễn cao vì người dùng TMĐT thường xuyên phải tra cứu. Thông tin dễ dàng tạo test case để đánh giá các tình huống truy xuất (multi-aspect) hoặc check xem AI có bị ảo giác về thời hạn và số liệu hay không.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | shopee_chinh_sach_tra_hang_hoan_tien.md | help.shopee.vn | 27,287 | category: "policy", topic: "return_refund", lang: "vi" |
| 2 | shopee_dong_kiem.md | help.shopee.vn | 9,948 | category: "faq", topic: "dong_kiem", lang: "vi" |
| 3 | shopee_huy_don_hoan_voucher.md | help.shopee.vn | 7,641 | category: "faq", topic: "voucher_refund", lang: "vi" |
| 4 | shopee_phuong_thuc_tra_hang.md | help.shopee.vn | 9,467 | category: "guide", topic: "return_method", lang: "vi" |
| 5 | shopee_quy_dinh_chung_tra_hang.md | help.shopee.vn | 9,014 | category: "policy", topic: "return_rules", lang: "vi" |
| 6 | shopee_thoi_gian_hoan_tien.md | help.shopee.vn | 7,346 | category: "faq", topic: "refund_timeline", lang: "vi" |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | "policy", "faq", "guide" | Hỗ trợ filter những truy vấn muốn tra cứu dạng tài liệu nào cụ thể. |
| topic | string | "return_refund", "dong_kiem" | Thu hẹp vùng search, hạn chế search context đụng độ nhau khi các file đều nói về "trả hàng". |
| lang | string | "vi" | Hữu ích để phân loại sau này nếu tích hợp tài liệu tiếng Anh. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên một số tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| shopee_chinh_sach... | FixedSizeChunker | 47 | 497 | Rất tệ — cắt giữa từ hoặc cụm quan trọng |
| shopee_chinh_sach... | SentenceChunker | 56 | 374 | Tạm — dễ bị hụt ý do chunk quá nhỏ |
| shopee_chinh_sach... | RecursiveChunker | 66 | 317 | Trung bình — dễ bị vụn mảnh nếu failback sâu |

### Strategy Của Tôi

**Loại:** Custom Strategy - `AgenticChunker`

**Mô tả cách hoạt động:**
> Rời bỏ các Hardcode Regex hay cơ chế tách gộp dựa vào kí tự. Tôi khởi tạo một module tận dụng trực tiếp LLM với chỉ thị "Đọc văn bản sau và phân tách nó thành các mẩu thông tin (chunks) có ý nghĩa và hoàn chỉnh ngữ cảnh. Mỗi khối thông tin phải trả lời chứa đựng nội dung có thể đứng độc lập dùng trong RAG." AI đọc toàn bộ file và nhả về JSON array.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tài liệu Shopee mặc dù có cấu trúc FAQ nhưng bên trong một câu trả lời lại có vô vàn "bảng/table, điều khoản nhỏ rải rác". Các thuật toán cơ khí của chẻ dòng, Regex (hay cả SentenceChunker) bị hở sườn khi thông tin định nghĩa, giải thích nằm trên 2 dòng cách xa nhau. Agentic Chunking chủ động "nhìn thấu" và đóng gói các mảng ý nghĩa trọn vẹn dứt điểm rủi ro chia tách data.

**Code snippet (nếu custom):**
```python
class AgenticChunker:
    """
    Sử dụng LLM (vd: gpt-4o-mini) để phân tách văn bản bằng mặt ngữ nghĩa thực thụ 
    chứ không phải bằng công thức chia câu vật lý.
    """
    def __init__(self, llm_fn: callable) -> None:
        self.llm_fn = llm_fn

    def chunk(self, text: str) -> list[str]:
        prompt = f'''
        Bên dưới là một văn bản quy định chính sách khá dài. 
        Hãy chia nó thành các mẩu thông tin (chunks) hoàn thiện, sao cho mỗi chunk 
        có thể độc lập cung cấp thông tin hữu ích để trả lời cho một người dùng.
        Bạn phải cung cấp nguyên vẹn nội dung gốc dạng JSON array of strings (["chunk 1", "chunk 2"]):

        Văn bản:
        {text}
        '''
        response_json = self.llm_fn(prompt)
        import json
        try:
            chunks = json.loads(response_json)
        except Exception:
            # Fallback in case LLM outputs non-valid JSON
            chunks = text.split("\n\n")
            
        return [c for c in chunks if c.strip()]
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| shopee_chinh_sach... | SentenceChunker (best baseline) | 56 | 374 | Trung bình — chunk thiếu context |
| shopee_chinh_sach... | **AgenticChunker (Của tôi)** | **12** | **~2450** | **Tuyệt đỉnh — Trọn vẹn mẩu hội thoại FAQ** |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Điểm Của Nhóm | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Hoàng Vĩnh Giang | Custome Recursive Strategy | 8/10 | Chunking dựa theo cấu trúc của tài liệu, đảm bảo tính toàn vẹn của thông tin đoạn văn. | Với những đoạn dài chunk có thể vượt quá lượng ký tự cho phép của mô hình embedding. |
| Nhữ Gia Bách | SemanticChunker | 8/10 | Chunk đúng chủ đề, score distribution rõ. | Thiếu thông tin số liệu cụ thể khi chunk tách rời context. |
| Trần Quang Quí | DocumentStructureChunker | 9/10 (Avg: 0.628) | Chunk bám sát cấu trúc Q&A, context coherent, không bị cắt giữa điều khoản. | Multi-aspect query (Q3) score thấp 0.59 vì định nghĩa và hướng dẫn nằm ở 2 chunk khác nhau. |
| Đoàn Nam Sơn | Parent-Child Chunking | 9/10 (Avg: 0.660) | Chunk hoạt động rất tốt, cắt đúng theo pattern Q&A, không bị cắt giữa điều khoản, rất phù hợp đối xứng các tài liệu có cấu trúc rõ. | Với các tài liệu không có cấu trúc rõ ràng thì có thể không hiệu quả. |
| Vũ Đức Duy (Tôi) | Agentic Chunker | 9/10 (Avg: 0.669) | Gom ngữ nghĩa cực sâu, chia văn bản rành mạch (cắt gọn giảm 4 lần lượng chunks thừa). Score cao nhất. | Phải gọi API tốn kém kinh phí, index siêu chậm, phụ thuộc vào chất lượng parser. |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Xét về chất lượng ngõ ra tuyệt đối: `AgenticChunker` là strategy "tối thượng" bởi vì mô hình sinh (generative) tự quyết định biên giới đoạn văn, bảo vệ thông tin đa chiều. Xét về bài toán Production rẻ và mạnh: `Parent-Child` hay `DocumentStructureChunker` của hai bạn Sơn, Quí là một biện pháp kỹ thuật rẻ mà vẫn có hiệu năng xuất sắc bám sát với sườn tài liệu.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi sử dụng regex (`(?<=[.!?])\s+`) kèm "lookbehind" để tìm các vị trí ngắt câu. Để các câu không quá mồ côi (orphans) lẻ tẻ, tôi tích lũy chúng vào buffer cho đến khi đạt `max_sentences_per_chunk` thì join chúng lại và append vào results array.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Approach đệ quy. Hàm `_split` kiểm tra văn bản đầu vào: nếu nhỏ hơn chuNks limit thì giữ nguyên. Ngược lại, lấy separator đầu tiên `\n\n` cắt ra. Dồn từng piece vào buffer, nếu chạm ngưỡng max size tôi tiếp tục gọi đệ quy `_split()` trên buffer đó với cấp độ separator kế tiếp (`\n`, `.`...). Lỡ cạn kho các separators thì switch về chia rẽ hard-split.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Sử dụng in-memory thuần túy. `add_documents` vòng loop từng doc, sinh dict với id phân rã và apply embed vector trực tiếp. Hàm `search` loop đè lên Records để _dot (Cosine tính) khoảng cách so với câu hỏi.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` chạy quá trình pre-filter mảng list bằng Python comprehension (chặn lại những meta-data không khớp) -> chỉ pass vector đã thoả vào đo dot_product, tăng độ chính xác 100%. Delete là thao tác lọc loại bỏ matching thông qua `doc_id`.

### KnowledgeBaseAgent

**`answer`** — approach:
> Triển khai luồng RAG cơ bản. Call `store.search` parameter `top_k=3` -> Lấy chuỗi content join bằng `\n` -> Tiêm vào template Prompt ép LLM trả lời "If not in context, say I don't know" rồi inject thẳng User's Question xuống dưới.

### Test Results

```text
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-8.0.0, pluggy-1.4.0
collected 42 items

... (Trích xuất) ...
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.08s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn trả hàng và hoàn tiền. | Tôi muốn gửi yêu cầu hoàn trả sản phẩm. | high | 0.7141 | Yes |
| 2 | Shopee hoàn tiền trong 24 giờ. | Tiền sẽ về tài khoản sau một ngày. | high | 0.5101 | Yes |
| 3 | Đồng kiểm là kiểm tra ngoại quan khi nhận hàng. | Phí vận chuyển được hoàn lại sau 3-5 ngày. | low | 0.4067 | Yes |
| 4 | Con mèo đang ngủ trên ghế sofa. | Tiền hoàn về ví ShopeePay mất bao lâu? | low | 0.2048 | Yes |
| 5 | Mã giảm giá có được hoàn không? | Voucher có được trả lại khi hủy đơn không? | high | 0.5428 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 2 mang kết quả cực kỳ bất ngờ (score 0.51 ở ngưỡng lửng lơ). Mặc dù mặt ngữ nghĩa logic con người "24 giờ = một ngày", mô hình Embedding (vốn huấn luyện trên xác xuất text context kề nhau) thường hiểu 2 cụm chữ viết khác hẳn nhau này không "chung" hướng mạnh. Nó nói lên việc LLM bắt semantics mạnh về từ loại nhưng rất yếu vè mặt suy diễn phép toán học hay quy đổi đơn vị thời gian chéo.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Tôi có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền? | 15 ngày kể từ lúc đơn hàng được cập nhật trạng thái Giao hàng thành công. Riêng thực phẩm tươi sống/đông lạnh: 24 giờ. |
| 2 | Tiền hoàn về ví ShopeePay mất bao lâu? | 24 giờ (với điều kiện Ví ShopeePay vẫn hoạt động bình thường và còn liên kết với tài khoản Shopee). |
| 3 | Đồng kiểm là gì và tôi được làm gì khi đồng kiểm? | Đồng kiểm là kiểm tra ngoại quan và số lượng sản phẩm khi nhận hàng. Được: kiểm tra bên ngoài, số lượng. Không được: mở tem chống hàng giả, dùng thử sản phẩm, làm hư hại sản phẩm. |
| 4 | Nếu trả hàng theo hình thức tự sắp xếp, tôi có được hoàn phí vận chuyển không? | Có. Bạn thanh toán trước phí trả hàng, Shopee hoàn lại trong 3–5 ngày làm việc: đơn Shopee Mall hoàn tiền mặt; đơn ngoài Mall hoàn Shopee Xu. |
| 5 | Mã giảm giá có được hoàn lại khi tôi trả hàng toàn bộ đơn không? | Tùy theo quy định hoàn mã giảm giá của Shopee. Voucher có thể được/không được hoàn tùy điều kiện cụ thể. |

### Kết Quả Của Tôi

**Chunker:** `AgenticChunker` | **Embedder:** `text-embedding-3-small` | **LLM:** `gpt-4o-mini`

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền? | Chunk policy về "Trả hàng/Hoàn tiền trong trường hợp Chưa nhận.../ 15 ngày..." | 0.6086 | Yes | Bạn có 15 ngày kể từ lúc cập nhật giao hàng thành công, riêng đồ tươi sống/đông lạnh là 24 giờ. |
| 2 | Tiền hoàn về ví ShopeePay mất bao lâu? | Thời gian hoàn tiền đối với đơn hàng... ShopeePay nhận hoàn trong 24h. | 0.6529 | Yes | Tiền hoàn về ví ShopeePay sẽ được gửi trong 24 giờ, cần đảm bảo ví ở trạng thái bình thường. |
| 3 | Đồng kiểm là gì và tôi được làm gì khi đồng kiểm? | Đồng kiểm là thông tin... kiểm tra ngoại quan số lượng, không mở tem. | 0.5852 | Yes | Đồng kiểm là kiểm tra ngoại quan và số lượng. Không mở tem hay sử dụng thử sản phẩm. |
| 4 | Nếu trả hàng theo hình thức tự sắp xếp, tôi có được hoàn phí vận chuyển không? | Trả hàng qua hình thức tự sắp xếp, bạn thanh toán phí trả hàng chờ hoàn lại... | 0.7572 | Yes | Có, phí trả hàng sẽ được hoàn lại theo Chính sách hỗ trợ phí trả hàng. |
| 5 | Mã giảm giá có được hoàn lại khi tôi trả hàng toàn bộ đơn không? | Mã giảm giá có thể hoàn lại hoặc không tùy quy định khi từ chối nhận... | 0.7433 | Yes | Có, mã giảm giá sẽ được hoàn lại trong vòng 48 giờ kể từ khi yêu cầu được chấp nhận. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

**(Insight & Trade-off):**
Tuy Agentic Chunker mang lại chất lượng Embedding cực tốt (cắt ra đúng **54 chunks** sắc nét thay vì 209 chunks nếu dùng regex cơ học), việc ứng dụng chúng vào các văn bản cực lớn sẽ rất **tốn kém và chậm chạp**, do GPT-4o-mini phải duyệt qua mọi văn bản. Hơn nữa, chất lượng trả lời của bước Agent LLM đôi khi bị thiên lệch nếu Retriever kéo về 2 chunks có quy định hơi chồng chéo nhau (như Q5 - LLM trả lời chắc chắn "Có" thay vì "Tùy điều kiện" như Gold text, tạo ra ảo giác nhẹ - Hallucination). Đây là minh chứng rõ nét cho sự đánh đổi giữa thời gian/chi phí index vs chất lượng RAG.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Qua cách phân chẻ cấu trúc rất tỉ mỉ của Quang Quí (Cắt theo bộ markdown Header) và Nam Sơn (Schema Parent-Child kéo giữ gốc cho nhánh phụ), tôi nhận ra việc ứng dụng RAG trong Doanh Nghiệp phụ thuộc sống còn vào "Format" tài liệu bạn nhận được. Nếu nó rất sạch sẽ, xài script Regex của các bạn là một giải pháp cực rẻ và ngon.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Có một nhóm demo kết hợp Filter dứt điểm ngay từ cấp Metadata Filter giống như `search_with_filter`, khiến thời gian quét DB siêu nhanh và chẳng bao giờ bị lạc quẻ giữa các doc trùng lắp domain. Nó thay đổi mindset của tôi về việc không chỉ "băm" mà phải "dán nhãn".

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ hạn chế sử dụng Agentic Chunking (gọi LLM bóc tách file thô) cho những pipeline Data dày ngàn file vì nó quá đắt đỏ, tốn Token và sập rate limit liên tục. Thay vì thế, dựa bào bài học "Similarity predictions", tôi sẽ kết hợp DocumentStructureChunker rồi chạy fine-tune trên một con Embedded model nội bộ để nó thông minh hơn với phép toán thời gian ("24h" hiểu là "1 ngày").

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 4 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 28 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **87 / 100** |
