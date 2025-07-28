from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from newspaper import Article
from typing import List


def load_jd(source_type: str, path_or_url: str) -> List[Document]:
    """
    Load job description from either a PDF file or a URL, using content cleaning.

    Args:
        source_type: "pdf" or "url"
        path_or_url: file path or link

    Returns:
        List[Document]
    """
    if source_type == "pdf":
        loader = PyMuPDFLoader(path_or_url)
        return loader.load()

    elif source_type == "url":
        article = Article(path_or_url)
        article.download()
        article.parse()
        clean_text = article.text.strip()
        return [Document(page_content=clean_text, metadata={"source": path_or_url})]

    else:
        raise ValueError("Invalid source_type. Use 'pdf' or 'url'.")
