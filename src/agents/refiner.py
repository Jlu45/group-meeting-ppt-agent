import json
import logging
from typing import Optional

from src.models import (
    StructuredPresentation, SlidePlan, LayoutType, TemplateDNA,
)

logger = logging.getLogger(__name__)

REFINER_PROMPT = """你是组会PPT内容优化专家。检查并优化以下PPT内容。

PPT标题：{title}
文档类型：{doc_type}

当前所有幻灯片：
{all_slides}

请检查以下方面并输出JSON：
1. 要点是否冗余或重复（精简到3-6个）
2. 表达是否简洁有力（每点不超过30字）
3. 各页风格是否统一
4. 逻辑是否连贯
5. 是否有占位符文本未替换

输出格式：
{{
    "refined_slides": [
        {{
            "index": 0,
            "title": "优化后标题",
            "points": ["要点1", "要点2"],
            "notes": "演讲者备注"
        }}
    ],
    "issues_found": ["发现的问题1", "发现的问题2"],
    "improvements": ["改进说明1", "改进说明2"]
}}"""


class RefinerAgent:
    """优化智能体 - 质量检查、表达优化、风格统一"""

    def __init__(self, llm_client=None, model: str = "gpt-4o"):
        self._llm_client = llm_client
        self._model = model

    def refine(self, presentation: StructuredPresentation, template_dna: Optional[TemplateDNA] = None) -> StructuredPresentation:
        presentation = self._rule_based_refine(presentation)

        if self._llm_client:
            try:
                result = self._llm_refine(presentation)
                if result:
                    presentation = result
            except Exception as e:
                logger.warning(f"LLM refinement failed: {e}")

        return presentation

    def _rule_based_refine(self, presentation: StructuredPresentation) -> StructuredPresentation:
        seen_titles = set()
        for i, slide in enumerate(presentation.slides):
            if slide.title in seen_titles and slide.layout != LayoutType.COVER:
                slide.title = f"{slide.title}（续）"
            seen_titles.add(slide.title)

            refined_points = []
            for p in slide.points:
                p = p.strip()
                if not p:
                    continue
                if len(p) > 60:
                    p = p[:57] + "..."
                refined_points.append(p)
            slide.points = refined_points

            if len(slide.points) > 6:
                slide.points = slide.points[:6]
                logger.info(f"Slide '{slide.title}' points trimmed to 6")

            placeholder_patterns = ["待补充", "TODO", "TBD", "placeholder", "xxx"]
            for j, p in enumerate(slide.points):
                if any(ph in p.lower() for ph in [x.lower() for x in placeholder_patterns]):
                    logger.warning(f"Slide '{slide.title}' point {j} contains placeholder: {p}")

            if not slide.notes and slide.layout != LayoutType.COVER:
                slide.notes = self._generate_default_notes(slide)

        return presentation

    def _llm_refine(self, presentation: StructuredPresentation) -> Optional[StructuredPresentation]:
        all_slides = self._format_all_slides(presentation)

        prompt = REFINER_PROMPT.format(
            title=presentation.title,
            doc_type=presentation.doc_type.value,
            all_slides=all_slides,
        )

        response = self._llm_client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是组会PPT内容优化专家，只输出JSON格式。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        data = json.loads(response.choices[0].message.content)
        refined = data.get("refined_slides", [])

        for item in refined:
            idx = item.get("index", -1)
            if 0 <= idx < len(presentation.slides):
                slide = presentation.slides[idx]
                if "title" in item:
                    slide.title = item["title"]
                if "points" in item:
                    slide.points = item["points"]
                if "notes" in item:
                    slide.notes = item["notes"]

        issues = data.get("issues_found", [])
        improvements = data.get("improvements", [])
        if issues:
            logger.info(f"Refiner issues: {issues}")
        if improvements:
            logger.info(f"Refiner improvements: {improvements}")

        return presentation

    def _generate_default_notes(self, slide: SlidePlan) -> str:
        if slide.layout == LayoutType.SUMMARY:
            return "总结本页核心结论"
        elif slide.layout == LayoutType.DISCUSSION:
            return "引导讨论下一步方向"
        elif slide.layout == LayoutType.TABLE:
            return "重点解读表格中的关键数据"
        elif slide.layout == LayoutType.CHART:
            return "解读图表趋势和关键数据点"
        else:
            return f"展开讲解{slide.title}相关内容"

    def _format_all_slides(self, presentation: StructuredPresentation) -> str:
        lines = []
        for i, slide in enumerate(presentation.slides):
            lines.append(f"第{i + 1}页: {slide.title} [{slide.layout.value}]")
            for p in slide.points:
                lines.append(f"  - {p}")
            if slide.notes:
                lines.append(f"  备注: {slide.notes}")
        return "\n".join(lines)
