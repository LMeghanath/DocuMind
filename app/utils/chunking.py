import os
import logging
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .preprocessing import preprocess_text

logger = logging.getLogger(__name__)

def extract_and_chunk_file(file_path):
    """
    Extracts text from a file (PDF/TXT) using LangChain loaders,
    cleans it using module 4 preprocess, and chunks it.
    """
    try:
        documents = []
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif ext == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file format for extraction: {ext}")

        # Preprocess text content 
        for i, doc in enumerate(documents):
            doc.page_content = preprocess_text(doc.page_content)
            # Add simple source name to metadata without full path
            doc.metadata["source"] = os.path.basename(file_path)
            doc.metadata["page"] = i + 1

        # Better chunking size (800 token length approximation, overlapping 100)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )

        chunks = text_splitter.split_documents(documents)
        return chunks

    except Exception as e:
        logger.error(f"Error extracting and chunking file {file_path}: {str(e)}")
        raise e
