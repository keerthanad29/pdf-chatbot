import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(text)

def get_answer(user_question, chunks):
    vectorizer = TfidfVectorizer()
    chunk_vectors = vectorizer.fit_transform(chunks)
    question_vector = vectorizer.transform([user_question])
    similarities = cosine_similarity(question_vector, chunk_vectors)[0]
    top_indices = np.argsort(similarities)[-3:][::-1]
    context = "\n\n".join([chunks[i] for i in top_indices])

    prompt = f"""Answer the question based on the context below.
If the answer is not in the context, say "Answer not found in the document."

Context: {context}

Question: {user_question}

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

st.set_page_config(page_title="PDF Chatbot")
st.title("📄 PDF Q&A Chatbot")

if "chunks" not in st.session_state:
    st.session_state.chunks = []

with st.sidebar:
    st.header("Upload PDF")
    pdf_docs = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")
    if st.button("Process PDF"):
        if pdf_docs:
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                st.session_state.chunks = get_text_chunks(raw_text)
                st.success("Done! Now ask questions.")
        else:
            st.warning("Please upload a PDF first!")

user_question = st.text_input("Ask a question about your PDF:")
if user_question:
    if st.session_state.chunks:
        with st.spinner("Finding answer..."):
            answer = get_answer(user_question, st.session_state.chunks)
            st.write("**Answer:**", answer)
    else:
        st.warning("Please upload and process a PDF first!")