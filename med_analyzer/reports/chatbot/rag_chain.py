import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

def get_report_qa_chain():
    """
    Creates a LangChain chain that answers questions
    strictly based on a medical report.
    """

    llm=ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.2,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt=ChatPromptTemplate.from_messages(
        [
            (
            "system",
            """
You are a medical report discussion assistant.

You answer user questions based on:
1) The structured medical report
2) The prior medical interpretation

Your role is to CLARIFY and EXPLAIN, not to reinterpret or diagnose.

Rules:
- Do NOT diagnose diseases
- Do NOT give treatment or medication advice
- Use patient-friendly, calm language
- Use cautious phrasing when discussing implications
- If the question goes beyond the report, say so clearly

            """,
        ),
        (
            "human",
            """
Medical Report (structured):
{report_json}

Doctor-style Explanation:
{llm_explanation}

Previous Conversation:
{chat_history}

User Question:
{question}

Answer the user clearly using the interpretation above:
            """,
        ),
        ]
    )

    chain=prompt | llm | StrOutputParser()

    return chain

def format_chat_history(messages):
    """
    Convert DB chat messages into a readable conversation transcript
    """
    history = []
    for msg in messages:
        if msg.role == "user":
            history.append(f"Patient asks: {msg.content}")
        else:
            history.append(f"Assistant explains: {msg.content}")
    return "\n".join(history)