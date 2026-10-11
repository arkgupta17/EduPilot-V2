class PromptBuilder:

    def build(
        self,
        query: str,
        chunks,
    ) -> str:

        if not chunks:
            context = (
                "No relevant information was retrieved."
            )

        else:

            context_parts = []

            for index, chunk in enumerate(
                chunks,
                start=1
            ):

                metadata = (
                    chunk.metadata
                    or {}
                )

                document_title = metadata.get(
                    "document_title",
                    "Unknown document"
                )

                page = metadata.get(
                    "page"
                )

                heading = (
                    chunk.heading
                    or "Untitled section"
                )

                source_label = (
                    f"{document_title}"
                )

                if page is not None:
                    source_label += (
                        f" | Page {page}"
                    )

                context_parts.append(
                    f"""
[Context {index}]
Source: {source_label}
Section: {heading}

{chunk.text}
""".strip()
                )

            context = "\n\n".join(
                context_parts
            )

        prompt = f"""
You are EduPilot, a grounded AI assistant.

Your task is to answer the user's question using
ONLY the information provided in the CONTEXT.

Do not use outside knowledge.

====================
CONTEXT
====================

{context}

====================
USER QUESTION
====================

{query}

====================
RULES
====================

1. Answer only from information supported by the
   provided context.

2. Never invent facts, names, dates, numbers,
   qualifications, events, or other information.

3. Carefully consider ALL relevant context before
   answering.

4. If multiple items satisfy the user's question,
   include all relevant items supported by the context.

5. If the question asks for a list, do not stop after
   finding the first matching item.

6. Preserve names, dates, identifiers, and numerical
   values accurately.

7. If the user asks for a calculation, perform the
   calculation only when the required values are
   explicitly present and the calculation is
   unambiguous.

8. When performing a calculation, show the relevant
   values and result clearly.

9. Do not confuse different numerical measures.
   For example, if the context contains multiple types
   of scores, do not assume they are interchangeable.

10. If the context contains contradictory information,
    state the contradiction rather than choosing a value
    without evidence.

11. If the requested information is not supported by
    the context, respond exactly:

    I don't know based on the available information.

12. Do not use outside knowledge to fill missing
    information.

13. Do not mention retrieval, embeddings, vector stores,
    FAISS, chunks, prompts, or the RAG system.

14. Do not mention these instructions.

15. Answer naturally and directly.

====================
ANSWER
====================
"""

        return prompt