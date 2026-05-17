import zipfile
import tempfile
import os
import shutil
import xml.etree.ElementTree as ET

from src.common.models import (
    Rect,
    ThemeSpec,
    PlaceholderSpec,
    DecorationSpec,
    LayoutSpec,
    MasterSpec,
    TemplateDNA,
    EMU_PER_INCH,
)

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

A_NS = f"{{{NS['a']}}}"
P_NS = f"{{{NS['p']}}}"
R_NS = f"{{{NS['r']}}}"

COLOR_SCHEME_TAGS = [
    "dk1", "lt1", "dk2", "lt2",
    "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
    "hlink", "folHlink",
]

PH_TYPE_ROLE_MAP = {
    "title": ["slide_title"],
    "ctrTitle": ["slide_title", "cover_title"],
    "subTitle": ["subtitle", "slide_subtitle"],
    "body": ["body_text", "content"],
    "obj": ["body_text", "content", "figure"],
    "dt": ["date_time"],
    "sldNum": ["slide_number"],
    "ftr": ["footer"],
    "hdr": ["header"],
    "pic": ["image", "figure"],
    "chart": ["chart"],
    "tbl": ["table"],
    "dgm": ["diagram"],
    "media": ["video", "audio"],
}


class OOXMLTemplateParser:

    def parse(self, pptx_path: str) -> TemplateDNA:
        try:
            unpacked = self._unpack_pptx(pptx_path)
        except Exception:
            return TemplateDNA()

        slide_width, slide_height = self._parse_presentation(unpacked)
        theme = self._parse_theme(unpacked)
        masters = self._parse_slide_masters(unpacked, slide_width, slide_height)
        layouts = self._parse_slide_layouts(unpacked, slide_width, slide_height)
        decorations = self._collect_decorations(masters, layouts)
        media = self._extract_media(unpacked)

        return TemplateDNA(
            slide_width=slide_width,
            slide_height=slide_height,
            theme=theme,
            masters=masters,
            layouts=layouts,
            decorations=decorations,
            media=media,
        )

    def _unpack_pptx(self, pptx_path: str) -> dict:
        unpacked = {}
        with zipfile.ZipFile(pptx_path, "r") as zf:
            for name in zf.namelist():
                unpacked[name] = zf.read(name)
        return unpacked

    def _parse_presentation(self, unpacked: dict):
        width_in = 10.0
        height_in = 7.5
        pres_path = "ppt/presentation.xml"
        if pres_path not in unpacked:
            return width_in, height_in
        try:
            root = ET.fromstring(unpacked[pres_path])
            sldSz = root.find(f"{P_NS}sldSz")
            if sldSz is not None:
                cx = int(sldSz.get("cx", 9144000))
                cy = int(sldSz.get("cy", 6858000))
                width_in = cx / EMU_PER_INCH
                height_in = cy / EMU_PER_INCH
        except Exception:
            pass
        return width_in, height_in

    def _parse_theme(self, unpacked: dict) -> ThemeSpec:
        theme_path = "ppt/theme/theme1.xml"
        if theme_path not in unpacked:
            return ThemeSpec()
        try:
            root = ET.fromstring(unpacked[theme_path])
            colors = self._parse_color_scheme(root)
            fonts = self._parse_font_scheme(root)
            name = ""
            theme_elements = root.find(f"{A_NS}themeElements")
            if theme_elements is not None:
                clr_scheme = theme_elements.find(f"{A_NS}clrScheme")
                if clr_scheme is not None:
                    name = clr_scheme.get("name", "")
            return ThemeSpec(
                name=name,
                colors=colors,
                fonts=fonts,
                raw_theme_xml_path=theme_path,
            )
        except Exception:
            return ThemeSpec()

    def _parse_color_scheme(self, root) -> dict:
        colors = {}
        try:
            clr_scheme = root.find(f".//{A_NS}clrScheme")
            if clr_scheme is None:
                return colors
            for tag in COLOR_SCHEME_TAGS:
                elem = clr_scheme.find(f"{A_NS}{tag}")
                if elem is not None:
                    colors[tag] = self._parse_color_value(elem)
            bg1 = colors.get("lt1", "#FFFFFF")
            bg2 = colors.get("lt2", "#FFFFFF")
            tx1 = colors.get("dk1", "#000000")
            tx2 = colors.get("dk2", "#000000")
            colors["bg1"] = bg1
            colors["bg2"] = bg2
            colors["tx1"] = tx1
            colors["tx2"] = tx2
        except Exception:
            pass
        return colors

    def _parse_font_scheme(self, root) -> dict:
        fonts = {}
        try:
            font_scheme = root.find(f".//{A_NS}fontScheme")
            if font_scheme is None:
                return fonts
            major = font_scheme.find(f"{A_NS}majorFont")
            minor = font_scheme.find(f"{A_NS}minorFont")
            if major is not None:
                latin = major.find(f"{A_NS}latin")
                ea = major.find(f"{A_NS}ea")
                fonts["major_latin"] = latin.get("typeface", "") if latin is not None else ""
                fonts["major_ea"] = ea.get("typeface", "") if ea is not None else ""
            if minor is not None:
                latin = minor.find(f"{A_NS}latin")
                ea = minor.find(f"{A_NS}ea")
                fonts["minor_latin"] = latin.get("typeface", "") if latin is not None else ""
                fonts["minor_ea"] = ea.get("typeface", "") if ea is not None else ""
        except Exception:
            pass
        return fonts

    def _parse_color_value(self, elem) -> str:
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
        return "#000000"

    def _parse_slide_masters(self, unpacked: dict, slide_w: float, slide_h: float) -> list:
        masters = []
        slide_size = (slide_w, slide_h)
        master_prefix = "ppt/slideMasters/"
        for name in sorted(unpacked.keys()):
            if name.startswith(master_prefix) and name.endswith(".xml"):
                try:
                    master = self._parse_single_master(name, unpacked[name], slide_size)
                    if master is not None:
                        masters.append(master)
                except Exception:
                    pass
        return masters

    def _parse_single_master(self, xml_path: str, content: bytes, slide_size: tuple) -> MasterSpec:
        try:
            root = ET.fromstring(content)
        except Exception:
            return None

        cSld = root.find(f".//{P_NS}cSld")
        if cSld is None:
            return None

        master_id = os.path.splitext(os.path.basename(xml_path))[0]
        name = master_id

        decorations = []
        shapes = cSld.findall(f".//{P_NS}sp")
        for sp in shapes:
            if self.is_decoration(sp, slide_size):
                dec = self._shape_to_decoration(sp, "master", slide_size)
                if dec is not None:
                    decorations.append(dec)

        pic_shapes = cSld.findall(f".//{P_NS}pic")
        for pic in pic_shapes:
            dec = self._pic_to_decoration(pic, "master", slide_size)
            if dec is not None:
                decorations.append(dec)

        cxn_shapes = cSld.findall(f".//{P_NS}cxnSp")
        for cxn in cxn_shapes:
            dec = self._cxn_to_decoration(cxn, "master", slide_size)
            if dec is not None:
                decorations.append(dec)

        return MasterSpec(
            id=master_id,
            name=name,
            source_xml_path=xml_path,
            layouts=[],
            decorations=decorations,
        )

    def _parse_slide_layouts(self, unpacked: dict, slide_w: float, slide_h: float) -> list:
        layouts = []
        slide_size = (slide_w, slide_h)
        layout_prefix = "ppt/slideLayouts/"
        for name in sorted(unpacked.keys()):
            if name.startswith(layout_prefix) and name.endswith(".xml"):
                try:
                    layout = self._parse_single_layout(name, unpacked[name], slide_size)
                    if layout is not None:
                        layouts.append(layout)
                except Exception:
                    pass
        return layouts

    def _parse_single_layout(self, xml_path: str, content: bytes, slide_size: tuple) -> LayoutSpec:
        try:
            root = ET.fromstring(content)
        except Exception:
            return None

        cSld = root.find(f".//{P_NS}cSld")
        if cSld is None:
            return None

        layout_id = os.path.splitext(os.path.basename(xml_path))[0]
        name = layout_id
        layout_type = "custom"

        placeholders = []
        shapes = cSld.findall(f".//{P_NS}sp")
        for sp in shapes:
            nvSpPr = sp.find(f"{P_NS}nvSpPr")
            if nvSpPr is None:
                continue
            nvPr = nvSpPr.find(f"{P_NS}nvPr")
            if nvPr is None:
                continue
            ph = nvPr.find(f"{P_NS}ph")
            if ph is None:
                continue

            ph_type = ph.get("type", "body")
            ph_idx_str = ph.get("idx")
            ph_idx = int(ph_idx_str) if ph_idx_str is not None else None

            spPr = sp.find(f"{P_NS}spPr")
            rect = self._parse_xfrm_from_spPr(spPr)

            text_style = self._extract_text_style(sp)
            shape_style = self._extract_shape_style(sp)

            sp_id = ""
            cNvPr = nvSpPr.find(f"{P_NS}cNvPr")
            if cNvPr is not None:
                sp_id = cNvPr.get("id", "")

            ph_spec = PlaceholderSpec(
                id=f"{layout_id}_ph_{sp_id}",
                layout_id=layout_id,
                ph_type=ph_type,
                idx=ph_idx,
                rect=rect,
                text_style=text_style,
                shape_style=shape_style,
                priority=self._calc_ph_priority(ph_type),
                max_chars=self.estimate_max_chars(rect, ph_type),
                semantic_roles=self.infer_semantic_roles(ph_type, rect),
            )
            placeholders.append(ph_spec)

            if ph_type in ("title", "ctrTitle"):
                layout_type = "title" if ph_type == "title" else "cover"

        decorations = []
        for sp in shapes:
            if self.is_decoration(sp, slide_size):
                dec = self._shape_to_decoration(sp, "layout", slide_size)
                if dec is not None:
                    dec.apply_to = [layout_id]
                    decorations.append(dec)

        pic_shapes = cSld.findall(f".//{P_NS}pic")
        for pic in pic_shapes:
            dec = self._pic_to_decoration(pic, "layout", slide_size)
            if dec is not None:
                dec.apply_to = [layout_id]
                decorations.append(dec)

        tags = self._infer_layout_tags(layout_type, placeholders)

        return LayoutSpec(
            id=layout_id,
            name=name,
            source_xml_path=xml_path,
            layout_type=layout_type,
            placeholders=placeholders,
            decorations=decorations,
            tags=tags,
        )

    def _parse_xfrm_from_spPr(self, spPr) -> Rect:
        if spPr is None:
            return Rect()
        xfrm = spPr.find(f".//{A_NS}xfrm")
        if xfrm is None:
            return Rect()
        return self._parse_xfrm(xfrm)

    def _parse_xfrm(self, xfrm) -> Rect:
        try:
            off = xfrm.find(f"{A_NS}off")
            ext = xfrm.find(f"{A_NS}ext")
            if off is None or ext is None:
                return Rect()
            x = int(off.get("x", 0)) / EMU_PER_INCH
            y = int(off.get("y", 0)) / EMU_PER_INCH
            w = int(ext.get("cx", 0)) / EMU_PER_INCH
            h = int(ext.get("cy", 0)) / EMU_PER_INCH
            return Rect(x=x, y=y, w=w, h=h)
        except Exception:
            return Rect()

    def _extract_text_style(self, sp) -> dict:
        style = {}
        try:
            txBody = sp.find(f"{P_NS}txBody")
            if txBody is None:
                return style
            bodyPr = txBody.find(f"{A_NS}bodyPr")
            if bodyPr is not None:
                anchor = bodyPr.get("anchor", "")
                if anchor:
                    style["anchor"] = anchor
                lIns = bodyPr.get("lIns")
                tIns = bodyPr.get("tIns")
                rIns = bodyPr.get("rIns")
                bIns = bodyPr.get("bIns")
                if lIns is not None:
                    style["lIns"] = int(lIns)
                if tIns is not None:
                    style["tIns"] = int(tIns)
                if rIns is not None:
                    style["rIns"] = int(rIns)
                if bIns is not None:
                    style["bIns"] = int(bIns)
            for p in txBody.findall(f"{A_NS}p"):
                for r in p.findall(f"{A_NS}r"):
                    rPr = r.find(f"{A_NS}rPr")
                    if rPr is not None:
                        sz = rPr.get("sz")
                        if sz is not None:
                            style["font_size"] = int(sz) / 100
                        b = rPr.get("b")
                        if b is not None:
                            style["bold"] = b == "1"
                        i = rPr.get("i")
                        if i is not None:
                            style["italic"] = i == "1"
                        solidFill = rPr.find(f"{A_NS}solidFill")
                        if solidFill is not None:
                            color = self._parse_color_value(solidFill)
                            style["font_color"] = color
                        latin = rPr.find(f"{A_NS}latin")
                        if latin is not None:
                            style["latin_font"] = latin.get("typeface", "")
                        ea = rPr.find(f"{A_NS}ea")
                        if ea is not None:
                            style["ea_font"] = ea.get("typeface", "")
                    break
                break
        except Exception:
            pass
        return style

    def _extract_shape_style(self, sp) -> dict:
        style = {}
        try:
            spPr = sp.find(f"{P_NS}spPr")
            if spPr is None:
                return style
            ln = spPr.find(f"{A_NS}ln")
            if ln is not None:
                w = ln.get("w")
                if w is not None:
                    style["line_width"] = int(w)
                solidFill = ln.find(f"{A_NS}solidFill")
                if solidFill is not None:
                    style["line_color"] = self._parse_color_value(solidFill)
            fill = spPr.find(f"{A_NS}solidFill")
            if fill is not None:
                style["fill_color"] = self._parse_color_value(fill)
            gradFill = spPr.find(f"{A_NS}gradFill")
            if gradFill is not None:
                style["fill_type"] = "gradient"
        except Exception:
            pass
        return style

    def _shape_to_decoration(self, sp, source: str, slide_size: tuple) -> DecorationSpec:
        try:
            spPr = sp.find(f"{P_NS}spPr")
            rect = self._parse_xfrm_from_spPr(spPr)
            nvSpPr = sp.find(f"{P_NS}nvSpPr")
            sp_id = ""
            if nvSpPr is not None:
                cNvPr = nvSpPr.find(f"{P_NS}cNvPr")
                if cNvPr is not None:
                    sp_id = cNvPr.get("id", "")

            xml_fragment = ET.tostring(sp, encoding="unicode")

            shape_type = "shape"
            nvPr = nvSpPr.find(f"{P_NS}nvPr") if nvSpPr is not None else None
            if nvPr is not None:
                ph = nvPr.find(f"{P_NS}ph")
                if ph is not None:
                    ph_type = ph.get("type", "")
                    if ph_type in ("ftr", "hdr", "dt", "sldNum"):
                        shape_type = ph_type

            return DecorationSpec(
                id=f"dec_{source}_{sp_id}",
                source=source,
                shape_type=shape_type,
                rect=rect,
                xml_fragment=xml_fragment,
            )
        except Exception:
            return None

    def _pic_to_decoration(self, pic, source: str, slide_size: tuple) -> DecorationSpec:
        try:
            spPr = pic.find(f"{P_NS}spPr")
            rect = self._parse_xfrm_from_spPr(spPr)
            nvPicPr = pic.find(f"{P_NS}nvPicPr")
            sp_id = ""
            if nvPicPr is not None:
                cNvPr = nvPicPr.find(f"{P_NS}cNvPr")
                if cNvPr is not None:
                    sp_id = cNvPr.get("id", "")

            media_rel_id = None
            blipFill = pic.find(f"{P_NS}blipFill")
            if blipFill is not None:
                blip = blipFill.find(f"{A_NS}blip")
                if blip is not None:
                    media_rel_id = blip.get(f"{R_NS}embed")

            xml_fragment = ET.tostring(pic, encoding="unicode")

            return DecorationSpec(
                id=f"dec_{source}_pic_{sp_id}",
                source=source,
                shape_type="picture",
                rect=rect,
                xml_fragment=xml_fragment,
                media_rel_id=media_rel_id,
            )
        except Exception:
            return None

    def _cxn_to_decoration(self, cxn, source: str, slide_size: tuple) -> DecorationSpec:
        try:
            spPr = cxn.find(f"{P_NS}spPr")
            rect = self._parse_xfrm_from_spPr(spPr)
            nvCxnSpPr = cxn.find(f"{P_NS}nvCxnSpPr")
            sp_id = ""
            if nvCxnSpPr is not None:
                cNvPr = nvCxnSpPr.find(f"{P_NS}cNvPr")
                if cNvPr is not None:
                    sp_id = cNvPr.get("id", "")

            xml_fragment = ET.tostring(cxn, encoding="unicode")

            return DecorationSpec(
                id=f"dec_{source}_cxn_{sp_id}",
                source=source,
                shape_type="connector",
                rect=rect,
                xml_fragment=xml_fragment,
            )
        except Exception:
            return None

    def _collect_decorations(self, masters: list, layouts: list) -> list:
        decorations = []
        for master in masters:
            decorations.extend(master.decorations)
        for layout in layouts:
            decorations.extend(layout.decorations)
        return decorations

    def _extract_media(self, unpacked: dict) -> dict:
        media = {}
        media_prefix = "ppt/media/"
        for name in unpacked:
            if name.startswith(media_prefix):
                media[name] = unpacked[name]
        return media

    def _calc_ph_priority(self, ph_type: str) -> int:
        priority_map = {
            "ctrTitle": 10,
            "title": 9,
            "subTitle": 8,
            "body": 7,
            "obj": 6,
            "tbl": 5,
            "chart": 5,
            "pic": 4,
            "dgm": 3,
            "media": 2,
            "dt": 1,
            "sldNum": 1,
            "ftr": 1,
            "hdr": 1,
        }
        return priority_map.get(ph_type, 0)

    def _infer_layout_tags(self, layout_type: str, placeholders: list) -> list:
        tags = []
        if layout_type == "cover":
            tags.append("cover")
        elif layout_type == "title":
            tags.append("title_slide")

        ph_types = {p.ph_type for p in placeholders}
        if "body" in ph_types or "obj" in ph_types:
            tags.append("content")
        if "tbl" in ph_types:
            tags.append("table")
        if "chart" in ph_types:
            tags.append("chart")
        if "pic" in ph_types:
            tags.append("image")
        if "media" in ph_types:
            tags.append("media")
        if not tags:
            tags.append("custom")
        return tags

    @staticmethod
    def infer_semantic_roles(ph_type: str, rect: Rect) -> list:
        roles = list(PH_TYPE_ROLE_MAP.get(ph_type, ["unknown"]))

        if rect.w <= 0 or rect.h <= 0:
            return roles

        slide_w_approx = 10.0
        slide_h_approx = 7.5
        x_ratio = rect.x / slide_w_approx if slide_w_approx > 0 else 0
        y_ratio = rect.y / slide_h_approx if slide_h_approx > 0 else 0
        w_ratio = rect.w / slide_w_approx if slide_w_approx > 0 else 0
        h_ratio = rect.h / slide_h_approx if slide_h_approx > 0 else 0

        if ph_type in ("title", "ctrTitle"):
            if y_ratio < 0.2 and w_ratio > 0.5:
                roles.append("top_title")
            elif y_ratio > 0.3 and w_ratio < 0.5:
                roles.append("side_title")
        elif ph_type in ("body", "obj"):
            if w_ratio > 0.7:
                roles.append("full_width_content")
            elif w_ratio < 0.5 and x_ratio < 0.3:
                roles.append("left_column")
            elif w_ratio < 0.5 and x_ratio > 0.5:
                roles.append("right_column")
            if h_ratio < 0.3:
                roles.append("short_text")
            elif h_ratio > 0.5:
                roles.append("long_text")
        elif ph_type == "subTitle":
            if y_ratio < 0.4:
                roles.append("cover_subtitle")

        return roles

    @staticmethod
    def estimate_max_chars(rect: Rect, ph_type: str) -> int:
        if rect.w <= 0 or rect.h <= 0:
            return 0

        font_size_map = {
            "ctrTitle": 28,
            "title": 24,
            "subTitle": 18,
            "body": 14,
            "obj": 14,
            "tbl": 12,
            "chart": 12,
            "pic": 10,
            "dt": 10,
            "sldNum": 10,
            "ftr": 10,
            "hdr": 10,
        }
        font_size_pt = font_size_map.get(ph_type, 14)
        chars_per_line = int((rect.w * 72) / (font_size_pt * 0.6))
        line_height_in = font_size_pt / 72 * 1.2
        num_lines = max(1, int(rect.h / line_height_in))
        return chars_per_line * num_lines

    @staticmethod
    def is_decoration(shape, slide_size: tuple) -> bool:
        try:
            nvSpPr = shape.find(f"{P_NS}nvSpPr")
            if nvSpPr is None:
                return False
            nvPr = nvSpPr.find(f"{P_NS}nvPr")
            if nvPr is not None:
                ph = nvPr.find(f"{P_NS}ph")
                if ph is not None:
                    ph_type = ph.get("type", "")
                    if ph_type in ("ftr", "hdr", "dt", "sldNum"):
                        return True
                    if ph_type in ("title", "ctrTitle", "subTitle", "body", "obj",
                                   "tbl", "chart", "pic", "dgm", "media"):
                        return False

            spPr = shape.find(f"{P_NS}spPr")
            if spPr is None:
                return False
            xfrm = spPr.find(f".//{A_NS}xfrm")
            if xfrm is None:
                return False
            off = xfrm.find(f"{A_NS}off")
            ext = xfrm.find(f"{A_NS}ext")
            if off is None or ext is None:
                return False

            cx = int(ext.get("cx", 0))
            cy = int(ext.get("cy", 0))

            if cy < 50000 and cx > 500000:
                return True

            slide_w_emu = int(slide_size[0] * EMU_PER_INCH) if slide_size else 9144000
            slide_h_emu = int(slide_size[1] * EMU_PER_INCH) if slide_size else 6858000
            x = int(off.get("x", 0))
            y = int(off.get("y", 0))

            if y < slide_h_emu * 0.08 and cy < slide_h_emu * 0.08:
                return True
            if y > slide_h_emu * 0.88 and cy < slide_h_emu * 0.12:
                return True

            noFill = spPr.find(f"{A_NS}noFill")
            has_text = False
            txBody = shape.find(f"{P_NS}txBody")
            if txBody is not None:
                for p in txBody.findall(f"{A_NS}p"):
                    for r in p.findall(f"{A_NS}r"):
                        t = r.find(f"{A_NS}t")
                        if t is not None and t.text and t.text.strip():
                            has_text = True
                            break
                    if has_text:
                        break

            if not has_text and noFill is not None:
                return True

            return False
        except Exception:
            return False
