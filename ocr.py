import pytesseract
from PIL import Image
import cv2
from pathlib import Path
import numpy as np

DATA_ROOT=Path("C:/medical_data")
image_path= DATA_ROOT/ "cbc_report_001.png"

image=Image.open(image_path)

text= pytesseract.image_to_string(image)
print("raw OCR output:")
print(text)
print("\n" + "="*50 + "\n")