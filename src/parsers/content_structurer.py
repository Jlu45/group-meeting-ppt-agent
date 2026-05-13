import json
import logging
from datetime import datetime
from typing import Optional

from src.models import (
    DocType, LayoutType, SlidePlan, StructuredPresentation, ParsedDocument,
)

logger = logging.getLogger(__name__)

CONTENT_LIMIT = 12000

STRUCTURING_PROMPT = """你是组会PPT内容规划专家。分析以下文档，输出JSON格式PPT大纲。

文档内容：
{content}

输出要求（严格JSON格式）：
{{
    "doc_type": "文档类型，从以下选择：progress_report/experiment_log/literature_note/tech_design/other",
    "title": "PPT标题",
    "summary": "一句话概述",
    "slides": [
        {{
            "title": "页面标题",
            "layout": "布局类型，从以下选择：cover/bullet_list/two_column/chart/table/image_grid/architecture/summary/discussion",
            "points": ["要点1", "要点2", "要点3"],
            "table_data": null,
            "chart_desc": "图表描述（如不需要图表则为null）",
            "notes": "演讲者备注"
        }}
    ]
}}

PPT结构（所有文档类型统一遵循）：
- 第1页: 封面（layout: cover）— 主题 + 汇报人 + 日期
- 第2页: 概述（layout: bullet_list）— 1页讲清楚核心内容
- 第3页起: 主体内容（按文档逻辑自动分页，通常3-8页）
- 倒数第2页: 总结（layout: summary）— 关键发现/进展/结论
- 最后1页: 讨论（layout: discussion）— 下一步计划/待解决问题

不同文档的内容映射：
- 进展报告(progress_report): 各模块进展→问题风险
- 实验记录(experiment_log): 方法→结果→分析
- 文献笔记(literature_note): 背景→方法→启发
- 技术方案(tech_design): 需求→设计→验证

要点规则：
- 每页3-6个要点
- 每个要点一句话，简洁有力
- 有数据时优先使用表格布局
- 有对比时使用双栏布局
- 有趋势/对比时使用图表布局"""


class ContentStructuringEngine:
    """文档类型无关的内容结构化 - Markdown → 统一PPT结构"""

    def __init__(self, llm_client=None, model: str = "gpt-4o"):
        self._llm_client = llm_client
        self._model = model

    def structure(self, parsed_doc: ParsedDocument, author: str = "", date: str = "") -> StructuredPresentation:
        content = parsed_doc.markdown_content[:CONTENT_LIMIT]

        if not content.strip():
            return self._build_fallback_structure(parsed_doc, author, date)

        try:
            response = self._call_llm(content)
            data = json.loads(response)
            return self._build_presentation(data, author, date)
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            return self._build_fallback_structure(parsed_doc, author, date)
        except Exception as e:
            logger.error(f"Content structuring failed: {e}")
            return self._build_fallback_structure(parsed_doc, author, date)

    def _call_llm(self, content: str) -> str:
        if self._llm_client is None:
            raise RuntimeError("LLM client not configured")

        prompt = STRUCTURING_PROMPT.format(content=content)
        response = self._llm_client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是一个专业的组会PPT内容规划专家，只输出JSON格式。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _build_presentation(self, data: dict, author: str, date: str) -> StructuredPresentation:
        doc_type = self._parse_doc_type(data.get("doc_type", "other"))
        title = data.get("title", "组会汇报")
        summary = data.get("summary", "")
        raw_slides = data.get("slides", [])

        slides = []
        for raw in raw_slides:
            layout = self._parse_layout_type(raw.get("layout", "bullet_list"))
            slides.append(SlidePlan(
                title=raw.get("title", ""),
                layout=layout,
                points=raw.get("points", []),
                table_data=raw.get("table_data"),
                chart_desc=raw.get("chart_desc"),
                notes=raw.get("notes", ""),
            ))

        slides = self._ensure_unified_structure(slides)

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        return StructuredPresentation(
            doc_type=doc_type,
            title=title,
            summary=summary,
            slides=slides,
            author=author,
            date=date,
        )

    def _ensure_unified_structure(self, slides: list[SlidePlan]) -> list[SlidePlan]:
        if not slides:
            slides = [
                SlidePlan(title="封面", layout=LayoutType.COVER, points=[]),
                SlidePlan(title="概述", layout=LayoutType.BULLET_LIST, points=["待补充"]),
                SlidePlan(title="总结", layout=LayoutType.SUMMARY, points=["待补充"]),
                SlidePlan(title="讨论与下一步", layout=LayoutType.DISCUSSION, points=["待补充"]),
            ]
            return slides

        if slides[0].layout != LayoutType.COVER:
            slides.insert(0, SlidePlan(title="封面", layout=LayoutType.COVER, points=[]))

        if len(slides) >= 2 and slides[1].layout == LayoutType.COVER:
            pass

        if len(slides) >= 3:
            second_last = slides[-2]
            if second_last.layout != LayoutType.SUMMARY and "总结" not in second_last.title:
                slides.insert(-1, SlidePlan(
                    title="总结", layout=LayoutType.SUMMARY, points=[]
                ))

            last = slides[-1]
            if last.layout != LayoutType.DISCUSSION and "讨论" not in last.title:
                slides.append(SlidePlan(
                    title="讨论与下一步", layout=LayoutType.DISCUSSION, points=[]
                ))

        return slides

    def _build_fallback_structure(self, parsed_doc: ParsedDocument, author: str, date: str) -> StructuredPresentation:
        content = parsed_doc.markdown_content
        lines = content.split("\n") if content else []
        title = "组会汇报"

        for line in lines[:20]:
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break

        chunks = self._split_content_to_chunks(content)
        slides = [SlidePlan(title=title, layout=LayoutType.COVER, points=[])]

        overview_points = [line.strip().lstrip("-*• ") for line in lines[:6] if line.strip() and not line.startswith("#")][:4]
        slides.append(SlidePlan(
            title="概述", layout=LayoutType.BULLET_LIST,
            points=overview_points or ["待补充"],
        ))

        for i, chunk in enumerate(chunks):
            chunk_title = f"内容 {i + 1}"
            chunk_lines = chunk.split("\n")
            for cl in chunk_lines:
                cl = cl.strip()
                if cl.startswith("## "):
                    chunk_title = cl[3:].strip()
                    break

            points = [l.strip().lstrip("-*• ") for l in chunk_lines if l.strip() and not l.startswith("#")][:5]
            slides.append(SlidePlan(
                title=chunk_title, layout=LayoutType.BULLET_LIST,
                points=points or ["待补充"],
            ))

        slides.append(SlidePlan(title="总结", layout=LayoutType.SUMMARY, points=["待补充"]))
        slides.append(SlidePlan(title="讨论与下一步", layout=LayoutType.DISCUSSION, points=["待补充"]))

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        return StructuredPresentation(
            doc_type=DocType.OTHER,
            title=title,
            summary="",
            slides=slides,
            author=author,
            date=date,
        )

    def _split_content_to_chunks(self, content: str, max_points: int = 5) -> list[str]:
        if not content:
            return []

        sections = []
        current = []
        for line in content.split("\n"):
            if line.startswith("## ") and current:
                sections.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append("\n".join(current))

        if len(sections) <= 1:
            paragraphs = [p for p in content.split("\n\n") if p.strip()]
            chunks = []
            chunk = []
            for p in paragraphs:
                chunk.append(p)
                if len(chunk) >= max_points:
                    chunks.append("\n\n".join(chunk))
                    chunk = []
            if chunk:
                chunks.append("\n\n".join(chunk))
            return chunks

        return sections

    def _parse_doc_type(self, raw: str) -> DocType:
        mapping = {
            "progress_report": DocType.PROGRESS_REPORT,
            "experiment_log": DocType.EXPERIMENT_LOG,
            "literature_note": DocType.LITERATURE_NOTE,
            "tech_design": DocType.TECH_DESIGN,
        }
        return mapping.get(raw, DocType.OTHER)

    def _parse_layout_type(self, raw: str) -> LayoutType:
        mapping = {
            "cover": LayoutType.COVER,
            "bullet_list": LayoutType.BULLET_LIST,
            "two_column": LayoutType.TWO_COLUMN,
            "chart": LayoutType.CHART,
            "table": LayoutType.TABLE,
            "image_grid": LayoutType.IMAGE_GRID,
            "architecture": LayoutType.ARCHITECTURE,
            "summary": LayoutType.SUMMARY,
            "discussion": LayoutType.DISCUSSION,
        }
        return mapping.get(raw, LayoutType.BULLET_LIST)
