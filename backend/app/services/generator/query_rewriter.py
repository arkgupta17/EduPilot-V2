from groq import Groq


class QueryRewriter:

    def __init__(self, api_key: str):
        self.client = Groq(
            api_key=api_key
        )

    def rewrite(
        self,
        query: str,
        history: list[dict] | None = None,
    ) -> str:

        query = query.strip()

        if not query:
            return ""

        if not history:
            return query

        # -------------------------------------------------
        # Keep only recent conversation
        # -------------------------------------------------

        recent_history = history[-6:]

        conversation = []

        for message in recent_history:

            role = message.get(
                "role",
                ""
            )

            content = message.get(
                "content",
                ""
            )

            if not content:
                continue

            conversation.append(
                f"{role}: {content}"
            )

        if not conversation:
            return query

        history_text = "\n".join(
            conversation
        )

        # -------------------------------------------------
        # Generic conversational rewriting
        # -------------------------------------------------

        system_prompt = """
You rewrite user questions for information retrieval.

Your job is ONLY to resolve conversational references
using the previous conversation.

Examples of references that may need resolution:

- it
- this
- that
- they
- them
- the first one
- the second one
- the above
- the previous item
- that document
- the other one

Rules:

1. Preserve the user's original intent.
2. Do not answer the question.
3. Do not add information that is not present
   in the conversation.
4. Do not assume what a document is about.
5. Do not classify documents into special categories.
6. Do not invent names, facts, entities, or values.
7. If the query is already clear, return it unchanged.
8. Return ONLY the rewritten retrieval query.
9. Do not explain your reasoning.
"""

        user_prompt = f"""
CONVERSATION:

{history_text}

CURRENT USER QUESTION:

{query}

Rewrite the current question so that it can be
understood independently of the conversation.
"""

        try:

            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
                max_tokens=200,
            )

            rewritten = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

            return rewritten or query

        except Exception as exc:

            print(
                "Query rewriting failed:",
                exc
            )

            # Retrieval should still work if the
            # rewriting service is unavailable.
            return query