import time
import os
import streamlit as st
from PyPDF2 import PdfReader
from fpdf import FPDF

import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "AIzaSyBAiDEySfbOeYT9lSt-8DdxyuC2DVeAzCo"))

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

# Function to divide text into manageable chunks
def divide_text_into_chunks(text, chunk_size=2000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# Function to call Gemini API for content generation
def call_gemini_api(prompt, max_retries=3):
    retries = 0
    model = genai.GenerativeModel("gemini-1.5-flash")

    while retries < max_retries:
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            retries += 1
            wait_time = 2 ** retries  # Exponential backoff
            st.warning(f"Error with Gemini API: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    st.error("Max retries exceeded. Please try again later.")
    return None

# Function to review CTD documents
def review_ctd_documents(documents_texts):
    combined_text = "\n\n".join(documents_texts)
    chunks = divide_text_into_chunks(combined_text, chunk_size=3000)
    all_reviews = []

    prompt_template = """
    You are an expert in reviewing Common Technical Dossiers (CTDs) for regulatory compliance and quality.
    Analyze the following CTD content and provide a structured review with detailed comments for improvement.

    Content:
    {content}

    Provide your feedback in the format below:
    - Section of CTD: [Section Name]
    - Subsection of CTD: [Subsection Name]
    - Review Comments: [Detailed Feedback]
    """

    for chunk in chunks:
        prompt = prompt_template.format(content=chunk)
        review = call_gemini_api(prompt)
        if review:
            all_reviews.append(review)

    return "\n\n".join(all_reviews)

# Function to generate a PDF report
def generate_pdf_report(review_output):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Add Unicode font from specified path
    pdf.add_font("ArialUnicode", fname=r"D:\wobb\review\Arial.ttf", uni=True)
    pdf.set_font("ArialUnicode", size=12)
    pdf.multi_cell(0, 10, review_output)

    pdf_path = r"D:\wobb\review\CTD_Review_Report.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Streamlit App Layout
st.set_page_config(page_title="CTD PDF Review Analyzer", page_icon="📄", layout="wide")
st.title("📄 Common Technical Dossier (CTD) Review Analyzer")
st.markdown(
    """
    Upload the CTD documents for all 5 modules (in PDF format), and let our AI-powered system provide an extensive review with detailed comments and suggestions for improvement.
    After analysis, a structured review report will be generated in PDF format.
    """
)

# File uploader for all 5 modules
uploaded_files = []
for i in range(1, 6):
    uploaded_file = st.file_uploader(f"Upload Module {i} (PDF format only)", type=["pdf"], key=f"file_uploader_{i}")
    if uploaded_file:
        uploaded_files.append(uploaded_file)

# Analyze uploaded documents
if len(uploaded_files) == 5:
    with st.spinner("Extracting text from the PDFs..."):
        documents_texts = []
        for uploaded_file in uploaded_files:
            document_text = extract_text_from_pdf(uploaded_file)
            if document_text:
                documents_texts.append(document_text)

    if documents_texts:
        st.subheader("📑 Extracted Document Texts Preview")
        for i, text in enumerate(documents_texts, start=1):
            st.text_area(f"Preview of Extracted Text - Module {i}", text[:1000], height=200)

        if st.button("Analyze All Modules"):
            with st.spinner("Analyzing the documents using AI..."):
                review_output = review_ctd_documents(documents_texts)

            if review_output:
                st.subheader("🔍 AI-Generated Review")
                st.text_area("Review Output", review_output, height=500)

                pdf_path = generate_pdf_report(review_output)
                with open(pdf_path, "rb") as f:
                    st.download_button("Download Review Report (PDF)", f, file_name="CTD_Review_Report.pdf", mime="application/pdf")
            else:
                st.error("Failed to generate a review. Please try again.")
else:
    st.info("Please upload all 5 modules to proceed.")
