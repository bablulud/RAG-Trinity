import pdfplumber
from typing import List, Tuple

def parse_pdf(pdf_path: str) -> str:
    """Parses a PDF, extracting both text and tables."""
    parsed_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    parsed_data.append(f"--- Page {page_num + 1} ---\n{text}\n\n")

                tables = page.extract_tables()
                for table in tables:
                    table_string = "\n".join([" | ".join(map(str, row)) for row in table])
                    if table_string:
                        parsed_data.append(f"--- Page {page_num + 1} Table ---\n{table_string}\n\n")
        return "".join(parsed_data)
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Splits text into overlapping chunks without relying on LangChain internals."""
    if not text:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: List[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks

def process_single_pdf(pdf_path: str, chunk_size: int, chunk_overlap: int) -> Tuple[List[str], str]:
    """Combines parsing and chunking for a single PDF."""
    print(f"Processing PDF: {pdf_path}")
    content = parse_pdf(pdf_path)
    if not content:
        return [], ""
    
    chunks = chunk_text(content, chunk_size, chunk_overlap)
    return chunks, content
