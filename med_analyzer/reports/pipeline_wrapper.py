from pathlib import Path
from .pipeline import (
    preprocess_image, get_best_ocr_text,
    extract_candidate_rows, parse_candidate_rows,
    build_test_ontology, normalize_extracted_rows,
    classify_abnormality, generate_reason, assign_risk_level,
    build_final_report, llm_reasoner
)
import json

DATA_ROOT = Path("C:/medical_data")  # or dynamic

def process_report(file_path):
    text = get_best_ocr_text(file_path)

    rows = extract_candidate_rows(text)
    parsed = parse_candidate_rows(rows)

    annotation_files = list(DATA_ROOT.glob("*.json"))
    ontology = build_test_ontology(annotation_files)

    extracted = normalize_extracted_rows(parsed, ontology)

    for test in extracted:
        test["status"] = classify_abnormality(test["value"], test["reference_range"])
        test["reason"] = generate_reason(test)
        test["risk_level"] = assign_risk_level(test["status"])

    final_report = build_final_report("user_upload", extracted)

    # If quota exceeded, this raises RuntimeError("AI_QUOTA_EXCEEDED")
    explanation = llm_reasoner(final_report)

    return final_report, explanation
