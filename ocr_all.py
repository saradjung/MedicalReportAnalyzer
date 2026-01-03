import pytesseract
from PIL import Image
from pathlib import Path
import os
import json
import re
import matplotlib.pyplot as plt

DATA_ROOT = Path("C:/medical_data")

# Ensure 'outputs' folder exists
outputs_folder = DATA_ROOT / "outputs"
outputs_folder.mkdir(parents=True, exist_ok=True)

def ocr_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

def parse_ocr_text(ocr_text):
    test_pattern = r"([a-zA-Z0-9\+\-]+)\s*[\:\-\=\>]\s*([0-9\.\-]+)\s*(\w+)?"
    tests = []
    matches = re.findall(test_pattern, ocr_text)
    
    for match in matches:
        test_name = match[0]
        test_value = match[1]
        test_unit = match[2] if len(match) > 2 else None
        
        test_result = {
            'test_name': test_name,
            'value': test_value,
            'unit': test_unit
        }
        tests.append(test_result)
    
    return tests

def save_parsed_data_to_json(image_name, parsed_data):
    image_name = Path(image_name)  # Convert string to Path object
    json_filename = outputs_folder / f"{image_name.stem}.json"
    
    report_data = {
        "report_metadata": {
            "image_filename": image_name.name,
        },
        "test_results": parsed_data
    }
    
    with open(json_filename, 'w') as json_file:
        json.dump(report_data, json_file, indent=4)
    print(f"Saved data to {json_filename}")

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def compare_test_results(manual_data, auto_data):
    manual_tests = manual_data["test_results"]
    auto_tests = auto_data["test_results"]
    
    errors = []
    
    for manual_test, auto_test in zip(manual_tests, auto_tests):
        # Check if the necessary keys exist in both manual and auto data
        if 'test_name' not in manual_test or 'test_name' not in auto_test:
            errors.append(f"Missing 'test_name' in one of the test results")
            continue
        
        # Get values for comparison, using .get() to avoid KeyErrors for missing keys
        test_name_m = manual_test['test_name']
        test_value_m = manual_test['value']
        test_status_m = manual_test.get('status', 'N/A')  # Default to 'N/A' if missing
        
        test_name_a = auto_test['test_name']
        test_value_a = auto_test['value']
        test_status_a = auto_test.get('status', 'N/A')  # Default to 'N/A' if missing
        
        # Compare test names
        if test_name_m != test_name_a:
            errors.append(f"Test name mismatch: {test_name_m} vs {test_name_a}")
        
        # Compare test values
        if test_value_m != test_value_a:
            errors.append(f"Value mismatch for {test_name_m}: {test_value_m} vs {test_value_a}")
        
        # Compare test statuses
        if test_status_m != test_status_a:
            errors.append(f"Status mismatch for {test_name_m}: {test_status_m} vs {test_status_a}")
    
    return errors


def visualize_comparison(errors):
    section_errors = {}
    for error in errors:
        section_name = error.split(":")[0]
        section_errors[section_name] = section_errors.get(section_name, 0) + 1
    
    sections = list(section_errors.keys())
    errors_count = list(section_errors.values())
    
    plt.bar(sections, errors_count)
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Sections')
    plt.ylabel('Number of Errors')
    plt.title('Error Comparison: Manual vs Automatic Extraction')
    plt.tight_layout()
    plt.show()

def process_and_compare_all_reports():
    errors = []
    for image_file in os.listdir(DATA_ROOT):
        if image_file.endswith(".png"):
            image_path = DATA_ROOT / image_file
            print(f"Processing image: {image_path}")
            
            extracted_text = ocr_from_image(image_path)
            parsed_tests = parse_ocr_text(extracted_text)
            save_parsed_data_to_json(image_file, parsed_tests)
            
            image_file_path = Path(image_file)  # Convert image_file to Path object
            manual_json_path = DATA_ROOT / f"{image_file_path.stem}_annotations.json"
            
            if manual_json_path.exists():
                manual_data = load_json(manual_json_path)
                auto_data = load_json(outputs_folder / f"{image_file_path.stem}.json")
                comparison_errors = compare_test_results(manual_data, auto_data)
                errors.extend(comparison_errors)
            else:
                print(f"Warning: Manual data for {image_file} not found.")
    
    visualize_comparison(errors)

process_and_compare_all_reports()
