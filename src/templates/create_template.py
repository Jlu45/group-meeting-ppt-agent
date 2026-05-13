import os
import zipfile
import tempfile
import shutil

from pptx import Presentation
from pptx.util import Inches
from lxml import etree


def create_default_academic_template(output_path: str):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    tmp = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
    tmp.close()
    prs.save(tmp.name)

    modified_path = _inject_theme_into_pptx(tmp.name)

    if modified_path:
        shutil.move(modified_path, output_path)
    else:
        shutil.move(tmp.name, output_path)

    print(f"Default academic template saved to {output_path}")


def _inject_theme_into_pptx(pptx_path: str) -> str:
    primary = "1E3A5F"
    secondary = "4A6FA5"
    accent = "E85D4E"
    bg = "F8F9FA"
    text = "2C3E50"

    try:
        new_path = pptx_path + "_new"
        with zipfile.ZipFile(pptx_path, "r") as zin:
            with zipfile.ZipFile(new_path, "w") as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "ppt/theme/theme1.xml":
                        data = _modify_theme_xml(data, primary, secondary, accent, bg, text)
                    zout.writestr(item, data)

        try:
            os.unlink(pptx_path)
        except Exception:
            pass

        return new_path
    except Exception as e:
        print(f"Theme injection note: {e}")
        return ""


def _modify_theme_xml(data: bytes, primary: str, secondary: str, accent: str, bg: str, text: str) -> bytes:
    root = etree.fromstring(data)

    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

    clr_scheme = root.find(".//a:clrScheme", ns)
    if clr_scheme is None:
        return data

    color_map = {
        "dk1": text,
        "lt1": bg,
        "dk2": primary,
        "lt2": "FFFFFF",
        "accent1": primary,
        "accent2": secondary,
        "accent3": accent,
        "accent4": "95A5A6",
        "accent5": "2ECC71",
        "accent6": "F39C12",
        "hlink": secondary,
        "folHlink": accent,
    }

    for tag, color in color_map.items():
        elem = clr_scheme.find(f"{{{ns['a']}}}{tag}")
        if elem is not None:
            for child in list(elem):
                elem.remove(child)
            srgb = etree.SubElement(elem, f"{{{ns['a']}}}srgbClr")
            srgb.set("val", color)

    font_scheme = root.find(".//a:fontScheme", ns)
    if font_scheme is not None:
        major = font_scheme.find(f"{{{ns['a']}}}majorFont")
        if major is not None:
            latin = major.find(f"{{{ns['a']}}}latin")
            if latin is not None:
                latin.set("typeface", "Source Han Serif SC")
            ea = major.find(f"{{{ns['a']}}}ea")
            if ea is not None:
                ea.set("typeface", "Source Han Serif SC")

        minor = font_scheme.find(f"{{{ns['a']}}}minorFont")
        if minor is not None:
            latin = minor.find(f"{{{ns['a']}}}latin")
            if latin is not None:
                latin.set("typeface", "Source Han Sans SC")
            ea = minor.find(f"{{{ns['a']}}}ea")
            if ea is not None:
                ea.set("typeface", "Source Han Sans SC")

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output = os.path.join(script_dir, "default_academic.pptx")
    create_default_academic_template(output)
