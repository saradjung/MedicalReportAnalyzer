import re
import json

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

UNIT_MAP = {
    # Variations of mg/dL
    "mgdl": "mg/dL",
    "mg/dl": "mg/dL",
    "mgdl": "mg/dL",
    "mg/dL": "mg/dL",
    
    # Variations of g/dL
    "gdl": "g/dL",
    "g/dl": "g/dL",
    "gm/dl": "g/dL",
    "gmdl": "g/dL",
    "g/dL": "g/dL",
    
    # mmol/L variations
    "mmoll": "mmol/L",
    "mmol/l": "mmol/L",
    "mmol/L": "mmol/L",
    
    # U/L variations
    "ul": "U/L",
    "u/l": "U/L",
    "U/L": "U/L",
    
    # Cell counts
    "cells/cumm": "cells/cumm",
    "cumm": "/cumm",
    "/cumm": "/cumm",
    "mill/cumm": "mill/cumm",
    "lakhs/cumm": "lakhs/cumm",
    
    # Other units
    "fl": "fl",
    "pg": "pg",
    "%": "%",
    "seconds": "seconds",
    "sec": "seconds",
}   

def normalize_unit(u):
    """Normalize unit to standard format"""
    if not u:
        return None
    
    # Remove all spaces and convert to lowercase
    u_clean = u.lower().replace(' ', '')
    
    # Look up in map
    normalized = UNIT_MAP.get(u_clean)
    
    if normalized:
        return normalized
    
    # If not in map, return cleaned version
    return u_clean


def normalize_extracted_rows(parsed_rows, ontology, threshold=0.60):
    normalized = []

    for row in parsed_rows:
        raw_norm = normalize_test_name(row["raw_name"])
        best_match = None
        best_score = 0

        for standard in ontology.keys():
            score = similarity(
                raw_norm,
                normalize_test_name(standard)   
            )
            if score > best_score:
                best_score = score
                best_match = standard

        normalized.append({
            "test_name": best_match if best_score >= threshold else row["raw_name"],
            "value": row.get("value"),
            "unit": normalize_unit(row.get("unit")),   
            "reference_range": row.get("reference_range"),
            "confidence": round(best_score, 2),
            "raw_line": row.get("raw_line")
        })

    return normalized

