import streamlit as st
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image

ocr = PaddleOCR(use_angle_cls=True, lang='en')

def preprocess_image(pil_img):
    return np.array(pil_img.convert("RGB"))

def extract_text(image):
    result = ocr.ocr(image)
    return "\n".join([line[1][0] for line in result[0]]) if result and len(result[0]) > 0 else "[NO TEXT DETECTED]"

st.title("🔍 PaddleOCR Test")

uploaded_file = st.file_uploader("Upload certificate", type=["jpg", "jpeg", "png"])



    text = extract_text(preprocessed)

    st.subheader("📄 OCR Text")
    st.text(text)
