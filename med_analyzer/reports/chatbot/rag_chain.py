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
You are a medical report assistant.

Rules:
- ONLY use the provided report data.
- DO NOT diagnose diseases.
- DO NOT give treatment or medication advice.

- Be clear, calm, and patient-friendly.
            """,
        ),
        (
            "human",
            """
Medical Report (structured):
{report_json}

Doctor-style Explanation:
{llm_explanation}

User Question:
{question}

Answer based ONLY on the report:
            """,
        ),
        ]
    )

    chain=prompt | llm | StrOutputParser()

    return chain
