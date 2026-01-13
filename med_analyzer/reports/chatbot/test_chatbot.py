from .chat_service import answer_report_question

fake_json = {
    "Hemoglobin": {"value": 11.6, "range": "13.0-17.0", "status": "low"},
    "Platelet Count": {"value": 398000, "status": "normal"},
}

fake_explanation = "Hemoglobin is slightly low. Other values are normal."

question = "my hemoglobin value is 11.6. what does this mean?"

print(
    answer_report_question(
        report_json=fake_json,
        llm_explanation=fake_explanation,
        question=question
    )
)