import os
import logging
from pathlib import Path
from typing import Optional

from src.models import ParsedDocument

logger = logging.getLogger(__name__)

PDF_SIZE_THRESHOLD = 5 * 1024 * 1024
TABLE_MARKER_THRESHOLD = 5


class UniversalDocumentParser:
    """通用文档解析器 - 任意格式 → Markdown"""

    def __init__(self, use_docling: bool = False):
        self._markitdown = None
        self._docling_converter = None
        self._use_docling = use_docling

    @property
    def markitdown(self):
        if self._markitdown is None:
            from markitdown import MarkItDown
            self._markitdown = MarkItDown(enable_plugins=True)
        return self._markitdown

    @property
    def docling_converter(self):
        if self._docling_converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._docling_converter = DocumentConverter()
            except ImportError:
                logger.warning("Docling not installed. Complex PDF parsing unavailable.")
                return None
        return self._docling_converter

    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        file_type = ext.lstrip(".")

        if ext == ".pdf":
            content = self._parse_pdf(file_path)
        elif ext in (".docx", ".xlsx", ".pptx"):
            content = self._parse_with_markitdown(file_path)
        elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
            content = self._parse_image(file_path)
        elif ext in (".md", ".markdown"):
            content = path.read_text(encoding="utf-8")
        elif ext in (".txt", ".csv", ".json", ".yaml", ".yml"):
            content = path.read_text(encoding="utf-8")
        elif ext in (".html", ".htm"):
            content = self._parse_with_markitdown(file_path)
        else:
            content = self._parse_with_markitdown(file_path)

        logger.info(f"Parsed {file_path} -> {len(content)} chars")
        return ParsedDocument(
            source_path=str(path.resolve()),
            markdown_content=content,
            file_type=file_type,
        )

    def parse_multiple(self, file_paths: list[str]) -> list[ParsedDocument]:
        results = []
        for fp in file_paths:
            try:
                results.append(self.parse(fp))
            except Exception as e:
                logger.error(f"Failed to parse {fp}: {e}")
        return results

    def merge_documents(self, documents: list[ParsedDocument]) -> ParsedDocument:
        if not documents:
            return ParsedDocument(source_path="", markdown_content="")

        merged_content = "\n\n---\n\n".join(
            f"## Source: {Path(doc.source_path).name}\n\n{doc.markdown_content}"
            for doc in documents
        )
        return ParsedDocument(
            source_path=";".join(d.source_path for d in documents),
            markdown_content=merged_content,
            file_type="merged",
        )

    def _parse_pdf(self, path: str) -> str:
        if self._should_use_docling(path):
            return self._parse_with_docling(path)
        return self._parse_with_markitdown(path)

    def _should_use_docling(self, path: str) -> bool:
        if self._use_docling:
            return True
        if os.path.getsize(path) > PDF_SIZE_THRESHOLD:
            logger.info("Large PDF detected, using Docling")
            return True
        try:
            preview = self._parse_with_markitdown(path)
            if preview.count("|---|") > TABLE_MARKER_THRESHOLD:
                logger.info("Table-heavy PDF detected, using Docling")
                return True
        except Exception:
            pass
        return False

    def _parse_with_markitdown(self, path: str) -> str:
        result = self.markitdown.convert(path)
        return result.text_content if result else ""

    def _parse_with_docling(self, path: str) -> str:
        converter = self.docling_converter
        if converter is None:
            logger.warning("Docling unavailable, falling back to MarkItDown")
            return self._parse_with_markitdown(path)
        result = converter.convert(path)
        return result.document.export_to_markdown()

    def _parse_image(self, path: str) -> str:
        try:
            result = self.markitdown.convert(path)
            if result and result.text_content.strip():
                return result.text_content
        except Exception:
            pass

        try:
            from PIL import Image
            img = Image.open(path)
            return f"![{Path(path).stem}]({path})\n\nImage: {Path(path).name}, Size: {img.size[0]}x{img.size[1]}"
        except Exception as e:
            return f"[Image: {Path(path).name}] (Error: {e})"
