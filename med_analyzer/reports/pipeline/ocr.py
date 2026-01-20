import pytesseract
from PIL import Image
import cv2
from pathlib import Path
import re


DATA_ROOT=Path("C:/medical_data")
image_path= DATA_ROOT/ "cbc_report_001.png"

image=Image.open(image_path)
#image.show()

text= pytesseract.image_to_string(image)
print("raw OCR output:")
print(text)
print("\n" + "="*50 + "\n")
def generate_preprocessed_versions(image_path):
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    versions = {}

    # 1. Raw grayscale (baseline)
    versions["raw"] = gray

    # 2. Mild denoise
    versions["denoised"] = cv2.medianBlur(gray, 3)

    # 3. Adaptive threshold (SAFE)
    versions["adaptive"] = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10
    )

    return versions

def ocr_with_fallback(image_path):
    versions = generate_preprocessed_versions(image_path)

    ocr_results = {}
    for name, img in versions.items():
        text = pytesseract.image_to_string(img)
        ocr_results[name] = text

    return ocr_results

def score_ocr_text(text):
    lines = text.split("\n")
    score = 0

    for line in lines:
        if re.search(r"\d", line):
            score += 1
        if re.search(r"(mg|dl|g/dl|mmol|%)", line.lower()):
            score += 2

    return score

def get_best_ocr_text(image_path):
    ocr_results=ocr_with_fallback(image_path)
    best_text=""
    best_score=-1
    best_version=None
    for name, text in ocr_results.items():
        score=score_ocr_text(text)
        print(f"OCR version '{name}' score:{score}")

        if score> best_score:
            best_score=score
            best_text=text
            best_version=name
    print(f'\n using OCR version: {best_version}')
    return best_text


versions = generate_preprocessed_versions(image_path)
cv2.imwrite("preprocessed.png", versions["adaptive"])
text=get_best_ocr_text(image_path)

print(text)
