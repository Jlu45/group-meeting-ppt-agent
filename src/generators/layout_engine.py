import logging
from dataclasses import dataclass
from typing import Optional

from pptx.util import Inches, Pt, Emu

from src.models import LayoutType, TemplateDNA, SlidePlan

logger = logging.getLogger(__name__)

SLIDE_W = 12192000
SLIDE_H = 6858000
MARGIN = 914400


@dataclass
class LayoutRegion:
    x: int
    y: int
    cx: int
    cy: int


class LayoutEngine:
    """布局引擎 - 计算各元素在幻灯片上的精确位置"""

    def __init__(self, template_dna: Optional[TemplateDNA] = None):
        self._template_dna = template_dna or TemplateDNA()
        self._slide_w = self._template_dna.slide_width or SLIDE_W
        self._slide_h = self._template_dna.slide_height or SLIDE_H

    def calculate_layout(self, slide_plan: SlidePlan) -> dict:
        layout_map = {
            LayoutType.COVER: self._cover_layout,
            LayoutType.BULLET_LIST: self._bullet_layout,
            LayoutType.TWO_COLUMN: self._two_column_layout,
            LayoutType.CHART: self._chart_layout,
            LayoutType.TABLE: self._table_layout,
            LayoutType.IMAGE_GRID: self._image_grid_layout,
            LayoutType.SUMMARY: self._summary_layout,
            LayoutType.DISCUSSION: self._discussion_layout,
            LayoutType.ARCHITECTURE: self._architecture_layout,
        }

        calculator = layout_map.get(slide_plan.layout, self._bullet_layout)
        return calculator(slide_plan)

    def _cover_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h

        return {
            "type": "cover",
            "title": LayoutRegion(
                x=MARGIN * 2,
                y=int(cy * 0.33),
                cx=cx - MARGIN * 4,
                cy=int(cy * 0.2),
            ),
            "subtitle": LayoutRegion(
                x=MARGIN * 2,
                y=int(cy * 0.57),
                cx=cx - MARGIN * 4,
                cy=int(cy * 0.08),
            ),
            "author": LayoutRegion(
                x=MARGIN * 2,
                y=int(cy * 0.68),
                cx=cx - MARGIN * 4,
                cy=int(cy * 0.06),
            ),
            "date": LayoutRegion(
                x=MARGIN * 2,
                y=int(cy * 0.78),
                cx=cx - MARGIN * 4,
                cy=int(cy * 0.05),
            ),
            "accent_line": LayoutRegion(
                x=int(cx * 0.3),
                y=int(cy * 0.55),
                cx=int(cx * 0.4),
                cy=int(cy * 0.005),
            ),
        }

    def _bullet_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h
        title_h = int(cy * 0.14)
        content_top = title_h + MARGIN

        return {
            "type": "bullet_list",
            "title_bar": LayoutRegion(x=0, y=0, cx=cx, cy=title_h),
            "title_text": LayoutRegion(
                x=MARGIN, y=int(title_h * 0.15),
                cx=cx - MARGIN * 2, cy=int(title_h * 0.7),
            ),
            "content": LayoutRegion(
                x=MARGIN, y=content_top,
                cx=cx - MARGIN * 2, cy=cy - content_top - MARGIN,
            ),
        }

    def _two_column_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h
        title_h = int(cy * 0.14)
        content_top = title_h + MARGIN
        content_h = cy - content_top - MARGIN
        col_w = (cx - MARGIN * 3) // 2

        return {
            "type": "two_column",
            "title_bar": LayoutRegion(x=0, y=0, cx=cx, cy=title_h),
            "title_text": LayoutRegion(
                x=MARGIN, y=int(title_h * 0.15),
                cx=cx - MARGIN * 2, cy=int(title_h * 0.7),
            ),
            "left_column": LayoutRegion(
                x=MARGIN, y=content_top,
                cx=col_w, cy=content_h,
            ),
            "divider": LayoutRegion(
                x=MARGIN + col_w + MARGIN // 2, y=content_top + MARGIN // 2,
                cx=int(cx * 0.002), cy=content_h - MARGIN,
            ),
            "right_column": LayoutRegion(
                x=MARGIN * 2 + col_w, y=content_top,
                cx=col_w, cy=content_h,
            ),
        }

    def _chart_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h
        title_h = int(cy * 0.14)
        content_top = title_h + MARGIN

        return {
            "type": "chart",
            "title_bar": LayoutRegion(x=0, y=0, cx=cx, cy=title_h),
            "title_text": LayoutRegion(
                x=MARGIN, y=int(title_h * 0.15),
                cx=cx - MARGIN * 2, cy=int(title_h * 0.7),
            ),
            "chart_area": LayoutRegion(
                x=MARGIN, y=content_top,
                cx=cx - MARGIN * 2, cy=int((cy - content_top - MARGIN) * 0.8),
            ),
            "caption": LayoutRegion(
                x=MARGIN, y=int(cy * 0.85),
                cx=cx - MARGIN * 2, cy=int(cy * 0.1),
            ),
        }

    def _table_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h
        title_h = int(cy * 0.14)
        content_top = title_h + MARGIN

        return {
            "type": "table",
            "title_bar": LayoutRegion(x=0, y=0, cx=cx, cy=title_h),
            "title_text": LayoutRegion(
                x=MARGIN, y=int(title_h * 0.15),
                cx=cx - MARGIN * 2, cy=int(title_h * 0.7),
            ),
            "table_area": LayoutRegion(
                x=MARGIN, y=content_top,
                cx=cx - MARGIN * 2, cy=cy - content_top - MARGIN,
            ),
        }

    def _image_grid_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h
        title_h = int(cy * 0.14)
        content_top = title_h + MARGIN
        content_h = cy - content_top - MARGIN

        num_images = max(len(plan.image_paths), 1)
        if num_images <= 2:
            cols, rows = 2, 1
        elif num_images <= 4:
            cols, rows = 2, 2
        elif num_images <= 6:
            cols, rows = 3, 2
        else:
            cols, rows = 4, 2

        gap = MARGIN // 2
        cell_w = (cx - MARGIN * 2 - gap * (cols - 1)) // cols
        cell_h = (content_h - gap * (rows - 1)) // rows

        cells = []
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if idx < num_images:
                    cells.append(LayoutRegion(
                        x=MARGIN + c * (cell_w + gap),
                        y=content_top + r * (cell_h + gap),
                        cx=cell_w, cy=cell_h,
                    ))

        return {
            "type": "image_grid",
            "title_bar": LayoutRegion(x=0, y=0, cx=cx, cy=title_h),
            "title_text": LayoutRegion(
                x=MARGIN, y=int(title_h * 0.15),
                cx=cx - MARGIN * 2, cy=int(title_h * 0.7),
            ),
            "cells": cells,
        }

    def _summary_layout(self, plan: SlidePlan) -> dict:
        cx = self._slide_w
        cy = self._slide_h

        return {
            "type": "summary",
            "title": LayoutRegion(
                x=MARGIN, y=int(cy * 0.06),
                cx=cx - MARGIN * 2, cy=int(cy * 0.1),
            ),
            "accent_line": LayoutRegion(
                x=int(cx * 0.35), y=int(cy * 0.18),
                cx=int(cx * 0.3), cy=int(cy * 0.005),
            ),
            "content": LayoutRegion(
                x=MARGIN * 2, y=int(cy * 0.24),
                cx=cx - MARGIN * 4, cy=int(cy * 0.68),
            ),
        }

    def _discussion_layout(self, plan: SlidePlan) -> dict:
        return self._summary_layout(plan)

    def _architecture_layout(self, plan: SlidePlan) -> dict:
        return self._chart_layout(plan)

    def estimate_text_overflow(self, text: str, region: LayoutRegion, font_size_pt: int = 18) -> bool:
        chars_per_line = max(1, region.cx // (font_size_pt * 12700))
        num_lines = len(text) // chars_per_line + 1
        line_height = int(font_size_pt * 12700 * 1.5)
        total_height = num_lines * line_height
        return total_height > region.cy
