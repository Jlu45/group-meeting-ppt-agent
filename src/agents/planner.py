import json
import logging
from typing import Optional

from src.models import (
    StructuredPresentation, SlidePlan, LayoutType, DocType, TemplateDNA,
)

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """你是组会PPT规划专家。根据以下信息，优化PPT大纲。

文档类型：{doc_type}
标题：{title}
概述：{summary}
当前大纲：
{current_outline}

模板信息：
- 主色：{primary_color}
- 标题字体：{title_font}
- 正文字体：{body_font}

请优化以下方面并输出JSON：
1. 页数是否合理（通常8-15页）
2. 布局选择是否最优
3. 图表规划是否合理
4. 内容密度是否均匀
5. 是否需要拆分或合并页面

输出格式：
{{
    "slides": [
        {{
            "title": "页面标题",
            "layout": "布局类型",
            "points": ["要点1", "要点2"],
            "chart_desc": "图表描述或null",
            "notes": "演讲者备注"
        }}
    ],
    "adjustments": ["调整说明1", "调整说明2"]
}}"""


class PlannerAgent:
    """规划智能体 - 页数规划、布局选择、图表决策"""

    def __init__(self, llm_client=None, model: str = "gpt-4o"):
        self._llm_client = llm_client
        self._model = model

    def plan(self, presentation: StructuredPresentation, template_dna: Optional[TemplateDNA] = None) -> StructuredPresentation:
        if self._llm_client is None:
            logger.info("No LLM client, using rule-based planning")
            return self._rule_based_plan(presentation, template_dna)

        try:
            result = self._llm_plan(presentation, template_dna)
            if result:
                return result
        except Exception as e:
            logger.error(f"LLM planning failed: {e}, falling back to rules")

        return self._rule_based_plan(presentation, template_dna)

    def _llm_plan(self, presentation: StructuredPresentation, template_dna: Optional[TemplateDNA]) -> Optional[StructuredPresentation]:
        current_outline = self._format_outline(presentation)
        theme = template_dna.theme if template_dna else None
        fonts = template_dna.fonts if template_dna else None

        prompt = PLANNER_PROMPT.format(
            doc_type=presentation.doc_type.value,
            title=presentation.title,
            summary=presentation.summary,
            current_outline=current_outline,
            primary_color=theme.primary if theme else "#1E3A5F",
            title_font=fonts.title if fonts else "Source Han Serif SC",
            body_font=fonts.body if fonts else "Source Han Sans SC",
        )

        response = self._llm_client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是组会PPT规划专家，只输出JSON格式。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        data = json.loads(response.choices[0].message.content)
        slides = []
        for raw in data.get("slides", []):
            layout = self._parse_layout(raw.get("layout", "bullet_list"))
            slides.append(SlidePlan(
                title=raw.get("title", ""),
                layout=layout,
                points=raw.get("points", []),
                chart_desc=raw.get("chart_desc"),
                notes=raw.get("notes", ""),
            ))

        if slides:
            presentation.slides = slides

        adjustments = data.get("adjustments", [])
        if adjustments:
            logger.info(f"Planner adjustments: {adjustments}")

        return presentation

    def _rule_based_plan(self, presentation: StructuredPresentation, template_dna: Optional[TemplateDNA]) -> StructuredPresentation:
        slides = presentation.slides

        for i, slide in enumerate(slides):
            if slide.layout == LayoutType.COVER:
                continue

            if slide.table_data and len(slide.table_data) > 3:
                slide.layout = LayoutType.TABLE
            elif slide.chart_desc:
                slide.layout = LayoutType.CHART
            elif len(slide.points) > 6:
                slide = self._split_slide(slide)
                slides[i] = slide
            elif len(slide.points) >= 4 and any(
                kw in slide.title for kw in ["对比", "比较", "vs", "VS", "优劣"]
            ):
                slide.layout = LayoutType.TWO_COLUMN

        if len(slides) > 15:
            slides = self._merge_thin_slides(slides)
        elif len(slides) < 5:
            slides = self._expand_thick_slides(slides)

        presentation.slides = slides
        return presentation

    def _split_slide(self, slide: SlidePlan) -> SlidePlan:
        if len(slide.points) <= 6:
            return slide
        slide.points = slide.points[:6]
        return slide

    def _merge_thin_slides(self, slides: list[SlidePlan]) -> list[SlidePlan]:
        merged = []
        skip = False
        for i, slide in enumerate(slides):
            if skip:
                skip = False
                continue
            if (
                slide.layout == LayoutType.BULLET_LIST
                and len(slide.points) <= 3
                and i + 1 < len(slides)
                and slides[i + 1].layout == LayoutType.BULLET_LIST
                and len(slides[i + 1].points) <= 3
            ):
                merged_slide = SlidePlan(
                    title=f"{slide.title} & {slides[i + 1].title}",
                    layout=LayoutType.TWO_COLUMN,
                    points=slide.points + slides[i + 1].points,
                    notes=slide.notes,
                )
                merged.append(merged_slide)
                skip = True
            else:
                merged.append(slide)
        return merged

    def _expand_thick_slides(self, slides: list[SlidePlan]) -> list[SlidePlan]:
        expanded = []
        for slide in slides:
            if slide.layout == LayoutType.BULLET_LIST and len(slide.points) > 4:
                half = len(slide.points) // 2
                expanded.append(SlidePlan(
                    title=slide.title + "（上）",
                    layout=LayoutType.BULLET_LIST,
                    points=slide.points[:half],
                    notes=slide.notes,
                ))
                expanded.append(SlidePlan(
                    title=slide.title + "（下）",
                    layout=LayoutType.BULLET_LIST,
                    points=slide.points[half:],
                    notes="",
                ))
            else:
                expanded.append(slide)
        return expanded

    def _format_outline(self, presentation: StructuredPresentation) -> str:
        lines = []
        for i, slide in enumerate(presentation.slides, 1):
            lines.append(f"第{i}页: {slide.title} [{slide.layout.value}]")
            for p in slide.points:
                lines.append(f"  - {p}")
            if slide.chart_desc:
                lines.append(f"  [图表: {slide.chart_desc}]")
        return "\n".join(lines)

    def _parse_layout(self, raw: str) -> LayoutType:
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
