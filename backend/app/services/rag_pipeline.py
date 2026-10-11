from pathlib import Path

from app.core.config import GROQ_API_KEY

from app.services.retrieval.retriever import Retriever
from app.services.generator.query_rewriter import QueryRewriter
from app.services.generator.prompt_builder import PromptBuilder
from app.services.generator.response_generator import ResponseGenerator


class RAGPipeline:

    INDEX_DIR = Path("data/index")

    def __init__(self):

        self.retriever = Retriever()

        self._index_signature = None

        self._load_index()

        self.query_rewriter = QueryRewriter(
            GROQ_API_KEY
        )

        self.prompt_builder = PromptBuilder()

        self.generator = ResponseGenerator(
            GROQ_API_KEY
        )

    # =====================================================
    # INDEX MANAGEMENT
    # =====================================================

    def _get_index_signature(self):
        """
        Return a signature representing the current
        persisted knowledge base.

        If either the FAISS index or chunks.json changes,
        the RAG pipeline knows that it needs to reload.
        """

        index_path = self.INDEX_DIR / "faiss.index"
        chunks_path = self.INDEX_DIR / "chunks.json"

        if not index_path.exists() or not chunks_path.exists():
            return None

        try:
            return (
                index_path.stat().st_mtime_ns,
                index_path.stat().st_size,
                chunks_path.stat().st_mtime_ns,
                chunks_path.stat().st_size,
            )

        except OSError:
            return None

    def _load_index(self):
        """
        Load the persisted vector index and remember
        its current signature.
        """

        self.retriever.load(
            str(self.INDEX_DIR)
        )

        self._index_signature = (
            self._get_index_signature()
        )

        print(
            "RAG index loaded.",
            "signature =",
            self._index_signature
        )

    def _refresh_index_if_needed(self):
        """
        Reload the index only when the persisted files
        have changed since the last load.
        """

        current_signature = (
            self._get_index_signature()
        )

        if current_signature is None:
            return

        if current_signature != self._index_signature:

            print(
                "Knowledge base changed. "
                "Reloading RAG index..."
            )

            self._load_index()

    def reload_index(self):
        """
        Explicitly reload the persisted vector index.

        Useful after ingestion or when the application
        needs to force a refresh.
        """

        self._load_index()

    # =====================================================
    # SIMPLE CONVERSATIONAL RESPONSES
    # =====================================================

    @staticmethod
    def _direct_response(query: str):

        q = query.lower().strip()

        greetings = {
            "hi",
            "hello",
            "hey",
            "hi edupilot",
            "hello edupilot",
            "hey edupilot",
        }

        thanks = {
            "thanks",
            "thank you",
            "thanks edupilot",
            "thank you edupilot",
            "thx",
            "ty",
        }

        if q in greetings:
            return "Hello! How can I help you?"

        if q in thanks:
            return "You're welcome! How can I help?"

        return None

    # =====================================================
    # RESULT MERGING
    # =====================================================

    @staticmethod
    def _merge_results(result_sets):

        merged = {}

        for results in result_sets:

            for result in results:

                chunk = result["chunk"]

                key = (
                    str(chunk.document_id),
                    str(chunk.id),
                )

                if (
                    key not in merged
                    or result["score"] > merged[key]["score"]
                ):
                    merged[key] = result

        return sorted(
            merged.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

    # =====================================================
    # RESULT DEDUPLICATION
    # =====================================================

    @staticmethod
    def _deduplicate_results(results):

        unique = {}

        for result in results:

            chunk = result["chunk"]

            key = (
                str(chunk.document_id),
                str(chunk.heading),
            )

            if (
                key not in unique
                or result["score"] > unique[key]["score"]
            ):
                unique[key] = result

        return sorted(
            unique.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

    # =====================================================
    # UNKNOWN ANSWER DETECTION
    # =====================================================

    @staticmethod
    def _is_unknown_answer(answer: str) -> bool:

        answer_lower = (
            answer
            .lower()
            .strip()
        )

        unknown_phrases = [
            "i don't know based on the available information",
            "i don't know based on the provided context",
            "the information is not available",
            "not available in the provided context",
            "cannot be determined from the provided context",
            "i cannot determine this from the provided context",
        ]

        return any(
            phrase in answer_lower
            for phrase in unknown_phrases
        )

    # =====================================================
    # SOURCE BUILDING
    # =====================================================

    
    @staticmethod
    def _build_sources(results):

     sources = []
     seen = set()

     for result in results:

        chunk = result["chunk"]

        key = (
            str(chunk.document_id),
            str(chunk.heading),
        )

        if key in seen:
            continue

        seen.add(key)

        metadata = chunk.metadata or {}

        source_url = metadata.get(
            "source_url",
            metadata.get(
                "source",
                ""
            ),
        )

        sources.append(
            {
                "heading": chunk.heading,
                "url": source_url,
                "score": round(
                    result["score"],
                    4,
                ),
            }
        )

     return sources

    # =====================================================
    # ANSWER
    # =====================================================

    def answer(
     self,
     query: str,
     history=None,
     document_id: str | None = None,
     source_id: str | None = None,
     top_k: int = 5
        ):

        if history is None:
            history = []

        query = query.strip()

        print("\n================================")
        print("Document scope:", document_id)
        print("Original query:", query)

        # -------------------------------------------------
        # EMPTY QUERY
        # -------------------------------------------------

        if not query:

            return {
                "answer": "Please ask me a question.",
                "sources": [],
            }

        # -------------------------------------------------
        # SIMPLE CONVERSATIONAL RESPONSE
        # -------------------------------------------------

        direct = self._direct_response(query)

        if direct:

            return {
                "answer": direct,
                "sources": [],
            }

        # -------------------------------------------------
        # IMPORTANT:
        # Refresh the in-memory index if ingestion has
        # changed the persisted knowledge base.
        # -------------------------------------------------

        try:

            self._refresh_index_if_needed()

        except Exception as exc:

            print(
                "Index refresh failed:",
                exc,
            )

            return {
                "answer": (
                    "I don't know based on "
                    "the available information."
                ),
                "sources": [],
            }

        # -------------------------------------------------
        # REWRITE QUERY USING CONVERSATION HISTORY
        # -------------------------------------------------

        try:

            search_query = self.query_rewriter.rewrite(
                query,
                history,
            )

        except Exception as exc:

            print(
                "Query rewriting failed:",
                exc,
            )

            search_query = query

        if not search_query:
            search_query = query

        print("Search query:", search_query)

        # -------------------------------------------------
        # RETRIEVE
        # -------------------------------------------------

        retrieval_k = max(
            top_k * 3,
            15,
        )

        try:

            results = self.retriever.retrieve(
                search_query,
                top_k=retrieval_k,
                document_id=document_id,
                source_id=source_id
            )

        except Exception as exc:

            print(
                "Retrieval failed:",
                exc,
            )

            return {
                "answer": (
                    "I don't know based on "
                    "the available information."
                ),
                "sources": [],
            }

        # -------------------------------------------------
        # DEDUPLICATE
        # -------------------------------------------------

        results = self._deduplicate_results(
            results
        )

        # -------------------------------------------------
        # KEEP STRONGEST EVIDENCE
        # -------------------------------------------------

        results = results[
            :max(top_k, 8)
        ]

        print("\nFinal evidence:")

        for result in results:

            chunk = result["chunk"]

            metadata = (
                chunk.metadata
                if chunk.metadata
                else {}
            )

            print(
                round(
                    result["score"],
                    4,
                ),
                "|",
                metadata.get(
                    "document_title",
                    "Unknown document",
                ),
                "|",
                chunk.heading,
            )

        # -------------------------------------------------
        # NOTHING RETRIEVED
        # -------------------------------------------------

        if not results:

            print("No relevant evidence found.")
            print("================================\n")

            return {
                "answer": (
                    "I don't know based on "
                    "the available information."
                ),
                "sources": [],
            }

        # -------------------------------------------------
        # BUILD GROUNDED CONTEXT
        # -------------------------------------------------

        chunks = [
            result["chunk"]
            for result in results
        ]

        prompt = self.prompt_builder.build(
            query,
            chunks,
        )

        # -------------------------------------------------
        # GENERATE ANSWER
        # -------------------------------------------------

        try:

            answer = self.generator.generate(
                prompt
            )

        except Exception as exc:

            print(
                "Answer generation failed:",
                exc,
            )

            return {
                "answer": (
                    "I couldn't generate an answer "
                    "from the available information."
                ),
                "sources": [],
            }

        # -------------------------------------------------
        # UNKNOWN ANSWER
        # -------------------------------------------------

        if self._is_unknown_answer(answer):

            print("Answer marked as unknown.")
            print("================================\n")

            return {
                "answer": answer,
                "sources": [],
            }

        # -------------------------------------------------
        # SOURCES
        # -------------------------------------------------

        sources = self._build_sources(
            results
        )

        print("================================\n")

        return {
            "answer": answer,
            "sources": sources,
        }