import pdfplumber
import os
import json
from groq import Groq
from dotenv import load_dotenv


def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_syllabus(text):
    prompt = f"""
You are a structured data explorer.

Extract ONLY syllabus units.

Each unit should become one JSON object.

Do NOT create a separate object for the list of all units.
Do NOT treat unit names as chapters.
The chapters field should contain only the topics listed under that unit.

Return ONLY valid JSON.

Schema:

[
  {{
    "subject": "string",
    "unit": "string",
    "chapters": ["string"],
    "exam_date": "YYYY-MM-DD or null",
    "weightage": "percentage or null"
  }}
]

Syllabus text:

{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
        max_tokens=4000
    )

    return response.choices[0].message.content


def clean_json_response(raw):
    start = raw.find("[")
    end = raw.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("Invalid JSON format in response")

    return raw[start:end + 1]


def main():
    pdf_path = r"C:\Users\Ankit\OneDrive\Desktop\Folder\PYTHON PROGRAMMING (BCC-402).pdf"

    print("Reading PDF...")
    text = extract_text_from_pdf(pdf_path)

    print("Extracting syllabus...")
    raw_output = extract_syllabus(text)

    print("Cleaning response...")
    cleaned_response = clean_json_response(raw_output)

    print("Parsing JSON...")
    data = json.loads(cleaned_response)

    output_file = "syllabus_data.json"

    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2)

    print(f"Saved successfully!")
    print("File location:", os.path.abspath(output_file))


 