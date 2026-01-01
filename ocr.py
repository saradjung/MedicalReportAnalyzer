import pytesseract
from PIL import Image
import cv2
from pathlib import Path
import numpy as np
import re, json

DATA_ROOT=Path("C:/medical_data")
image_path= DATA_ROOT/ "cbc_report_001.png"

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

def extract_test_results(ocr_text):
    """
    Extract test name, value, and unit from OCR text
    This is a simple pattern-matching approach to start
    """
    results=[]

    # Pattern to match lines like: "Hemoglobin    12.1    gm/dl    13.0-17.0"
    # This is a simplified pattern - we'll need to refine it
    pattern=r'([A-Za-z\s\(\)]+)\s+([\d\.]+)\s+([\w/]+)\s+([\d\.\-]+)'
    matches=re.findall(pattern, ocr_text)
    #print("matches:",matches)

    for match in matches:
        test_name=match[0].strip()
        value=float(match[1])
        unit=match[2].strip()
        ref_range=match[3].strip()

        results.append({"test_name": test_name,
            "value": value,
            "unit": unit,
            "reference_range": ref_range})

        return results

extracted_data=extract_test_results(text)
print(json.dumps(extracted_data,indent=2))

