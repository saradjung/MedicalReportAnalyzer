import pytesseract
from PIL import Image
from pathlib import Path


# CONFIG: directory set
DATA_ROOT = Path("C:/medical_data")
OCR_OUTPUT_DIR = DATA_ROOT / "ocr_outputs"

OCR_OUTPUT_DIR.mkdir(exist_ok=True)


# find images in png format from base directory
images = list(DATA_ROOT.glob("*.png")) + list(DATA_ROOT.glob("*.jpg"))

if not images:
    print("❌ No image files found in medical_data folder.")
    exit()

print(f"📄 Found {len(images)} images. Starting OCR...\n")


# OCR PROCESSING: for all images in png format

for image_path in images:
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)

        output_file = OCR_OUTPUT_DIR / f"{image_path.stem}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"OCR done: {image_path.name}")

    except Exception as e:
        print(f"Error processing {image_path.name}: {e}")

print("\nOCR processing completed.")
