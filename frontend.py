import streamlit as st
import requests

st.title("Certificate Data Extractor")
uploaded_file = st.file_uploader("Upload Certificate Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Certificate")
    if st.button("Extract Data"):
        files = {"file": uploaded_file.getvalue()}
        response = requests.post("http://localhost:8000/extract", files=files)
        if response.status_code == 200:
            data = response.json()
            st.json(data)
        else:
            st.error("Failed to extract data.")