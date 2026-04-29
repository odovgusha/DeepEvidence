from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 🔹 Initialize model
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)


prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a scientific assistant.

    STRICT RULES:
    - Use ALL relevant information from <retrieved_data>
    - Combine information from MULTIPLE sources when possible
    - Do NOT rely on a single source if others are available
    - If sources disagree, mention differences

    - Answer ONLY using retrieved_data
    - Do NOT use outside knowledge

    OUTPUT FORMAT:
    1. Give a clear, concise answer
    2. Provide a combined summary across sources
    3. List sources used

    Always cite like [SOURCE 1], [SOURCE 2]
    """
     ),
    ("user",
     """
<retrieved_data>
{rag_data}
</retrieved_data>

<conversation_history>
{history}
</conversation_history>

<user_input>
{user_input}
</user_input>
"""
    )
])

chain = prompt | llm



def build_rag_context(results, k=5):
    chunks = []

    for i, r in enumerate(results[:k]):
        if isinstance(r, dict):
            text = r.get("content", "")
            source_name = r.get("filename", "Unknown")
        elif hasattr(r, "page_content"):
            text = r.page_content
            source_name = getattr(r, "metadata", {}).get("source", "Unknown")
        else:
            text = str(r)
            source_name = "Unknown"

        text = text.replace("\n", " ").strip()

        chunks.append(
            f"[SOURCE {i+1} | {source_name}]\n{text}\n"
        )

    return "\n\n".join(chunks)


def generate_answer(user_input, results, history):
    rag_data = build_rag_context(results, k=5)

    print("\n QUESTION:", user_input)
    print(" RESULTS:", len(results))
    print("\n FULL RETRIEVED CONTEXT:\n")
    print(rag_data)

    response = chain.invoke({
        "rag_data": rag_data,
        "history": history,
        "user_input": user_input
    })

    return response.content