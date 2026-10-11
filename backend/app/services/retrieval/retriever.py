import json
import re
from pathlib import Path

from app.models.chunk import Chunk

from .embedding_service import EmbeddingService
from .faiss_store import VectorStore


class Retriever:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = None
        self.chunks = []

    # =========================================================
    # INDEX
    # =========================================================

    def index(self, chunks):

        if not chunks:
            raise ValueError(
                "Cannot index an empty chunk list."
            )

        self.chunks = list(chunks)

        embeddings = (
            self.embedding_service.embed_chunks(
                self.chunks
            )
        )

        dimension = embeddings.shape[1]

        self.vector_store = VectorStore(
            dimension=dimension
        )

        self.vector_store.add(
            embeddings
        )

    # =========================================================
    # RETRIEVE
    # =========================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        document_id: str | None = None,
        source_id: str | None = None,
        mode: str = "general",
    ):
        """
        Retrieve the most relevant chunks.

        document_id:
            None -> no document restriction
            value -> search only within that document

        source_id:
            None -> no website/source restriction
            value -> search all pages belonging to that source
        """

        if self.vector_store is None:
            raise RuntimeError(
                "Vector store has not been indexed."
            )

        if not self.chunks:
            return []

        query = query.strip()

        if not query:
            return []

        print(
            "\nRetriever:",
            "document_id =",
            document_id,
            "| source_id =",
            source_id,
        )

        # =====================================================
        # 1. TOKENIZE QUERY
        # =====================================================

        query_tokens = self._tokenize(query)

        # =====================================================
        # 2. QUERY EMBEDDING
        # =====================================================

        query_embedding = (
            self.embedding_service.embed_query(
                query
            )
        )

        # =====================================================
        # 3. SEARCH VECTOR STORE
        #
        # Search all vectors first so that we can combine
        # semantic similarity with lexical signals.
        # =====================================================

        semantic_scores, indices = (
            self.vector_store.search(
                query_embedding,
                len(self.chunks)
            )
        )

        # =====================================================
        # 4. BUILD CANDIDATES
        # =====================================================

        candidates = []

        for semantic_score, index in zip(
            semantic_scores,
            indices
        ):

            if index == -1:
                continue

            if index >= len(self.chunks):
                continue

            chunk = self.chunks[index]

            chunk_document_id = str(
                chunk.document_id
            )

            # =================================================
            # DOCUMENT SCOPE
            #
            # =================================================

            if document_id is not None:
                if (
                    chunk_document_id
                    != str(document_id)
                ):
                    continue

            # =================================================
            # SOURCE SCOPE
            #
            # source_id groups multiple pages belonging
            # to the same website/source.
            # =================================================

            if source_id is not None:
                chunk_source_id = str(
                    (chunk.metadata or {}).get(
                        "source_id",
                        ""
                    )
                )

                if chunk_source_id != str(source_id):
                    continue

            # =================================================
            # SCORES
            # =================================================

            semantic_score = float(
                semantic_score
            )

            lexical_score = (
                self._lexical_score(
                    query_tokens,
                    chunk
                )
            )

            heading_score = (
                self._heading_score(
                    query_tokens,
                    chunk
                )
            )

            document_score = (
                self._document_match(
                    query_tokens,
                    chunk
                )
            )

            phrase_score = (
                self._phrase_score(
                    query,
                    chunk
                )
            )

            # =================================================
            # FINAL SCORE
            #
            # Semantic similarity remains the strongest
            # signal, while exact lexical matches provide
            # additional precision.
            # =================================================

            final_score = (
    0.40 * semantic_score
    + 0.30 * lexical_score
    + 0.20 * heading_score
    + 0.05 * document_score
    + 0.05 * phrase_score
)

            # Explicit document scope gets a small boost.
            #
            # This does NOT determine relevance; it only
            # reinforces that the result belongs to the
            # requested document.

            if document_id is not None:
                final_score += 0.10

            candidates.append(
                {
                    "chunk": chunk,
                    "score": float(final_score),
                    "semantic_score": semantic_score,
                    "lexical_score": lexical_score,
                    "heading_score": heading_score,
                    "document_score": document_score,
                    "phrase_score": phrase_score,
                }
            )

        # =====================================================
        # 5. SORT
        # =====================================================

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # =====================================================
        # 6. REMOVE WEAK RESULTS
        # =====================================================

        if candidates:

            best_score = candidates[0]["score"]

            dynamic_minimum = max(
                min_score,
                best_score * 0.45
            )

            candidates = [
                result
                for result in candidates
                if result["score"]
                >= dynamic_minimum
            ]

        # =====================================================
        # 7. DEDUPLICATE
        # =====================================================

        results = []

        seen = set()

        for result in candidates:

            chunk = result["chunk"]

            key = (
                str(chunk.document_id),
                str(chunk.id),
                str(chunk.text).strip(),
            )

            if key in seen:
                continue

            seen.add(key)

            results.append(result)

            if len(results) >= top_k:
                break

        # =====================================================
        # 8. DEBUG
        # =====================================================

        print(
            "\nFinal retrieval results:"
        )

        for result in results:

            chunk = result["chunk"]

            metadata = (
                chunk.metadata
                or {}
            )

            print(
                round(
                    result["score"],
                    4
                ),
                "| semantic:",
                round(
                    result["semantic_score"],
                    4
                ),
                "| lexical:",
                round(
                    result["lexical_score"],
                    4
                ),
                "| heading:",
                round(
                    result["heading_score"],
                    4
                ),
                "| document:",
                round(
                    result["document_score"],
                    4
                ),
                "| phrase:",
                round(
                    result["phrase_score"],
                    4
                ),
                "|",
                metadata.get(
                    "document_title",
                    "Unknown document"
                ),
                "|",
                chunk.heading,
            )

        return results

    # =========================================================
    # TOKENIZATION
    # =========================================================

    @staticmethod
    def _tokenize(
        text: str
    ) -> set[str]:

        words = re.findall(
            r"[a-zA-Z0-9]+",
            text.lower()
        )

        stop_words = {
            "the",
            "is",
            "are",
            "a",
            "an",
            "and",
            "or",
            "of",
            "to",
            "in",
            "on",
            "for",
            "what",
            "which",
            "who",
            "how",
            "where",
            "when",
            "why",
            "my",
            "your",
            "their",
            "this",
            "that",
            "these",
            "those",
            "do",
            "does",
            "did",
            "tell",
            "me",
            "about",
            "give",
            "only",
            "mentioned",
            "listed",
            "according",
        }

        return {
            word
            for word in words
            if word not in stop_words
        }

    # =========================================================
    # DOCUMENT MATCH
    # =========================================================

    def _document_match(
        self,
        query_tokens: set[str],
        chunk: Chunk
    ) -> float:

        if not query_tokens:
            return 0.0

        metadata = (
            chunk.metadata
            or {}
        )

        title = str(
            metadata.get(
                "document_title",
                ""
            )
        )

        source = str(
            metadata.get(
                "source",
                ""
            )
        )

        document_text = (
            f"{title} {source}"
        )

        document_tokens = (
            self._tokenize(
                document_text
            )
        )

        if not document_tokens:
            return 0.0

        matches = (
            query_tokens
            &
            document_tokens
        )

        return (
            len(matches)
            /
            len(query_tokens)
        )

    # =========================================================
    # CHUNK TEXT MATCH
    # =========================================================

    def _lexical_score(
        self,
        query_tokens: set[str],
        chunk: Chunk
    ) -> float:

        if not query_tokens:
            return 0.0

        text_tokens = (
            self._tokenize(
                chunk.text
            )
        )

        if not text_tokens:
            return 0.0

        matches = (
            query_tokens
            &
            text_tokens
        )

        return (
            len(matches)
            /
            len(query_tokens)
        )

    # =========================================================
    # HEADING MATCH
    # =========================================================

    def _heading_score(
        self,
        query_tokens: set[str],
        chunk: Chunk
    ) -> float:

        if not query_tokens:
            return 0.0

        heading_tokens = (
            self._tokenize(
                chunk.heading
            )
        )

        if not heading_tokens:
            return 0.0

        matches = (
            query_tokens
            &
            heading_tokens
        )

        return (
            len(matches)
            /
            len(query_tokens)
        )

    # =========================================================
    # PHRASE MATCH
    # =========================================================

    def _phrase_score(
        self,
        query: str,
        chunk: Chunk
    ) -> float:

        query_text = (
            query
            .lower()
            .strip()
        )

        chunk_text = (
            f"{chunk.heading} "
            f"{chunk.text}"
        ).lower()

        if not query_text:
            return 0.0

        # Generic phrase matching.
        #
        # These are linguistic patterns rather than
        # document-specific concepts.

        phrases = [
            "total amount",
            "total cost",
            "total fee",
            "total score",
            "date of birth",
            "phone number",
            "email address",
            "application number",
            "registration number",
            "project name",
            "project names",
            "projects mentioned",
            "projects listed",
            "skills",
            "experience",
            "education",
            "qualifications",
            "requirements",
            "eligibility",
            "fees",
            "fee",
            "amount",
            "address",
            "contact",
        ]

        matches = 0

        for phrase in phrases:

            if (
                phrase in query_text
                and phrase in chunk_text
            ):
                matches += 1

        if matches == 0:
            return 0.0

        return min(
            1.0,
            matches / 2.0
        )

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        directory: str
    ):

        if self.vector_store is None:
            raise RuntimeError(
                "Cannot save an unindexed retriever."
            )

        directory = Path(
            directory
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        index_path = (
            directory
            /
            "faiss.index"
        )

        chunks_path = (
            directory
            /
            "chunks.json"
        )

        self.vector_store.save(
            str(index_path)
        )

        chunks_data = [
            chunk.model_dump()
            for chunk in self.chunks
        ]

        chunks_path.write_text(
            json.dumps(
                chunks_data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    # =========================================================
    # LOAD
    # =========================================================

    def load(
        self,
        directory: str
    ):

        directory = Path(
            directory
        )

        index_path = (
            directory
            /
            "faiss.index"
        )

        chunks_path = (
            directory
            /
            "chunks.json"
        )

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not chunks_path.exists():
            raise FileNotFoundError(
                f"Chunks file not found: {chunks_path}"
            )

        dimension = (
            self.embedding_service
            .model
            .get_sentence_embedding_dimension()
        )

        self.vector_store = VectorStore(
            dimension=dimension
        )

        self.vector_store.load(
            str(index_path)
        )

        chunks_data = json.loads(
            chunks_path.read_text(
                encoding="utf-8"
            )
        )

        self.chunks = [
            Chunk(**chunk)
            for chunk in chunks_data
        ]