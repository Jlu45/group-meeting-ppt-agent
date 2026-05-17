import re
import uuid
from typing import List, Optional

from src.common.models import (
    AssetStore,
    ContentUnit,
    Evidence,
    FigureAsset,
    FileRecognitionResult,
    MetricAsset,
    SourceFile,
    TableAsset,
)


_KIND_KEYWORDS: dict[str, list[str]] = {
    "method": ["方法", "实验", "method", "experiment", "methodology", "approach", "方案", "设计"],
    "result": ["实验结果", "实验效果", "实验性能", "结果", "result", "性能", "performance", "outcome", "效果", "评估", "evaluation"],
    "background": ["背景", "background", "相关", "related", "相关工作", "related work", "引言", "introduction"],
    "limitation": ["限制", "limitation", "问题", "problem", "不足", "挑战", "challenge", "缺陷"],
    "next_step": ["下一步", "next", "计划", "plan", "未来", "future", "展望", "outlook"],
    "claim": ["结论", "conclusion", "贡献", "contribution", "总结", "summary", "发现", "finding"],
}

_TABLE_ROW_RE = re.compile(r"^\|[-:| ]+\|$")
_TABLE_SEP_RE = re.compile(r"^\|[-:| ]+\|$")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_METRIC_RE = re.compile(
    r"(?P<name>[^\s:：]*?)\s*[:：]?\s*"
    r"(?P<value>\d+\.?\d*)\s*"
    r"(?P<unit>%|pp|dB|ms|s|sec|GB|MB|KB|TB|fps|Hz|MHz|GHz|F1|ACC|Acc|精度|准确率|召回率)?"
)
_PERCENT_RE = re.compile(r"(?P<value>\d+\.?\d*)\s*%")
_SIMPLE_NUM_RE = re.compile(r"(?P<value>\d+\.\d{2,})")


def _infer_kind(title: str) -> str:
    lower = title.lower()
    best_kind = "claim"
    best_score = 0
    for kind, keywords in _KIND_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in lower:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_kind = kind
    return best_kind


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    parts = re.split(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)
    sections: list[tuple[str, str]] = []
    if not parts:
        return sections
    if parts[0].strip():
        sections.append(("", parts[0]))
    i = 1
    while i + 1 < len(parts):
        sections.append((parts[i].strip(), parts[i + 1]))
        i += 2
    return sections


def _extract_tables(text: str, source_file_id: str) -> list[TableAsset]:
    tables: list[TableAsset] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if _TABLE_SEP_RE.match(next_line):
                header_line = line
                columns = [c.strip() for c in header_line.strip("|").split("|") if c.strip()]
                row_count = 0
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    row_count += 1
                    j += 1
                table_id = f"tbl-{uuid.uuid4().hex[:8]}"
                tables.append(TableAsset(
                    id=table_id,
                    source_file_id=source_file_id,
                    title="",
                    dataframe_ref="",
                    columns=columns,
                    row_count=row_count,
                    summary="",
                    suggested_use="table_slide",
                ))
                i = j
                continue
        i += 1
    return tables


def _extract_figures(text: str, source_file_id: str) -> list[FigureAsset]:
    figures: list[FigureAsset] = []
    for match in _IMAGE_RE.finditer(text):
        alt = match.group(1)
        path = match.group(2)
        fig_id = f"fig-{uuid.uuid4().hex[:8]}"
        figures.append(FigureAsset(
            id=fig_id,
            source_file_id=source_file_id,
            path=path,
            title=alt,
            caption=alt,
            image_type="result_plot",
            suggested_use="result_visual",
        ))
    return figures


def _extract_metrics(text: str, evidence_id: str) -> list[MetricAsset]:
    metrics: list[MetricAsset] = []
    seen: set[str] = set()
    for match in _PERCENT_RE.finditer(text):
        val = match.group("value")
        key = f"{val}%"
        if key not in seen:
            seen.add(key)
            metric_id = f"met-{uuid.uuid4().hex[:8]}"
            metrics.append(MetricAsset(
                id=metric_id,
                name="",
                value=float(val),
                unit="%",
                baseline=None,
                delta=None,
                evidence_ids=[evidence_id] if evidence_id else [],
            ))
    for match in _METRIC_RE.finditer(text):
        name = match.group("name").strip()
        value = match.group("value")
        unit = match.group("unit") or ""
        key = f"{name}:{value}{unit}"
        if key not in seen and name:
            seen.add(key)
            metric_id = f"met-{uuid.uuid4().hex[:8]}"
            metrics.append(MetricAsset(
                id=metric_id,
                name=name,
                value=float(value),
                unit=unit if unit else None,
                baseline=None,
                delta=None,
                evidence_ids=[evidence_id] if evidence_id else [],
            ))
    for match in _SIMPLE_NUM_RE.finditer(text):
        value = match.group("value")
        key = f"num:{value}"
        if key not in seen:
            seen.add(key)
            metric_id = f"met-{uuid.uuid4().hex[:8]}"
            metrics.append(MetricAsset(
                id=metric_id,
                name="",
                value=float(value),
                unit=None,
                baseline=None,
                delta=None,
                evidence_ids=[evidence_id] if evidence_id else [],
            ))
    return metrics


class AssetBuilder:
    def build_from_parsed(self, file_recognition: FileRecognitionResult, markdown_content: str) -> AssetStore:
        store = AssetStore()

        source_id = file_recognition.id or f"src-{uuid.uuid4().hex[:8]}"
        source = SourceFile(
            id=source_id,
            path=file_recognition.path,
            filename=file_recognition.filename,
            extension=file_recognition.extension,
            base_type=file_recognition.base_type,
            content_type=file_recognition.content_type,
            sequence=file_recognition.sequence_number,
            metadata={
                "ppt_purpose": file_recognition.ppt_purpose,
                "confidence": file_recognition.confidence,
                "date": file_recognition.date,
                "version": file_recognition.version,
            },
        )
        store.source_files[source_id] = source

        sections = _split_sections(markdown_content)

        for idx, (title, body) in enumerate(sections):
            kind = _infer_kind(title) if title else "claim"
            unit_id = f"cu-{uuid.uuid4().hex[:8]}"
            evidence_id = f"ev-{uuid.uuid4().hex[:8]}"

            body_stripped = body.strip()
            summary = body_stripped[:200] if body_stripped else ""
            details = [line.strip() for line in body_stripped.split("\n") if line.strip()] if body_stripped else []

            evidence = Evidence(
                id=evidence_id,
                source_file_id=source_id,
                location=f"section:{idx}",
                quote=summary[:100],
                confidence=file_recognition.confidence,
            )
            store.evidences[evidence_id] = evidence

            unit = ContentUnit(
                id=unit_id,
                kind=kind,
                title=title,
                summary=summary,
                details=details,
                evidence_ids=[evidence_id],
                priority=max(1, 5 - idx) if idx < 5 else 1,
                tags=[kind],
            )
            store.content_units[unit_id] = unit

            for table in _extract_tables(body, source_id):
                table.title = title
                store.tables[table.id] = table

            for figure in _extract_figures(body, source_id):
                store.figures[figure.id] = figure

            for metric in _extract_metrics(body, evidence_id):
                store.metrics[metric.id] = metric

        if not sections and markdown_content.strip():
            unit_id = f"cu-{uuid.uuid4().hex[:8]}"
            evidence_id = f"ev-{uuid.uuid4().hex[:8]}"
            body_stripped = markdown_content.strip()
            summary = body_stripped[:200]

            evidence = Evidence(
                id=evidence_id,
                source_file_id=source_id,
                location="full_document",
                quote=summary[:100],
                confidence=file_recognition.confidence,
            )
            store.evidences[evidence_id] = evidence

            unit = ContentUnit(
                id=unit_id,
                kind="claim",
                title=file_recognition.filename,
                summary=summary,
                details=[line.strip() for line in body_stripped.split("\n") if line.strip()],
                evidence_ids=[evidence_id],
                priority=3,
                tags=["claim"],
            )
            store.content_units[unit_id] = unit

            for table in _extract_tables(markdown_content, source_id):
                store.tables[table.id] = table
            for figure in _extract_figures(markdown_content, source_id):
                store.figures[figure.id] = figure
            for metric in _extract_metrics(markdown_content, evidence_id):
                store.metrics[metric.id] = metric

        return store

    def merge_stores(self, stores: list[AssetStore]) -> AssetStore:
        merged = AssetStore()
        for store in stores:
            merged.source_files.update(store.source_files)
            merged.evidences.update(store.evidences)
            merged.content_units.update(store.content_units)
            merged.tables.update(store.tables)
            merged.figures.update(store.figures)
            merged.code.update(store.code)
            merged.metrics.update(store.metrics)
        return merged
