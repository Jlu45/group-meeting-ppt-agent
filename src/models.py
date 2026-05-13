from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class DocType(Enum):
    PROGRESS_REPORT = "progress_report"
    EXPERIMENT_LOG = "experiment_log"
    LITERATURE_NOTE = "literature_note"
    TECH_DESIGN = "tech_design"
    OTHER = "other"


class LayoutType(Enum):
    COVER = "cover"
    BULLET_LIST = "bullet_list"
    TWO_COLUMN = "two_column"
    CHART = "chart"
    TABLE = "table"
    IMAGE_GRID = "image_grid"
    ARCHITECTURE = "architecture"
    SUMMARY = "summary"
    DISCUSSION = "discussion"


@dataclass
class ParsedDocument:
    source_path: str
    markdown_content: str
    file_type: str = ""


@dataclass
class ThemeColors:
    primary: str = "#1E3A5F"
    secondary: str = "#4A6FA5"
    accent: str = "#E85D4E"
    background: str = "#F8F9FA"
    text: str = "#2C3E50"
    light_bg: str = "#FFFFFF"
    subtle: str = "#95A5A6"


@dataclass
class FontHierarchy:
    title: str = "Source Han Serif SC"
    body: str = "Source Han Sans SC"
    mono: str = "Consolas"
    title_size: int = 32
    subtitle_size: int = 24
    body_size: int = 18
    small_size: int = 14


@dataclass
class DecorationPatterns:
    logo: Optional[dict] = None
    header: Optional[dict] = None
    footer: Optional[dict] = None
    dividers: list = field(default_factory=list)


@dataclass
class LayoutStructure:
    layout_type: str
    placeholder_positions: dict = field(default_factory=dict)
    element_positions: dict = field(default_factory=dict)


@dataclass
class TemplateDNA:
    theme: ThemeColors = field(default_factory=ThemeColors)
    fonts: FontHierarchy = field(default_factory=FontHierarchy)
    layouts: list = field(default_factory=list)
    decorations: DecorationPatterns = field(default_factory=DecorationPatterns)
    media: dict = field(default_factory=dict)
    slide_width: int = 12192000
    slide_height: int = 6858000


@dataclass
class SlidePlan:
    title: str
    layout: LayoutType
    points: list = field(default_factory=list)
    table_data: Optional[list] = None
    chart_desc: Optional[str] = None
    image_paths: list = field(default_factory=list)
    notes: str = ""


@dataclass
class StructuredPresentation:
    doc_type: DocType
    title: str
    summary: str
    slides: list = field(default_factory=list)
    author: str = ""
    date: str = ""


@dataclass
class ComplianceReport:
    color_score: float = 0.0
    font_score: float = 0.0
    layout_score: float = 0.0
    decoration_score: float = 0.0

    @property
    def overall_score(self) -> float:
        return (self.color_score + self.font_score + self.layout_score + self.decoration_score) / 4

    @property
    def passed(self) -> bool:
        return self.overall_score >= 0.9


@dataclass
class ValidationResult:
    level1_passed: bool = False
    level2_passed: bool = False
    level3_passed: bool = False
    issues: list = field(default_factory=list)
    compliance: Optional[ComplianceReport] = None

    @property
    def all_passed(self) -> bool:
        return self.level1_passed and self.level2_passed and self.level3_passed
