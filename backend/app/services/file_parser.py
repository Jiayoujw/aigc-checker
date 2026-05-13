import asyncio
import io
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

_executor = ThreadPoolExecutor(max_workers=4)


def _parse_txt_sync(content: bytes) -> str:
    text = content.decode("utf-8", errors="ignore")
    if not text.strip():
        raise ValueError("未能从文件中提取到文本内容")
    return text


def _parse_docx_sync(content: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        raise ValueError("未能从文件中提取到文本内容")
    return "\n".join(paragraphs)


def _parse_pdf_from_bytes(content: bytes) -> str:
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    page_count = doc.page_count

    if page_count < 10:
        pages = []
        for i in range(page_count):
            text = doc[i].get_text()
            if text:
                pages.append(text)
        doc.close()
        result = "\n".join(pages)
        if not result.strip():
            raise ValueError("未能从文件中提取到文本内容，文件可能为扫描图片PDF")
        return result

    # Parallel parse for large documents
    chunk_size = max(1, page_count // 4)
    chunks = []
    for start in range(0, page_count, chunk_size):
        end = min(start + chunk_size, page_count)
        chunks.append(range(start, end))

    def _parse_chunk(content: bytes, page_range: range) -> list[str]:
        local_doc = fitz.open(stream=content, filetype="pdf")
        results = []
        for i in page_range:
            text = local_doc[i].get_text()
            if text:
                results.append(text)
        local_doc.close()
        return results

    all_pages = []
    futures = [_executor.submit(_parse_chunk, content, chunk) for chunk in chunks]
    for f in futures:
        all_pages.extend(f.result())

    doc.close()

    result = "\n".join(all_pages)
    if not result.strip():
        raise ValueError("未能从文件中提取到文本内容，文件可能为扫描图片PDF")
    return result


def _parse_pdf_from_path(file_path: str) -> str:
    """Parse PDF directly from disk — memory-efficient for huge files.
       PyMuPDF reads pages on demand, so only the current page is in RAM."""
    import fitz

    doc = fitz.open(file_path)
    page_count = doc.page_count

    if page_count < 10:
        pages = []
        for i in range(page_count):
            text = doc[i].get_text()
            if text:
                pages.append(text)
        doc.close()
        result = "\n".join(pages)
        if not result.strip():
            raise ValueError("未能从文件中提取到文本内容，文件可能为扫描图片PDF")
        return result

    # Parallel processing by page ranges from disk
    chunk_size = max(1, page_count // 4)
    chunks = []
    for start in range(0, page_count, chunk_size):
        end = min(start + chunk_size, page_count)
        chunks.append(range(start, end))

    def _parse_chunk_from_path(file_path: str, page_range: range) -> list[str]:
        local_doc = fitz.open(file_path)
        results = []
        for i in page_range:
            text = local_doc[i].get_text()
            if text:
                results.append(text)
        local_doc.close()
        return results

    all_pages = []
    futures = [_executor.submit(_parse_chunk_from_path, file_path, chunk) for chunk in chunks]
    for f in futures:
        all_pages.extend(f.result())

    doc.close()

    result = "\n".join(all_pages)
    if not result.strip():
        raise ValueError("未能从文件中提取到文本内容，文件可能为扫描图片PDF")
    return result


PARSERS_BYTES = {
    ".txt": _parse_txt_sync,
    ".docx": _parse_docx_sync,
    ".pdf": _parse_pdf_from_bytes,
}


async def parse_file(
    filename: str,
    content: bytes | None = None,
    on_progress: Callable[[int], None] | None = None,
    file_path: str | None = None,
) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower()

    if on_progress:
        on_progress(10)

    loop = asyncio.get_running_loop()

    if ext == ".pdf" and file_path:
        text = await loop.run_in_executor(_executor, _parse_pdf_from_path, file_path)
    elif content is not None:
        parser = PARSERS_BYTES.get(ext)
        if not parser:
            raise ValueError(f"不支持的文件格式: {ext}，仅支持 .txt, .docx, .pdf")
        text = await loop.run_in_executor(_executor, parser, content)
    else:
        raise ValueError("无文件内容可供解析")

    if on_progress:
        on_progress(100)

    return text
