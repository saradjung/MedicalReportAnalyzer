from .ocr import get_best_ocr_text
from .parsing import extract_candidate_rows, parse_candidate_rows
from .normalization import normalize_extracted_rows
from .interpretation import (
    enrich_tests_with_interpretation, 
    classify_abnormality, 
    generate_reason,
    assign_risk_level
)
from .reporting import build_final_report
from .cache import ONTOLOGY  # Import the pre-built ontology
from .llm_reasoner import llm_reasoner

def run_pipeline(file_path):
    # OCR + preprocessing
    text = get_best_ocr_text(file_path)

    # Candidate rows + parsing
    candidate_rows = extract_candidate_rows(text)
    parsed_rows = parse_candidate_rows(candidate_rows)

    # Use the CACHED ontology instead of rebuilding
    extracted_data = normalize_extracted_rows(parsed_rows, ONTOLOGY)

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