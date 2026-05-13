import json
import logging
from typing import Optional

from src.models import (
    StructuredPresentation, SlidePlan, LayoutType, TemplateDNA,
)

logger = logging.getLogger(__name__)

GENERATOR_PROMPT = """你是组会PPT内容生成专家。根据以下幻灯片规划，生成精炼的PPT内容。

页面标题：{title}
布局类型：{layout}
当前要点：{points}
文档类型：{doc_type}
文档概述：{summary}

请优化以下内容并输出JSON：
1. 每个要点精炼为一句完整的话（不超过30字）
2. 确保要点之间逻辑连贯
3. 优先使用具体数据/结论，避免模糊描述
4. 如有图表需求，描述图表内容

输出格式：
{{
    "title": "优化后的标题",
    "points": ["要点1", "要点2", "要点3"],
    "chart_desc": "图表描述或null",
    "notes": "演讲者备注（1-2句话）"
}}"""


class GeneratorAgent:
    """生成智能体 - 文本生成、图表生成、幻灯片组装"""

    def __init__(self, llm_client=None, model: str = "gpt-4o"):
        self._llm_client = llm_client
        self._model = model

    def generate(self, presentation: StructuredPresentation, template_dna: Optional[TemplateDNA] = None) -> StructuredPresentation:
        enhanced_slides = []
        for slide in presentation.slides:
            enhanced = self._enhance_slide(slide, presentation)
            enhanced_slides.append(enhanced)

        presentation.slides = enhanced_slides
        return presentation

    def _enhance_slide(self, slide: SlidePlan, presentation: StructuredPresentation) -> SlidePlan:
        if slide.layout == LayoutType.COVER:
            return self._enhance_cover(slide, presentation)

        if self._llm_client is None:
            return slide

        try:
            result = self._llm_enhance(slide, presentation)
            if result:
                return result
        except Exception as e:
            logger.warning(f"LLM enhancement failed for slide '{slide.title}': {e}")

        return slide

    def _llm_enhance(self, slide: SlidePlan, presentation: StructuredPresentation) -> Optional[SlidePlan]:
        prompt = GENERATOR_PROMPT.format(
            title=slide.title,
            layout=slide.layout.value,
            points=json.dumps(slide.points, ensure_ascii=False),
            doc_type=presentation.doc_type.value,
            summary=presentation.summary,
        )

        response = self._llm_client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是组会PPT内容生成专家，只输出JSON格式。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        data = json.loads(response.choices[0].message.content)
        return SlidePlan(
            title=data.get("title", slide.title),
            layout=slide.layout,
            points=data.get("points", slide.points),
            table_data=slide.table_data,
            chart_desc=data.get("chart_desc", slide.chart_desc),
            image_paths=slide.image_paths,
            notes=data.get("notes", slide.notes),
        )

    def _enhance_cover(self, slide: SlidePlan, presentation: StructuredPresentation) -> SlidePlan:
        if not slide.title or slide.title == "封面":
            slide.title = presentation.title
        if not slide.points:
            slide.points = []
        return slide
