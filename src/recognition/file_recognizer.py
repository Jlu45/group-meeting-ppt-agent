import re
import uuid
from pathlib import Path
from typing import Optional

from src.common.models import FileRecognitionResult


class SmartFileRecognizer:
    EXTENSION_MAP: dict[str, str] = {
        ".docx": "document", ".doc": "document", ".pdf": "document",
        ".md": "markdown", ".markdown": "markdown", ".txt": "text",
        ".tex": "latex", ".html": "html", ".htm": "html",
        ".xlsx": "spreadsheet", ".xls": "spreadsheet",
        ".csv": "csv", ".tsv": "tsv",
        ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".pkl": "pickle", ".h5": "hdf5", ".hdf5": "hdf5",
        ".npy": "numpy", ".npz": "numpy_archive",
        ".py": "python", ".ipynb": "jupyter",
        ".R": "r_script", ".r": "r_script",
        ".m": "matlab", ".mlx": "matlab_live",
        ".sh": "shell", ".bash": "shell",
        ".do": "stata", ".sas": "sas", ".jl": "julia",
        ".png": "image", ".jpg": "image", ".jpeg": "image",
        ".bmp": "image", ".gif": "image", ".svg": "svg",
        ".tif": "image", ".tiff": "image", ".webp": "image",
        ".drawio": "diagram", ".vsdx": "visio",
        ".bib": "bibtex", ".ris": "ris", ".enw": "endnote", ".nbib": "pubmed",
        ".pptx": "presentation", ".ppt": "presentation",
    }

    NAMING_PATTERNS: dict[str, str] = {
        r"实验记录|lab[_-]?note|experiment[_-]?log|exp[_-]?\d+": "experiment_log",
        r"实验方案|protocol|experimental[_-]?design|实验设计": "experiment_protocol",
        r"周报|weekly|week[_-]?\d+|w\d{1,2}": "weekly_report",
        r"月报|monthly|month[_-]?\d+": "monthly_report",
        r"组会|group[_-]?meeting|meeting[_-]?\d+": "group_meeting",
        r"文献笔记|literature[_-]?note|reading[_-]?note|paper[_-]?note": "literature_note",
        r"文献综述|review|survey": "literature_review",
        r"设计方案|design[_-]?doc|technical[_-]?design": "tech_design",
        r"架构|architecture|system[_-]?design": "system_architecture",
        r"数据分析|data[_-]?analysis|analysis[_-]?result": "data_analysis",
        r"结果|results?|outcome": "results",
        r"清洗|clean|preprocess|预处理": "data_preprocessing",
        r"训练|train|training|fit": "model_training",
        r"评估|eval|evaluation|validate|test": "model_evaluation",
        r"画图|plot|figure|visualization|viz": "plotting",
        r"原始|raw|original": "raw_data",
        r"处理|processed|cleaned": "processed_data",
        r"fig[_-]?\d+|figure[_-]?\d+|图\d+": "figure",
        r"table[_-]?\d+|tab[_-]?\d+|表\d+": "table",
        r"final|最终版|定稿": "final_version",
        r"draft|草稿|初稿|wip": "draft_version",
        r"^(\d{2,3})[_-]": "numbered_sequence",
    }

    PURPOSE_MAP: dict[str, str] = {
        "experiment_log": "method_and_result",
        "experiment_protocol": "methodology",
        "weekly_report": "progress",
        "monthly_report": "progress",
        "group_meeting": "progress",
        "literature_note": "background_and_related_work",
        "literature_review": "background_and_related_work",
        "tech_design": "methodology_or_architecture",
        "system_architecture": "architecture",
        "data_analysis": "results",
        "results": "results",
        "data_preprocessing": "methodology",
        "model_training": "methodology",
        "model_evaluation": "results",
        "plotting": "result_visual",
        "raw_data": "data_source",
        "processed_data": "data_source",
        "figure": "result_visual",
        "table": "result_table",
        "final_version": "primary",
        "draft_version": "draft",
        "numbered_sequence": "sequential",
    }

    _PARSER_MAP: dict[str, str] = {
        "document": "UniversalDocumentParser",
        "markdown": "UniversalDocumentParser",
        "text": "UniversalDocumentParser",
        "spreadsheet": "UniversalDocumentParser",
        "csv": "UniversalDocumentParser",
        "python": "UniversalDocumentParser",
        "jupyter": "UniversalDocumentParser",
        "image": "UniversalDocumentParser",
        "bibtex": "UniversalDocumentParser",
        "latex": "UniversalDocumentParser",
        "html": "UniversalDocumentParser",
        "json": "UniversalDocumentParser",
        "yaml": "UniversalDocumentParser",
        "presentation": "UniversalDocumentParser",
    }

    _SLIDE_TYPE_MAP: dict[str, list[str]] = {
        "method_and_result": ["method", "result", "discussion"],
        "methodology": ["method", "architecture"],
        "progress": ["progress", "timeline", "next_step"],
        "background_and_related_work": ["background", "related_work", "literature"],
        "methodology_or_architecture": ["method", "architecture"],
        "architecture": ["architecture", "system_design"],
        "results": ["result", "comparison", "highlight"],
        "result_visual": ["result", "figure", "highlight"],
        "result_table": ["result", "table", "comparison"],
        "data_source": ["data", "appendix"],
        "primary": ["cover", "summary", "conclusion"],
        "draft": ["draft", "wip"],
        "sequential": ["progress", "timeline"],
    }

    _DATE_RE = re.compile(
        r"(?P<date>(?:\d{4})[_-]?(?:0[1-9]|1[0-2])[_-]?(?:0[1-9]|[12]\d|3[01]))"
    )
    _VERSION_RE = re.compile(r"[vV](?P<version>\d+(?:\.\d+)*)")
    _SEQUENCE_RE = re.compile(r"^(?P<seq>\d{1,3})[_-]")

    def recognize(self, file_paths: list[str]) -> list[FileRecognitionResult]:
        results: list[FileRecognitionResult] = []
        for fp in file_paths:
            path = Path(fp)
            filename = path.name
            ext = path.suffix.lower()

            base_type = self.EXTENSION_MAP.get(ext, "unknown")
            content_type, naming_conf = self._match_naming_pattern(filename)
            ppt_purpose = self.PURPOSE_MAP.get(content_type, "general")

            metadata = self._extract_metadata(filename)

            if content_type:
                confidence = 0.6 + naming_conf * 0.3
            elif base_type != "unknown":
                confidence = 0.5
            else:
                confidence = 0.2

            if metadata.get("date"):
                confidence = min(confidence + 0.05, 1.0)
            if metadata.get("version"):
                confidence = min(confidence + 0.05, 1.0)

            suggested_parser = self._PARSER_MAP.get(base_type, "UniversalDocumentParser")
            suggested_slide_types = self._SLIDE_TYPE_MAP.get(ppt_purpose, ["general"])

            result = FileRecognitionResult(
                id=f"frec-{uuid.uuid4().hex[:8]}",
                path=str(path.resolve()),
                filename=filename,
                extension=ext,
                base_type=base_type,
                content_type=content_type,
                ppt_purpose=ppt_purpose,
                confidence=round(confidence, 2),
                sequence_number=metadata.get("sequence"),
                date=metadata.get("date"),
                version=metadata.get("version"),
                suggested_parser=suggested_parser,
                suggested_slide_types=suggested_slide_types,
            )
            results.append(result)

        return results

    def _match_naming_pattern(self, filename: str) -> tuple[str, float]:
        stem = Path(filename).stem
        best_type = ""
        best_conf = 0.0

        for pattern, content_type in self.NAMING_PATTERNS.items():
            try:
                match = re.search(pattern, stem, re.IGNORECASE)
                if match:
                    conf = min(1.0, len(match.group(0)) / max(len(stem), 1) + 0.5)
                    if conf > best_conf:
                        best_conf = conf
                        best_type = content_type
            except re.error:
                continue

        return best_type, best_conf

    def _extract_metadata(self, filename: str) -> dict:
        metadata: dict = {}

        date_match = self._DATE_RE.search(filename)
        if date_match:
            raw = date_match.group("date")
            normalized = raw.replace("_", "-")
            if len(normalized) == 8 and "-" not in normalized:
                normalized = f"{normalized[:4]}-{normalized[4:6]}-{normalized[6:8]}"
            metadata["date"] = normalized

        version_match = self._VERSION_RE.search(filename)
        if version_match:
            metadata["version"] = version_match.group("version")

        seq_match = self._SEQUENCE_RE.search(filename)
        if seq_match:
            metadata["sequence"] = int(seq_match.group("seq"))

        return metadata
