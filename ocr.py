import pytesseract
from PIL import Image
import cv2
from pathlib import Path
import numpy as np

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


