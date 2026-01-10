import pytesseract
from PIL import Image
import cv2
from pathlib import Path
import numpy as np
import re, json

DATA_ROOT=Path("C:/medical_data")
image_path= DATA_ROOT/ "coagulation_002.png"

image=Image.open(image_path)
#image.show()

text= pytesseract.image_to_string(image)
print("raw OCR output:")
print(text)
print("\n" + "="*50 + "\n")

def preprocess_image(image_path):
    img=cv2.imread(image_path)

    gray=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to get black text on white background
    _, thresh=cv2.threshold(gray, 0,255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    denoised=cv2.fastNlMeansDenoising(thresh)

    return denoised

preprocessed=preprocess_image(image_path)
cv2.imwrite("preprocessed.png",preprocessed)
text=pytesseract.image_to_string(preprocessed)

print(text)


def normalize_test_name(name):
    """
    Normalize test names for comparison by removing special characters,
    converting to lowercase, and removing common words
    """
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name)     # Normalize whitespace
    return name.strip()

# print("extracted_data:",extracted_data)
# print(json.dumps(extracted_data,indent=2))
def extract_candidate_rows(ocr_text):
    rows = []
    for line in ocr_text.split("\n"):
        line = line.strip()
        if len(line) < 5:
            continue
        if re.search(r"\d", line):  # must contain a number
            rows.append(line)
    return rows

ROW_REGEX = re.compile(
    r"""
    (?P<name>[A-Za-z][A-Za-z\s\.\(\)/\-]+?)   # test name
    \s+
    (?P<value>\d+(\.\d+)?)                   # value
    \s*
    (?P<unit>[a-zA-Z/%µ]+)?                  # unit
    \s*
    (?P<range>\d+(\.\d+)?\s*[-–]\s*\d+(\.\d+)?)?
    """,
    re.VERBOSE
)

def parse_candidate_rows(rows):
    parsed = []
    for line in rows:
        m = ROW_REGEX.search(line)
        if not m:
            continue
        parsed.append({
            "raw_name": m.group("name").strip(),
            "value": float(m.group("value")),
            "unit": m.group("unit"),
            "reference_range": m.group("range"),
            "raw_line": line
        })
    return parsed

from collections import defaultdict
def build_test_ontology(annotation_files):
    ontology = defaultdict(set)

    for file in annotation_files:
        with open(file) as f:
            data = json.load(f)

        # SAFETY CHECK
        if "test_results" not in data:
            continue

        for test in data["test_results"]:
            # SAFETY CHECK
            if "test_name" not in test:
                continue

            norm = normalize_test_name(test["test_name"])
            ontology[norm].add(test["test_name"])

    return ontology


from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

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



candidate_rows = extract_candidate_rows(text)
parsed_rows = parse_candidate_rows(candidate_rows)

# build ontology from ALL annotation files
annotation_files = list(DATA_ROOT.glob("*.json"))
ontology = build_test_ontology(annotation_files)

extracted_data = normalize_extracted_rows(parsed_rows, ontology)

def calculate_accuracy(extracted_data, ground_truth_json):
    """
    Compare with fuzzy matching since OCR won't be perfect
    """
    # Build a lookup dictionary with normalized names
    gt_tests = {}
    for test in ground_truth_json['test_results']:
        normalized_name = normalize_test_name(test['test_name'])
        gt_tests[normalized_name] = test
    
    correct_names = 0
    correct_values = 0
    total = len(ground_truth_json['test_results'])
    
    matched_tests = []
    unmatched_tests = []
    
    for extracted in extracted_data:
        test_name = normalize_test_name(extracted['test_name'])
        
        # Try exact match first
        if test_name in gt_tests:
            correct_names += 1
            matched_tests.append(extracted['test_name'])
            
            gt_value = gt_tests[test_name]['value']
            if abs(extracted['value'] - gt_value) < 0.01:
                correct_values += 1
        else:
            # Try partial matching (if normalized name is substring of ground truth)
            found = False
            for gt_name in gt_tests.keys():
                if test_name in gt_name or gt_name in test_name:
                    correct_names += 1
                    matched_tests.append(f"{extracted['test_name']} -> {gt_tests[gt_name]['test_name']}")
                    
                    gt_value = gt_tests[gt_name]['value']
                    if abs(extracted['value'] - gt_value) < 0.01:
                        correct_values += 1
                    found = True
                    break
            
            if not found:
                unmatched_tests.append(extracted['test_name'])
    
    print(f"\nTest Name Accuracy: {correct_names}/{total} = {correct_names/total*100:.1f}%")
    print(f"Value Accuracy: {correct_values}/{total} = {correct_values/total*100:.1f}%")
    print(f"\nMatched tests: {matched_tests}")
    print(f"Unmatched tests: {unmatched_tests}")
    
    return correct_names/total, correct_values/total

ground_truth_json_path=DATA_ROOT/ "coagulation_002_annotations.json"
with open(ground_truth_json_path, 'r') as f:
    ground_truth_json = json.load(f)
accuracy=calculate_accuracy(extracted_data,ground_truth_json)
print("accuracy:",accuracy)

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

export_report_json(
    report_id="coagulation_002",
    extracted_data=extracted_data
)

