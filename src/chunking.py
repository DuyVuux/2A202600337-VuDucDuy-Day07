from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = []
        current_chunk = []

        for sentence in sentences:
            current_chunk.append(sentence)

            if len(current_chunk) >= self.max_sentences_per_chunk:
                chunks.append(" ".join(current_chunk).strip())
                current_chunk = []

        # phần còn lại
        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())

        return chunks

class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # TODO: implement recursive splitting strategy
        if not text:
            return []

        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # TODO: recursive helper used by RecursiveChunker.chunk
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        # nếu hết separator → hard split
        if not remaining_separators:
            return [
                current_text[i: i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]

        # split theo separator hiện tại
        if sep:
            parts = current_text.split(sep)
        else:
            # separator cuối: split từng ký tự
            parts = list(current_text)

        chunks = []
        buffer = ""

        for part in parts:
            piece = part if sep == "" else part + sep

            if len(buffer) + len(piece) <= self.chunk_size:
                buffer += piece
            else:
                if buffer:
                    chunks.extend(self._split(buffer.strip(), remaining_separators[1:]))
                buffer = piece

        if buffer:
            chunks.extend(self._split(buffer.strip(), remaining_separators[1:]))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    dot_product = _dot(vec_a, vec_b)

    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size).chunk(text)
        sentence = SentenceChunker().chunk(text)
        recursive = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def stats(chunks):
            if not chunks:
                return {
                    "count": 0,
                    "avg_length": 0,
                    "chunks": []
                }

            return {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks),
                "chunks": chunks 
            }

        return {
            "fixed_size": stats(fixed),
            "by_sentences": stats(sentence),
            "recursive": stats(recursive),
        }