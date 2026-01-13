from .rag_chain import get_report_qa_chain

def answer_report_question(report_json, llm_explanation, question ):
    """
    Answers a user's question about a specific medical report.
    """

    chain=get_report_qa_chain()

    response=chain.invoke({
        "report_json":report_json,
        "llm_explanation":llm_explanation,
        "question":question,
    })

    return response