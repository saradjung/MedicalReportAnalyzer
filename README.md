# MedAnalyzer

MedAnalyzer is a Django-based web application that allows users to upload medical reports (such as lab test images), extract structured data using OCR and rule-based parsing, and generate patient-friendly explanations using a large language model (LLM). The goal is to improve accessibility and understanding of medical reports without providing diagnosis or treatment advice.

## Features

- User authentication (registration, login, logout)
- Secure upload of medical report files
- Image preprocessing and OCR using OpenCV and Tesseract
- Rule-based extraction of test names, values, units, and reference ranges
- Normalization using ontology built from annotated JSON files
- Automatic classification of results (normal, low, high)
- Generation of structured JSON medical reports
- Patient-friendly explanations using Gemini API (LLM)
- Dashboard for managing uploaded reports
- Responsive user interface built with Tailwind CSS

## Tech Stack

- Backend: Python, Django
- Frontend: Django Templates, Tailwind CSS
- OCR: OpenCV, PyTesseract, Pillow, NumPy
- AI Integration: Google Gemini API
- Database: SQLite (default, configurable)
- Environment Management: python-dotenv

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/medanalyzer.git
cd medanalyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables
Create a .env file in the project root:
```bash
GEMINI_API_KEY=your_api_key_here
```

### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start development server
```bash
python manage.py runserver
```
Open browser and navigate to:
```bash
http://127.0.0.1:8000/
```

## Usage

1. Register a new account.
2. Log in to the dashboard.
3. Upload a medical report image (PNG/JPG).
4. The system processes the file using OCR and parsing.
5. View structured extracted data and AI-generated explanation in the report detail page.

## Important Disclaimer

- This project is intended for educational and informational purposes only.
- The system does not provide medical diagnosis.
- The system does not prescribe treatment.
- Users must always consult a qualified healthcare professional for medical decisions.

## Authors

- [Sarad Thapa](https://np.linkedin.com/in/sarad-jung-thapa-9b5682297)  
- [Rabin Shrestha](https://github.com/rabinshresthaaa)