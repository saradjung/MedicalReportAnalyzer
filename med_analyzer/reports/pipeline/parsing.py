import re

def is_header_or_metadata(line):
    """Filter out headers, hospital names, dates, etc."""
    line_lower = line.lower()
    
    metadata_patterns = [
        r'hospital', r'diagnostic', r'laboratory', r'patient',
        r'doctor', r'dr\.', r'date', r'time', r'report',
        r'gender', r'age', r'sample', r'specimen', r'method',
        r'uhid', r'bill', r'ward', r'pathologist',
        r'^\d{2}[-/]\d{2}[-/]\d{2,4}',  # Dates
        r'mob\s*:', r'tel\s*:', r'email', r'address'
    ]
    
    return any(re.search(p, line_lower) for p in metadata_patterns)

def is_likely_test_name(name):
    """Check if name looks like a medical test"""
    name_lower = name.lower().strip()
    
    if len(name_lower) < 3:
        return False
    
    medical_keywords = [
        'count', 'level', 'acid', 'protein', 'albumin', 'hemoglobin',
        'glucose', 'cholesterol', 'bilirubin', 'creatinine', 'cell',
        'platelet', 'lymphocyte', 'neutrophil', 'ratio', 'volume'
    ]
    
    non_test_keywords = [
        'hospital', 'diagnostic', 'laboratory', 'doctor', 'patient',
        'report', 'pathologist', 'building', 'road', 'contact'
    ]
    
    for keyword in medical_keywords:
        if keyword in name_lower:
            return True
    
    for keyword in non_test_keywords:
        if keyword in name_lower:
            return False
    
    return True

def extract_unit_from_text(text):
    """
    More aggressive unit extraction that handles spacing issues
    """
    # Remove the value number first to avoid confusion
    text_without_value = re.sub(r'^\s*\d+[.,]?\d*\s*', '', text)
    
    # Common unit patterns with flexible spacing and slashes
    unit_patterns = [
        # With slash
        r'(mg\s*/\s*dl|g\s*/\s*dl|mmol\s*/\s*l|u\s*/\s*l|iu\s*/\s*l|ng\s*/\s*ml)',
        # Without slash but common medical units
        r'(mgdl|gdl|mmoll|cells/cumm|cumm|mill/cumm|lakhs/cumm)',
        # Single letter units
        r'\b(fl|pg|seconds?|sec)\b',
        # Percentage
        r'%',
    ]
    
    for pattern in unit_patterns:
        match = re.search(pattern, text_without_value, re.IGNORECASE)
        if match:
            unit = match.group(0)
            # Normalize the unit
            unit = re.sub(r'\s+', '', unit)  # Remove all spaces
            return unit
    
    return None

def extract_test_components(line):
    """Extract test components with flexible parsing"""
    numbers = re.findall(r'\d+[.,]?\d*', line)
    
    if len(numbers) < 1:
        return None
    
    # Find the most likely test value
    value = None
    value_idx = 0
    
    for i, num in enumerate(numbers):
        try:
            num_float = float(num.replace(',', '.'))
            if num_float < 10000:  # Medical values typically < 10000
                value = num_float
                value_idx = i
                break
        except ValueError:
            continue
    
    if value is None:
        return None
    
    # Extract test name (before value)
    value_pattern = re.escape(numbers[value_idx])
    match = re.search(value_pattern, line)
    
    if not match:
        return None
    
    test_name = line[:match.start()].strip()
    remaining = line[match.end():].strip()
    
    # Clean test name
    test_name = re.sub(r'^[^\w]+', '', test_name)
    test_name = re.sub(r'^\d+\.?\s*', '', test_name)
    
    if len(test_name) < 2:
        return None
    
    # NEW: Better unit extraction
    unit = extract_unit_from_text(remaining)
    
    # Extract reference range
    ref_range = None
    range_match = re.search(r'(\d+[.,]?\d*)\s*[-–]\s*(\d+[.,]?\d*)', remaining)
    
    if range_match:
        ref_range = range_match.group(0).replace(',', '.')
    
    return {
        "raw_name": test_name,
        "value": value,
        "unit": unit,
        "reference_range": ref_range,
        "raw_line": line
    }

def extract_candidate_rows(ocr_text):
    """Extract lines that might contain test results"""
    rows = []
    for line in ocr_text.split("\n"):
        line = line.strip()
        if len(line) < 5:
            continue
        if not re.search(r"\d", line):
            continue
        if is_header_or_metadata(line):
            continue
        rows.append(line)
    return rows

def parse_candidate_rows(rows):
    """Parse candidate rows into structured data"""
    parsed = []
    for line in rows:
        test_data = extract_test_components(line)
        if test_data and test_data.get('value') is not None:
            if is_likely_test_name(test_data['raw_name']):
                parsed.append(test_data)
    return parsed