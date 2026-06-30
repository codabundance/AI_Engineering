import os
import glob
import sys
from openai import OpenAI
import tiktoken
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.manifold import TSNE
import plotly.graph_objects as go

def main():
    load_dotenv(override=True)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai = OpenAI(api_key=openai_api_key)
    MODEL = "gpt-4.1-nano"
    db_name = "vector_db"

    knowledge_base_path = "knowledge-base/**/*.md"
    files = glob.glob(knowledge_base_path, recursive=True)
    print(f"Found {len(files)} files in the knowledge base")

    entire_knowledge_base = ""

    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            entire_knowledge_base += f.read()
            entire_knowledge_base += "\n\n"

    print(f"Total characters in knowledge base: {len(entire_knowledge_base):,}")

    # How many tokens in all the documents?

    encoding = tiktoken.encoding_for_model(MODEL)
    tokens = encoding.encode(entire_knowledge_base)
    token_count = len(tokens)
    print(f"Total tokens for {MODEL}: {token_count:,}")

    # Load in everything in the knowledgebase using LangChain's loaders

    folders = glob.glob("knowledge-base/*")

    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)

    print(f"Loaded {len(documents)} documents")
    print(f"First document: {documents[0]}")
    # Split the documents into chunks

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    # Embed the chunks
    # Pick an embedding model

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    #embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    if os.path.exists(db_name):
        Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()
    #langchains way of combining both vector store and embedding generation
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)
    print(f"Vectorstore created with {vectorstore._collection.count()} documents")

    # Let's investigate the vectors

    collection = vectorstore._collection #rows in sqlite3 table, each chunk is a row
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")

if __name__ == "__main__":
    sys.exit(main())