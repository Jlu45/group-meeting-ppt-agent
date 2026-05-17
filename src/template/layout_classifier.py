from src.common.models import LayoutSpec, PlaceholderSpec


TITLE_TYPES = {"title", "ctrTitle"}
BODY_TYPES = {"body", "obj"}
MEDIA_TYPES = {"pic", "media"}
CHART_TYPES = {"chart"}
TABLE_TYPES = {"tbl"}
SUBTITLE_TYPES = {"subtitle"}
FOOTER_TYPES = {"ftr", "sldNum"}


def is_two_column(bodies: list) -> bool:
    if len(bodies) < 2:
        return False
    sorted_bodies = sorted(bodies, key=lambda p: p.rect.x)
    first = sorted_bodies[0]
    second = sorted_bodies[1]
    x_diff = abs(second.rect.x - first.rect.x)
    y_diff = abs(second.rect.y - first.rect.y)
    avg_w = (first.rect.w + second.rect.w) / 2
    return x_diff > avg_w * 0.3 and y_diff < avg_w * 0.5


def classify_layout(layout: LayoutSpec) -> str:
    placeholders = layout.placeholders
    titles = [p for p in placeholders if p.ph_type in TITLE_TYPES]
    bodies = [p for p in placeholders if p.ph_type in BODY_TYPES]
    medias = [p for p in placeholders if p.ph_type in MEDIA_TYPES]
    charts = [p for p in placeholders if p.ph_type in CHART_TYPES]
    tables = [p for p in placeholders if p.ph_type in TABLE_TYPES]
    subtitles = [p for p in placeholders if p.ph_type in SUBTITLE_TYPES]

    has_title = len(titles) > 0
    has_body = len(bodies) > 0
    has_media = len(medias) > 0
    has_chart = len(charts) > 0
    has_table = len(tables) > 0
    has_subtitle = len(subtitles) > 0

    ctr_titles = [p for p in placeholders if p.ph_type == "ctrTitle"]
    has_ctr_title = len(ctr_titles) > 0

    if has_ctr_title and has_subtitle and not has_body:
        return "section"

    if has_title and not has_body and not has_media and not has_chart and not has_table:
        if has_ctr_title:
            return "cover"
        if not has_subtitle:
            return "cover"

    if has_media and len(bodies) <= 1:
        return "image_focus"

    if has_title and has_chart:
        return "chart"

    if has_title and has_table:
        return "table"

    if has_title and len(bodies) >= 2 and is_two_column(bodies):
        return "two_column"

    if has_title and len(bodies) == 1:
        return "bullet_list"

    if not has_title and not has_body:
        return "blank"

    return "generic"
