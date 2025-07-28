from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document
from typing import List
import re


class DocumentLoader(BaseLoader):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            latex_content = f.read()

        # Clean only noisy LaTeX preamble, keep all structure
        cleaned_text = self._strip_irrelevant_preamble(latex_content)

        # Wrap as LangChain Document
        metadata = {"source": self.file_path}
        return [Document(page_content=cleaned_text, metadata=metadata)]

    def _strip_irrelevant_preamble(self, text: str) -> str:
        # Remove comments
        text = re.sub(r"%.+", "", text)
        # Remove documentclass, usepackage, geometry, etc.
        text = re.sub(r"\\(documentclass|usepackage|geometry|pagestyle|begin\{document\}|end\{document\})\{[^}]*\}", "", text)
        text = re.sub(r"\\(title|author|date)\{[^}]*\}", "", text)
        # Remove empty lines
        text = re.sub(r"\n\s*\n", "\n", text)
        return text.strip()
