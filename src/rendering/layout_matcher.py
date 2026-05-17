from src.common.models import LayoutSpec, PlaceholderSpec, SlideIntent
from src.template.layout_classifier import classify_layout


ROLE_TYPE_MAP = {
    "title": {"title", "ctrTitle"},
    "subtitle": {"subtitle"},
    "body": {"body"},
    "key_points": {"body", "obj"},
    "chart": {"chart", "obj"},
    "image": {"pic", "media", "obj"},
    "table": {"tbl", "obj"},
    "footer": {"ftr", "sldNum"},
}

LAYOUT_TYPE_COMPAT = {
    "cover": {"cover", "section"},
    "section": {"section", "cover"},
    "bullet_list": {"bullet_list", "generic"},
    "two_column": {"two_column", "bullet_list", "generic"},
    "image_focus": {"image_focus", "generic"},
    "chart": {"chart", "generic"},
    "table": {"table", "generic"},
    "blank": {"blank", "generic"},
}


class LayoutMatcher:
    def __init__(self):
        self._history: dict[str, float] = {}

    def select(self, intent: SlideIntent, layouts: list[LayoutSpec]) -> LayoutSpec:
        if not layouts:
            raise ValueError("No layouts available for selection")
        scored = [(layout, self._score(intent, layout)) for layout in layouts]
        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]
        self._history[best.id] = self._history.get(best.id, 0.5) + 0.05
        return best

    def _score(self, intent: SlideIntent, layout: LayoutSpec) -> float:
        semantic = self._semantic_role_match(intent, layout)
        capacity = self._placeholder_capacity_match(intent, layout)
        geometry = self._visual_geometry_match(intent, layout)
        priority = layout.score_bias
        historical = self._history.get(layout.id, 0.5)
        overflow = self._overflow_risk(intent, layout)

        return (
            0.35 * semantic
            + 0.25 * capacity
            + 0.20 * geometry
            + 0.10 * priority
            + 0.10 * historical
            - 0.30 * overflow
        )

    def _semantic_role_match(self, intent: SlideIntent, layout: LayoutSpec) -> float:
        if not intent.content_roles:
            return 0.5
        ph_types = {p.ph_type for p in layout.placeholders}
        matched = 0
        for role in intent.content_roles:
            expected = ROLE_TYPE_MAP.get(role, set())
            if expected & ph_types:
                matched += 1
        return matched / len(intent.content_roles)

    def _placeholder_capacity_match(self, intent: SlideIntent, layout: LayoutSpec) -> float:
        needed = len(intent.content_roles)
        if needed == 0:
            return 1.0
        available = len(layout.placeholders)
        if available >= needed:
            return 1.0
        return available / needed

    def _visual_geometry_match(self, intent: SlideIntent, layout: LayoutSpec) -> float:
        layout_type = classify_layout(layout)
        if not intent.slide_type:
            return 0.5
        compatible = LAYOUT_TYPE_COMPAT.get(intent.slide_type, {"generic"})
        if layout_type in compatible:
            return 1.0
        if layout_type == "generic":
            return 0.4
        return 0.1

    def _overflow_risk(self, intent: SlideIntent, layout: LayoutSpec) -> float:
        body_placeholders = [p for p in layout.placeholders if p.ph_type in {"body", "obj"}]
        if not body_placeholders:
            return 0.0
        max_chars = max((p.max_chars or 0) for p in body_placeholders)
        if max_chars == 0:
            return 0.0
        estimated = len(intent.content_roles) * 120
        if estimated <= max_chars:
            return 0.0
        return min(1.0, (estimated - max_chars) / max_chars)
