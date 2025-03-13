import pytesseract
import easyocr
from PIL import Image
import os

'''
# Set Tesseract OCR path (modify based on your OS)
pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"

def extract_text_tesseract(image_path):
    """Extracts text from an image using Tesseract OCR."""
    img = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(img)
    return extracted_text.strip()

def extract_text_easyocr(image_path):
    """Extracts text from an image using EasyOCR."""
    reader = easyocr.Reader(['en'])  # Language: English
    results = reader.readtext(image_path, detail=0)
    return " ".join(results)

def extract_text(image_path, method="tesseract"):
    """Extract text using selected OCR method."""
    if method == "tesseract":
        return extract_text_tesseract(image_path)
    elif method == "easyocr":
        return extract_text_easyocr(image_path)
    else:
        raise ValueError("Invalid method. Use 'tesseract' or 'easyocr'.")

# Example Usage
if __name__ == "__main__":
    image_path = "/Users/sanj/Documents/Projects/C532/grocery_bill/data/bill1.jpeg"
    raw_text = extract_text(image_path, method="tesseract")
    print("\nExtracted Text:\n", raw_text)
'''
'''
import easyocr

def extract_text_easyocr(image_path):
    """Extracts text from an image using EasyOCR."""
    reader = easyocr.Reader(['en'])  # English language
    results = reader.readtext(image_path, detail=0)  # Get extracted text
    return "\n".join(results)

# Example Usage
if __name__ == "__main__":
    image_path = "/Users/sanj/Documents/Projects/C532/grocery_bill/data/bill1.jpeg"
    extracted_text = extract_text_easyocr(image_path)
    print("\nExtracted Text (EasyOCR):\n", extracted_text)

'''

import easyocr
import re

def extract_text_easyocr(image_path):
    """Extracts raw text from an image using EasyOCR."""
    reader = easyocr.Reader(['en'])  # English
    results = reader.readtext(image_path, detail=0)
    raw_text = "\n".join(results)  # Convert list to text format
    return raw_text

def is_price(line):
    """Detects if a line is a price (e.g., 1.79, 3.49, 10.99)"""
    return bool(re.match(r'^\d+(\.\d{2})$', line.strip()))

def merge_multiline_entries(lines):
    """Merges product names with their prices."""
    cleaned_lines = []
    temp_line = ""

    for line in lines:
        line = line.strip()

        if is_price(line):
            # If last entry was an item name, merge it with this price
            if temp_line:
                cleaned_lines.append(f"{temp_line} {line}")
                temp_line = ""  # Reset temp storage
            else:
                cleaned_lines.append(line)  # Store price separately (rare case)
        else:
            # If line is an item name, store it temporarily
            temp_line = line

    return cleaned_lines

def clean_ocr_text(raw_text):
    """Dynamically cleans and structures OCR-extracted text for parsing."""
    cleaned_lines = []
    
    for line in raw_text.split("\n"):
        line = line.strip()

        # Ignore lines that contain non-relevant text dynamically
        if any(ignore_word in line.lower() for ignore_word in ["your cashier", "tax", "total", "payment", "credit", "balance", "auth", "change", "card", "amount", "savings"]):
            continue

        # Remove unwanted special characters (excluding currency symbols)
        line = re.sub(r'[^\w\s\.\$,]', '', line)

        # Standardize price formats (convert 1,99 -> 1.99)
        line = re.sub(r'(\d+),(\d{2})', r'\1.\2', line)  # Convert 1,99 → 1.99

        # Remove units like "Ib", "Jb", "b" that don't add value
        line = re.sub(r'\b(lb|Ib|Jb|b)\b', '', line, flags=re.IGNORECASE)

        # Remove trailing spaces
        line = line.strip()

        if line:
            cleaned_lines.append(line)

    # Merge product names with their prices
    cleaned_lines = merge_multiline_entries(cleaned_lines)

    return cleaned_lines

# Example Usage
if __name__ == "__main__":
    image_path = "/Users/sanj/Documents/Projects/C532/grocery_bill/data/bill2.jpeg"
    extracted_text = extract_text_easyocr(image_path)
    structured_text = clean_ocr_text(extracted_text)

    print("\nCleaned & Structured OCR Text:\n")
    for line in structured_text:
        print(line)

