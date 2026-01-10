import pytesseract
from PIL import Image
import cv2
from pathlib import Path
import numpy as np
import re, json
from collections import defaultdict
from difflib import SequenceMatcher
import os

# Define paths
DATA_ROOT = Path("C:/medical_data")
output_dir = "outputs"

# Function to preprocess the image (grayscale + thresholding)
def preprocess_image(image_path):
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.fastNlMeansDenoising(thresh)
    return denoised

# Normalize test name for comparison (removes special characters, makes it lowercase)
def normalize_test_name(name):
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name)     # Normalize whitespace
    return name.strip()

# Extract candidate rows that contain numerical values (test data)
def extract_candidate_rows(ocr_text):
    rows = []
    for line in ocr_text.split("\n"):
        line = line.strip()
        if len(line) < 5:
            continue
        if re.search(r"\d", line):  # must contain a number
            rows.append(line)
    return rows

# Improved regex to handle test names, values, units, and reference ranges
ROW_REGEX = re.compile(
    r"""
    (?P<name>[A-Za-z][A-Za-z\s\.\(\)/\-]+?)   # Test name
    \s+
    (?P<value>\d+(\.\d+)?)                   # Value
    \s*
    (?P<unit>[a-zA-Z/%µ]+)?                  # Unit
    \s*
    (?P<range>(\d+(\.\d+)?\s*[-–]\s*\d+(\.\d+)?))?  # Reference range (optional)
    """,
    re.VERBOSE
)

# Parse the candidate rows and extract test name, value, unit, and reference range
def parse_candidate_rows(rows):
    parsed = []
    for line in rows:
        m = ROW_REGEX.search(line)
        if not m:
            continue
        parsed.append({
            "raw_name": m.group("name").strip(),
            "value": float(m.group("value")) if m.group("value") else None,
            "unit": m.group("unit"),
            "reference_range": m.group("range"),
            "raw_line": line
        })
    return parsed

# Build a test ontology from existing annotation files (for fuzzy matching)
def build_test_ontology(annotation_files):
    ontology = defaultdict(set)
    for file in annotation_files:
        with open(file) as f:
            data = json.load(f)

        # SAFETY CHECK
        if "test_results" not in data:
            continue

        for test in data["test_results"]:
            if "test_name" not in test:
                continue

            norm = normalize_test_name(test["test_name"])
            ontology[norm].add(test["test_name"])

    return ontology

# Similarity function to match test names using fuzzy matching (based on SequenceMatcher)
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Normalize the extracted rows by matching with the test ontology
def normalize_extracted_rows(parsed_rows, ontology, threshold=0.75):
    normalized = []
    for row in parsed_rows:
        raw_norm = normalize_test_name(row["raw_name"])
        best_match = None
        best_score = 0

        for standard in ontology.keys():
            score = similarity(raw_norm, standard)
            if score > best_score:
                best_score = score
                best_match = standard

        normalized.append({
            "test_name": best_match if best_score >= threshold else row["raw_name"],
            "value": row["value"],
            "unit": row["unit"],
            "reference_range": row["reference_range"],
            "confidence": round(best_score, 2),
            "raw_line": row["raw_line"]
        })

    return normalized

# Compare extracted data with ground truth JSON using fuzzy matching
def calculate_accuracy(extracted_data, ground_truth_json):
    # SAFETY CHECK: If 'test_results' is missing or empty in ground_truth_json
    if 'test_results' not in ground_truth_json or not ground_truth_json['test_results']:
        print("No valid 'test_results' found in the ground truth JSON, skipping accuracy calculation.")
        return 0, 0  # Return 0 accuracy if there's no data
    
    gt_tests = {}
    for test in ground_truth_json['test_results']:
        if 'test_name' not in test:
            print("Missing 'test_name' in ground truth data, skipping this entry.")
            continue
        if 'value' not in test:  # Check if 'value' is missing
            print(f"Missing 'value' in ground truth data for test: {test.get('test_name')}, skipping this entry.")
            continue
        gt_tests[normalize_test_name(test['test_name'])] = test
    
    total = len(gt_tests)  # Get the total count of valid test names in ground truth
    
    # If no valid test names were found in the ground truth, return early
    if total == 0:
        print("No valid 'test_name' entries found in the ground truth data, skipping accuracy calculation.")
        return 0, 0
    
    correct_names = 0
    correct_values = 0

    matched_tests = []
    unmatched_tests = []

    for extracted in extracted_data:
        test_name = normalize_test_name(extracted['test_name'])

        # Exact match
        if test_name in gt_tests:
            correct_names += 1
            matched_tests.append(extracted['test_name'])
            
            # Only compare 'value' if it's present in both extracted and ground truth
            gt_value = gt_tests[test_name].get('value')
            if gt_value is not None and abs(extracted['value'] - gt_value) < 0.01:
                correct_values += 1
        else:
            # Try partial match
            found = False
            for gt_name in gt_tests.keys():
                if test_name in gt_name or gt_name in test_name:
                    correct_names += 1
                    matched_tests.append(f"{extracted['test_name']} -> {gt_tests[gt_name]['test_name']}")
                    
                    # Only compare 'value' if it's present in both extracted and ground truth
                    gt_value = gt_tests[gt_name].get('value')
                    if gt_value is not None and abs(extracted['value'] - gt_value) < 0.01:
                        correct_values += 1
                    found = True
                    break

            if not found:
                unmatched_tests.append(extracted['test_name'])

    print(f"\nTest Name Accuracy: {correct_names}/{total} = {correct_names/total*100:.1f}%")
    print(f"Value Accuracy: {correct_values}/{total} = {correct_values/total*100:.1f}%")
    print(f"\nMatched tests: {matched_tests}")
    print(f"Unmatched tests: {unmatched_tests}")

    return correct_names / total, correct_values / total

# Export the extracted data to a structured JSON report
def export_report_json(report_id, extracted_data, output_dir="outputs"):
    output = {
        "report_id": report_id,
        "tests": extracted_data
    }

    Path(output_dir).mkdir(exist_ok=True)
    out_path = Path(output_dir) / f"{report_id}_extracted.json"

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved structured report to {out_path}")

# Main function to process reports in a directory
def process_reports_in_directory(data_root):
    image_files = [f for f in os.listdir(data_root) if f.endswith('.png') or f.endswith('.jpg')]

    for image_file in image_files:
        print(f"Processing: {image_file}")
        image_path = data_root / image_file
        ground_truth_json_path = data_root / f"{image_file.replace('.png', '_annotations.json').replace('.jpg', '_annotations.json')}"

        # Skip if ground truth file doesn't exist
        if not ground_truth_json_path.exists():
            print(f"Ground truth file for {image_file} does not exist, skipping.")
            continue

        # Preprocess image and extract OCR text
        preprocessed = preprocess_image(image_path)
        cv2.imwrite(f"preprocessed_{image_file}", preprocessed)  # Save preprocessed image for review

        text = pytesseract.image_to_string(preprocessed)
        print("Raw OCR output:")
        print(text)
        print("\n" + "=" * 50 + "\n")

        # Extract candidate rows (e.g., test names and values)
        candidate_rows = extract_candidate_rows(text)
        parsed_rows = parse_candidate_rows(candidate_rows)

        # Build ontology from existing annotation files
        annotation_files = list(data_root.glob("*.json"))
        ontology = build_test_ontology(annotation_files)

        # Normalize the extracted rows using the ontology
        extracted_data = normalize_extracted_rows(parsed_rows, ontology)

        # Load ground truth annotations
        with open(ground_truth_json_path, 'r') as f:
            ground_truth_json = json.load(f)

        # Calculate accuracy of the extraction
        accuracy = calculate_accuracy(extracted_data, ground_truth_json)
        print("Accuracy:", accuracy)

        # Export the structured report as JSON
        export_report_json(report_id=image_file.replace('.png', '').replace('.jpg', ''), extracted_data=extracted_data)

# Run batch processing
if __name__ == "__main__":
    process_reports_in_directory(DATA_ROOT)
