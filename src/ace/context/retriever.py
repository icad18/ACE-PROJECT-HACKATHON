"""
Hybrid Search Retriever combining BM25 keyword matching and vector cosine similarity.
"""

import math
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ace.context.embeddings import VectorEmbedder, cosine_similarity


@dataclass
class CodeChunk:
    file_path: str
    content: str
    symbol_name: Optional[str] = None
    start_line: int = 1
    end_line: int = 1
    embedding: Optional[List[float]] = None


class HybridRetriever:
    """Indexes code chunks and performs hybrid BM25 + Dense Vector search."""

    def __init__(self, embedder: Optional[VectorEmbedder] = None):
        self.embedder = embedder or VectorEmbedder()
        self.chunks: List[CodeChunk] = []

    def add_chunk(self, file_path: str, content: str, symbol_name: Optional[str] = None, start_line: int = 1, end_line: int = 1) -> None:
        """Add and embed a code snippet into the index."""
        emb = self.embedder.embed_text(content)
        self.chunks.append(CodeChunk(
            file_path=file_path,
            content=content,
            symbol_name=symbol_name,
            start_line=start_line,
            end_line=end_line,
            embedding=emb
        ))

    def _bm25_score(self, query_terms: List[str], text: str) -> float:
        """Compute term frequency matching score."""
        tokens = re.findall(r'\w+', text.lower())
        if not tokens:
            return 0.0
        score = 0.0
        for term in query_terms:
            tf = tokens.count(term.lower())
            if tf > 0:
                score += (tf / (tf + 1.5))
        return score

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform reciprocal rank fusion (RRF) search over indexed chunks."""
        if not self.chunks:
            return []

        query_terms = re.findall(r'\w+', query.lower())
        query_vec = self.embedder.embed_text(query)

        # 1. Rank by BM25
        bm25_scores = [
            (idx, self._bm25_score(query_terms, chunk.content + " " + (chunk.symbol_name or "")))
            for idx, chunk in enumerate(self.chunks)
        ]
        bm25_ranked = sorted(bm25_scores, key=lambda x: x[1], reverse=True)

        # 2. Rank by Vector Similarity
        vec_scores = [
            (idx, cosine_similarity(query_vec, chunk.embedding or []))
            for idx, chunk in enumerate(self.chunks)
        ]
        vec_ranked = sorted(vec_scores, key=lambda x: x[1], reverse=True)

        # 3. Reciprocal Rank Fusion (k=60)
        rrf_scores: Dict[int, float] = {}
        for rank, (idx, _) in enumerate(bm25_ranked, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (60 + rank))
        for rank, (idx, _) in enumerate(vec_ranked, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (60 + rank))

        top_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:top_k]

        results = []
        for i in top_indices:
            chunk = self.chunks[i]
            results.append({
                "file_path": chunk.file_path,
                "symbol_name": chunk.symbol_name,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content,
                "score": rrf_scores[i]
            })

        return results
