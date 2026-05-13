import zipfile
import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from src.models import (
    TemplateDNA, ThemeColors, FontHierarchy,
    DecorationPatterns, LayoutStructure,
)

logger = logging.getLogger(__name__)

OOXML_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}

EMUs_PER_PT = 12700
EMUs_PER_INCH = 914400


class TemplateDNAExtractor:
    """从PPTX模板提取完整设计规范 - OOXML深度解析"""

    def extract(self, template_path: str) -> TemplateDNA:
        if not Path(template_path).exists():
            logger.warning(f"Template not found: {template_path}, using defaults")
            return TemplateDNA()

        unpacked = self._unpack_pptx(template_path)
        return TemplateDNA(
            theme=self._extract_theme_colors(unpacked),
            fonts=self._extract_font_hierarchy(unpacked),
            layouts=self._extract_layout_structures(unpacked),
            decorations=self._analyze_decoration_patterns(unpacked),
            media=self._extract_media_relationships(unpacked),
            slide_width=self._extract_slide_dimensions(unpacked).get("width", 12192000),
            slide_height=self._extract_slide_dimensions(unpacked).get("height", 6858000),
        )

    def _unpack_pptx(self, path: str) -> dict[str, bytes]:
        unpacked = {}
        with zipfile.ZipFile(path, "r") as zf:
            for name in zf.namelist():
                unpacked[name] = zf.read(name)
        return unpacked

    def _extract_theme_colors(self, unpacked: dict) -> ThemeColors:
        theme_path = "ppt/theme/theme1.xml"
        if theme_path not in unpacked:
            return ThemeColors()

        try:
            root = ET.fromstring(unpacked[theme_path])
            color_scheme = root.find(f".//{{{OOXML_NS['a']}}}clrScheme")
            if color_scheme is None:
                return ThemeColors()

            return ThemeColors(
                primary=self._get_color_from_scheme(color_scheme, "accent1"),
                secondary=self._get_color_from_scheme(color_scheme, "accent2"),
                accent=self._get_color_from_scheme(color_scheme, "accent3"),
                background=self._get_color_from_scheme(color_scheme, "bg1", default="#F8F9FA"),
                text=self._get_color_from_scheme(color_scheme, "tx1", default="#2C3E50"),
                light_bg=self._get_color_from_scheme(color_scheme, "bg2", default="#FFFFFF"),
                subtle=self._get_color_from_scheme(color_scheme, "accent4", default="#95A5A6"),
            )
        except Exception as e:
            logger.error(f"Failed to extract theme colors: {e}")
            return ThemeColors()

    def _get_color_from_scheme(self, scheme, tag: str, default: str = "#1E3A5F") -> str:
        elem = scheme.find(f"{{{OOXML_NS['a']}}}{tag}")
        if elem is None:
            return default

        for child in elem:
            tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag_name == "srgbClr":
                val = child.get("val")
                if val:
                    return f"#{val}"
            elif tag_name == "sysClr":
                val = child.get("lastClr")
                if val:
                    return f"#{val}"
        return default

    def _extract_font_hierarchy(self, unpacked: dict) -> FontHierarchy:
        theme_path = "ppt/theme/theme1.xml"
        if theme_path not in unpacked:
            return FontHierarchy()

        try:
            root = ET.fromstring(unpacked[theme_path])
            font_scheme = root.find(f".//{{{OOXML_NS['a']}}}fontScheme")
            if font_scheme is None:
                return FontHierarchy()

            major_font = font_scheme.find(f"{{{OOXML_NS['a']}}}majorFont")
            minor_font = font_scheme.find(f"{{{OOXML_NS['a']}}}minorFont")

            title_font = self._get_latin_font(major_font, "Source Han Serif SC")
            body_font = self._get_latin_font(minor_font, "Source Han Sans SC")

            title_ea = self._get_ea_font(major_font, title_font)
            body_ea = self._get_ea_font(minor_font, body_font)

            return FontHierarchy(
                title=title_ea or title_font,
                body=body_ea or body_font,
                mono=self._get_latin_font(major_font, "Consolas"),
            )
        except Exception as e:
            logger.error(f"Failed to extract fonts: {e}")
            return FontHierarchy()

    def _get_latin_font(self, font_elem, default: str) -> str:
        if font_elem is None:
            return default
        latin = font_elem.find(f"{{{OOXML_NS['a']}}}latin")
        if latin is not None:
            return latin.get("typeface", default)
        return default

    def _get_ea_font(self, font_elem, default: str) -> str:
        if font_elem is None:
            return default
        ea = font_elem.find(f"{{{OOXML_NS['a']}}}ea")
        if ea is not None:
            return ea.get("typeface", default)
        return default

    def _extract_layout_structures(self, unpacked: dict) -> list[LayoutStructure]:
        layouts = []
        slide_layout_prefix = "ppt/slideLayouts/"
        for name, content in unpacked.items():
            if name.startswith(slide_layout_prefix) and name.endswith(".xml"):
                try:
                    layout = self._parse_slide_layout(name, content)
                    if layout:
                        layouts.append(layout)
                except Exception as e:
                    logger.warning(f"Failed to parse layout {name}: {e}")
        return layouts

    def _parse_slide_layout(self, name: str, content: bytes) -> Optional[LayoutStructure]:
        root = ET.fromstring(content)
        layout_type = "custom"

        cSld = root.find(f".//{{{OOXML_NS['p']}}}cSld")
        if cSld is None:
            return None

        placeholders = {}
        for sp in cSld.findall(f".//{{{OOXML_NS['p']}}}sp"):
            nvSpPr = sp.find(f"{{{OOXML_NS['p']}}}nvSpPr")
            if nvSpPr is not None:
                nvPr = nvSpPr.find(f"{{{OOXML_NS['p']}}}nvPr")
                if nvPr is not None:
                    ph = nvPr.find(f"{{{OOXML_NS['p']}}}ph")
                    if ph is not None:
                        ph_type = ph.get("type", "body")
                        ph_idx = ph.get("idx", "0")

                        spPr = sp.find(f"{{{OOXML_NS['p']}}}spPr")
                        if spPr is not None:
                            xfrm = spPr.find(f".//{{{OOXML_NS['a']}}}xfrm")
                            if xfrm is not None:
                                off = xfrm.find(f"{{{OOXML_NS['a']}}}off")
                                ext = xfrm.find(f"{{{OOXML_NS['a']}}}ext")
                                if off is not None and ext is not None:
                                    placeholders[ph_type] = {
                                        "idx": ph_idx,
                                        "x": int(off.get("x", 0)),
                                        "y": int(off.get("y", 0)),
                                        "cx": int(ext.get("cx", 0)),
                                        "cy": int(ext.get("cy", 0)),
                                    }

                        if ph_type == "title":
                            layout_type = "title"
                        elif ph_type == "ctrTitle":
                            layout_type = "cover"

        return LayoutStructure(
            layout_type=layout_type,
            placeholder_positions=placeholders,
        )

    def _analyze_decoration_patterns(self, unpacked: dict) -> DecorationPatterns:
        logo = self._find_logo(unpacked)
        header = self._find_header_elements(unpacked)
        footer = self._find_footer_elements(unpacked)
        dividers = self._find_divider_lines(unpacked)

        return DecorationPatterns(
            logo=logo,
            header=header,
            footer=footer,
            dividers=dividers,
        )

    def _find_logo(self, unpacked: dict) -> Optional[dict]:
        for name, content in unpacked.items():
            if name.startswith("ppt/slideMasters/") and name.endswith(".xml"):
                try:
                    root = ET.fromstring(content)
                    for pic in root.findall(f".//{{{OOXML_NS['p']}}}pic"):
                        blipFill = pic.find(f"{{{OOXML_NS['p']}}}blipFill")
                        if blipFill is not None:
                            blip = blipFill.find(f"{{{OOXML_NS['a']}}}blip")
                            if blip is not None:
                                embed = blip.get(f"{{{OOXML_NS['r']}}}embed")
                                spPr = pic.find(f"{{{OOXML_NS['p']}}}spPr")
                                pos = self._get_element_position(spPr)
                                if embed and pos:
                                    return {
                                        "rId": embed,
                                        "position": pos,
                                    }
                except Exception:
                    pass
        return None

    def _find_header_elements(self, unpacked: dict) -> Optional[dict]:
        return self._find_zone_elements(unpacked, "top")

    def _find_footer_elements(self, unpacked: dict) -> Optional[dict]:
        return self._find_zone_elements(unpacked, "bottom")

    def _find_zone_elements(self, unpacked: dict, zone: str) -> Optional[dict]:
        for name, content in unpacked.items():
            if name.startswith("ppt/slideMasters/") and name.endswith(".xml"):
                try:
                    root = ET.fromstring(content)
                    elements = []
                    for sp in root.findall(f".//{{{OOXML_NS['p']}}}sp"):
                        spPr = sp.find(f"{{{OOXML_NS['p']}}}spPr")
                        pos = self._get_element_position(spPr)
                        if pos:
                            y_ratio = pos["y"] / 6858000
                            if zone == "top" and y_ratio < 0.15:
                                elements.append(pos)
                            elif zone == "bottom" and y_ratio > 0.85:
                                elements.append(pos)
                    if elements:
                        return {"elements": elements, "zone": zone}
                except Exception:
                    pass
        return None

    def _find_divider_lines(self, unpacked: dict) -> list:
        dividers = []
        for name, content in unpacked.items():
            if name.startswith("ppt/slideMasters/") and name.endswith(".xml"):
                try:
                    root = ET.fromstring(content)
                    for cxnSp in root.findall(f".//{{{OOXML_NS['p']}}}cxnSp"):
                        spPr = cxnSp.find(f"{{{OOXML_NS['p']}}}spPr")
                        pos = self._get_element_position(spPr)
                        if pos and pos["cy"] < 50000:
                            dividers.append(pos)
                except Exception:
                    pass
        return dividers

    def _extract_media_relationships(self, unpacked: dict) -> dict:
        media = {}
        for name, content in unpacked.items():
            if name.startswith("ppt/media/"):
                media[name] = content
        return media

    def _extract_slide_dimensions(self, unpacked: dict) -> dict:
        presentation_path = "ppt/presentation.xml"
        if presentation_path not in unpacked:
            return {}

        try:
            root = ET.fromstring(unpacked[presentation_path])
            sldSz = root.find(f"{{{OOXML_NS['p']}}}sldSz")
            if sldSz is not None:
                return {
                    "width": int(sldSz.get("cx", 12192000)),
                    "height": int(sldSz.get("cy", 6858000)),
                }
        except Exception:
            pass
        return {}

    def _get_element_position(self, spPr) -> Optional[dict]:
        if spPr is None:
            return None
        xfrm = spPr.find(f".//{{{OOXML_NS['a']}}}xfrm")
        if xfrm is None:
            return None
        off = xfrm.find(f"{{{OOXML_NS['a']}}}off")
        ext = xfrm.find(f"{{{OOXML_NS['a']}}}ext")
        if off is None or ext is None:
            return None
        return {
            "x": int(off.get("x", 0)),
            "y": int(off.get("y", 0)),
            "cx": int(ext.get("cx", 0)),
            "cy": int(ext.get("cy", 0)),
        }

    def extract_text_styles(self, unpacked: dict) -> dict:
        theme_path = "ppt/theme/theme1.xml"
        if theme_path not in unpacked:
            return {}

        try:
            root = ET.fromstring(unpacked[theme_path])
            fmt_scheme = root.find(f".//{{{OOXML_NS['a']}}}fmtScheme")
            if fmt_scheme is None:
                return {}

            styles = {}
            for bg in fmt_scheme.findall(f"{{{OOXML_NS['a']}}}bgFillStyleLst/{{{OOXML_NS['a']}}}solidFill"):
                srgb = bg.find(f"{{{OOXML_NS['a']}}}srgbClr")
                if srgb is not None:
                    styles.setdefault("backgrounds", []).append(f"#{srgb.get('val', '')}")

            return styles
        except Exception:
            return {}
