import streamlit as st
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import json
import re

# Load PaddleOCR (CPU mode)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Minimal preprocessing (preserve RGB format)
def preprocess_image(pil_img):
    return np.array(pil_img.convert("RGB"))

# Extract raw text using PaddleOCR
def extract_text(image):
    result = ocr.ocr(image)
    lines = []
    if result and isinstance(result[0], list):
        for line in result[0]:
            if len(line) >= 2:
                lines.append(line[1][0])
    return "\n".join(lines) if lines else "[NO TEXT DETECTED]"

# Extract structured fields using regex
def extract_fields(text):
    def match(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m
        return None

    return {
        "issuance_date": (m := match([r"Issuance\s*Date[:\- ]+([\d]{2}[\-/][\d]{2}[\-/][\d]{4})"])) and m.group(1),
        "ccc_reference_number": (m := match([r"CCC Reference Number[:\- ]+([A-Z0-9\-]+)"])) and m.group(1),
        "company_name": (m := match([r"confirm that\s+([^\n]+)"])) and m.group(1).strip(),
        "commercial_registration_number": (m := match([r"CRN[-: ]?(\d+)", r"Commercial Registration No.*?(\d+)"])) and m.group(1),
        "address": (m := match([r"\d{1,4} [A-Za-z0-9 ]+Blvd"])) and m.group(0),
        "assessment_standard": (m := match([r"compliance with (.+?)\.", r"Standard\s*\((.*?)\)"])) and m.group(1),
        "assessment_period": {
            "start_date": (m := match([r"between\s+([\d\-\/]+)\s+and\s+([\d\-\/]+)"])) and m.group(1),
            "end_date": m and m.group(2)
        } if (m := match([r"between\s+([\d\-\/]+)\s+and\s+([\d\-\/]+)"])) else None,
        "classification": (m := match([r"classification of[:\- ]+([A-Z]), Type[:\- ]+(\w+)", r"Type[:\- ]+(\w+)"])) and (m.group(1) if m.lastindex > 1 else None),
        "type": m and (m.group(2) if m.lastindex > 1 else m.group(1))
    }

# Streamlit UI
st.set_page_config(page_title="Certificate Extractor", layout="centered")
st.title("📜 Cybersecurity Certificate OCR Extractor")

uploaded_file = st.file_uploader("📤 Upload a certificate image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with st.spinner("🔍 Running OCR..."):
        preprocessed = preprocess_image(image)
        text = extract_text(preprocessed)
        fields = extract_fields(text)

    st.subheader("📄 Raw OCR Text")
    st.text(text)

    st.subheader("📋 Extracted Fields")
    st.json(fields)

    st.subheader("📥 Download Results")
    col1, col2 = st.columns(2)
    col1.download_button("⬇️ Download JSON", data=json.dumps(fields, indent=2), file_name="output.json")
    col2.download_button("⬇️ Download Raw Text", data=text, file_name="raw_text.txt")
