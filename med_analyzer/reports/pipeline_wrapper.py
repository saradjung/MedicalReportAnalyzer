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
    # 1OCR + preprocessing
    text = get_best_ocr_text(file_path)

    # Candidate rows + parsing
    candidate_rows = extract_candidate_rows(text)
    parsed_rows = parse_candidate_rows(candidate_rows)

    # Load ontology (existing annotation files)
    annotation_files = list(DATA_ROOT.glob("*.json"))
    ontology = build_test_ontology(annotation_files)

    # Normalize rows
    extracted_data = normalize_extracted_rows(parsed_rows, ontology)

    # Assign status, reasons, risk
    for test in extracted_data:
        test["status"] = classify_abnormality(test["value"], test["reference_range"])
        test["reason"] = generate_reason(test)
        test["risk_level"] = assign_risk_level(test["status"])

    # Build final report JSON
    final_report = build_final_report("user_upload", extracted_data)

    # Generate patient-friendly explanation via LLM
    llm_explanation = llm_reasoner(final_report)

    return final_report, llm_explanation
