
from langchain.tools import tool


@tool
def search_resume(query: str) -> List[str]:
    results = resume_vector_store.similarity_search(query)
    return [doc.page_content for doc in results]

@tool
def search_jd(query: str) -> List[str]:
    return [doc.page_content for doc in jd_all_splits]