import io


async def parse_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")


async def parse_docx(content: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


async def parse_pdf(content: bytes) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


PARSERS = {
    ".txt": parse_txt,
    ".docx": parse_docx,
    ".pdf": parse_pdf,
}


async def parse_file(filename: str, content: bytes) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    parser = PARSERS.get(ext)
    if not parser:
        raise ValueError(f"不支持的文件格式: {ext}，仅支持 .txt, .docx, .pdf")
    text = await parser(content)
    if not text.strip():
        raise ValueError("未能从文件中提取到文本内容")
    return text
