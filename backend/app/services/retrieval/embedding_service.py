from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """
    Load the embedding model once per Python process.

    Because this function is cached, multiple
    EmbeddingService instances reuse the same model
    instead of loading another copy into memory.
    """

    print(
        f"Loading embedding model: {MODEL_NAME}"
    )

    return SentenceTransformer(
        MODEL_NAME
    )


class EmbeddingService:

    def __init__(
        self,
        model_name: str = MODEL_NAME,
    ):
        """
        Embedding service using Sentence Transformers.

        The model is cached globally for the process.
        """

        self.model_name = model_name

        # Use the cached loader for the default model.
        #
        # If a different model is explicitly supplied,
        # load that model directly.
        if model_name == MODEL_NAME:
            self.model = _load_model()

        else:
            print(
                f"Loading embedding model: {model_name}"
            )

            self.model = SentenceTransformer(
                model_name
            )

    # =====================================================
    # EMBED TEXT
    # =====================================================

    def embed_text(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Convert a single piece of text into an embedding.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot embed empty text."
            )

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.astype(
            np.float32
        )

    # =====================================================
    # EMBED QUERY
    # =====================================================

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray:
        """
        Embed a user query.

        Returns a normalized float32 vector.
        """

        if not query or not query.strip():
            raise ValueError(
                "Cannot embed an empty query."
            )

        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.astype(
            np.float32
        )

    # =====================================================
    # EMBED CHUNKS
    # =====================================================

    def embed_chunks(
        self,
        chunks,
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Embed multiple document chunks efficiently.

        Batch encoding is substantially better than calling
        embed_text() once for every chunk.
        """

        if not chunks:
            raise ValueError(
                "Cannot embed an empty chunk list."
            )

        texts = []

        for chunk in chunks:

            text = (
                getattr(
                    chunk,
                    "text",
                    ""
                )
                or ""
            ).strip()

            if not text:
                text = " "

            texts.append(text)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(
            embeddings,
            dtype=np.float32,
        )

    # =====================================================
    # EMBED MULTIPLE TEXTS
    # =====================================================

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Generic batch embedding method.

        Useful for future processors or retrieval features
        that need embeddings without constructing Chunk objects.
        """

        if not texts:
            raise ValueError(
                "Cannot embed an empty text list."
            )

        cleaned_texts = [
            text.strip()
            if text and text.strip()
            else " "
            for text in texts
        ]

        embeddings = self.model.encode(
            cleaned_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(
            embeddings,
            dtype=np.float32,
        )

    # =====================================================
    # MODEL INFORMATION
    # =====================================================

    @property
    def dimension(self) -> int:
        """
        Return the embedding vector dimension.
        """

        dimension = (
            self.model
            .get_sentence_embedding_dimension()
        )

        if dimension is None:
            raise RuntimeError(
                "Could not determine embedding dimension."
            )

        return int(dimension)