from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from models import db, Paper
import os

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


load_dotenv()

INDEX_PATH = "faiss_index"

# Uses OPENAI_API_KEY from .env automatically
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)


def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE ,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def load_or_create_index():
    index_file = os.path.join(INDEX_PATH, "index.faiss")

    if os.path.exists(index_file):
        return FAISS.load_local(
            INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    return None


def save_index(vectorstore):
    vectorstore.save_local(INDEX_PATH)


def add_paper_to_index(paper_id, filename, text):
    chunks = split_text(text)

    paper = Paper.query.get(paper_id)
    paper.chunk_count = len(chunks)
    paper.chunk_size = CHUNK_SIZE
    paper.chunk_overlap = CHUNK_OVERLAP
    db.session.commit()

    metadatas = [
        {"paper_id": paper_id, "filename": filename}
        for _ in chunks
    ]

    existing = load_or_create_index()

    if existing:
        existing.add_texts(chunks, metadatas=metadatas)
        save_index(existing)
    else:
        vectorstore = FAISS.from_texts(
            chunks,
            embeddings,
            metadatas=metadatas,
        )
        save_index(vectorstore)


def search_all(query, k=5):
    vectorstore = load_or_create_index()

    if not vectorstore:
        return []

    return vectorstore.similarity_search(query, k=k)