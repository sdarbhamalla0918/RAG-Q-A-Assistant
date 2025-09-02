import os 
import streamlit as st 
from streamlit import components
from streamlit.components.v1 import html
from dotenv import load_dotenv
from PyPDF2 import PdfReader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size= 10000, chunk_overlap =1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding = embeddings)
    vector_store.save_local('faiss_index')
    

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.3)
    
    prompt = PromptTemplate(template = prompt_template, input_variables = ['context','question'])
    chain = load_qa_chain(model, chain_type="stuff", prompt= prompt )
    return chain


def user_input():
    st.markdown("---")
    st.markdown("### 💬 Ask your question here")
    user_question = st.text_input(" ", label_visibility="collapsed", placeholder="Type your question and press Enter...")
    if user_question:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain({'input_documents': docs, 'question': user_question}, return_only_outputs=True)
        st.markdown("#### 🧠 Answer")
        st.success(response['output_text'])

def main():
    st.set_page_config(page_title="Chat PDF", layout="wide", page_icon=":books:")
    st.markdown("<h1 style='text-align: center;'>📚 Chat with Multiple PDFs</h1>", unsafe_allow_html=True)
    
    linkedin_profile_link = "https://www.linkedin.com/in/aritramukherjeeofficial/"
    github_profile_link = "https://github.com/AritraOfficial"

    st.sidebar.markdown(
        f"[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)]({linkedin_profile_link}) "
        f"[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)]({github_profile_link})"
    )
    with st.sidebar:
        st.title("📤 Upload Your PDFs")
        pdf_docs = st.file_uploader("Upload PDF Files", accept_multiple_files=True)
        if st.button("🚀 Process", help="Click to process PDF files", use_container_width=True):
            with st.spinner("⏳ Processing your files..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("✅ Done! Your PDF files are processed.")
                st.info("You can now ask questions from the uploaded PDF files.")

    user_input()

if __name__ == '__main__':
    main()