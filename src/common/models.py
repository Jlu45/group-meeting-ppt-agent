from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Literal, Optional, Union

EMU_PER_INCH = 914400


@dataclass
class Rect:
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Rect":
        return cls(x=d.get("x", 0.0), y=d.get("y", 0.0), w=d.get("w", 0.0), h=d.get("h", 0.0))


@dataclass
class ThemeSpec:
    name: str = ""
    colors: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, str] = field(default_factory=dict)
    raw_theme_xml_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "colors": self.colors,
            "fonts": self.fonts,
            "raw_theme_xml_path": self.raw_theme_xml_path,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ThemeSpec":
        return cls(
            name=d.get("name", ""),
            colors=d.get("colors", {}),
            fonts=d.get("fonts", {}),
            raw_theme_xml_path=d.get("raw_theme_xml_path"),
        )


@dataclass
class PlaceholderSpec:
    id: str = ""
    layout_id: str = ""
    ph_type: str = ""
    idx: Optional[int] = None
    rect: Rect = field(default_factory=Rect)
    text_style: Dict[str, Any] = field(default_factory=dict)
    shape_style: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    max_chars: Optional[int] = None
    semantic_roles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "layout_id": self.layout_id,
            "ph_type": self.ph_type,
            "idx": self.idx,
            "rect": self.rect.to_dict(),
            "text_style": self.text_style,
            "shape_style": self.shape_style,
            "priority": self.priority,
            "max_chars": self.max_chars,
            "semantic_roles": self.semantic_roles,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlaceholderSpec":
        return cls(
            id=d.get("id", ""),
            layout_id=d.get("layout_id", ""),
            ph_type=d.get("ph_type", ""),
            idx=d.get("idx"),
            rect=Rect.from_dict(d["rect"]) if "rect" in d else Rect(),
            text_style=d.get("text_style", {}),
            shape_style=d.get("shape_style", {}),
            priority=d.get("priority", 0),
            max_chars=d.get("max_chars"),
            semantic_roles=d.get("semantic_roles", []),
        )


@dataclass
class DecorationSpec:
    id: str = ""
    source: Literal["master", "layout", "slide"] = "master"
    shape_type: str = ""
    rect: Rect = field(default_factory=Rect)
    xml_fragment: str = ""
    media_rel_id: Optional[str] = None
    apply_to: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "shape_type": self.shape_type,
            "rect": self.rect.to_dict(),
            "xml_fragment": self.xml_fragment,
            "media_rel_id": self.media_rel_id,
            "apply_to": self.apply_to,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DecorationSpec":
        return cls(
            id=d.get("id", ""),
            source=d.get("source", "master"),
            shape_type=d.get("shape_type", ""),
            rect=Rect.from_dict(d["rect"]) if "rect" in d else Rect(),
            xml_fragment=d.get("xml_fragment", ""),
            media_rel_id=d.get("media_rel_id"),
            apply_to=d.get("apply_to", []),
        )


@dataclass
class LayoutSpec:
    id: str = ""
    name: str = ""
    source_xml_path: str = ""
    layout_type: str = ""
    placeholders: List[PlaceholderSpec] = field(default_factory=list)
    decorations: List[DecorationSpec] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    score_bias: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_xml_path": self.source_xml_path,
            "layout_type": self.layout_type,
            "placeholders": [p.to_dict() for p in self.placeholders],
            "decorations": [d.to_dict() for d in self.decorations],
            "tags": self.tags,
            "score_bias": self.score_bias,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LayoutSpec":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            source_xml_path=d.get("source_xml_path", ""),
            layout_type=d.get("layout_type", ""),
            placeholders=[PlaceholderSpec.from_dict(p) for p in d.get("placeholders", [])],
            decorations=[DecorationSpec.from_dict(dc) for dc in d.get("decorations", [])],
            tags=d.get("tags", []),
            score_bias=d.get("score_bias", 0.0),
        )


@dataclass
class MasterSpec:
    id: str = ""
    name: str = ""
    source_xml_path: str = ""
    layouts: List[LayoutSpec] = field(default_factory=list)
    decorations: List[DecorationSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_xml_path": self.source_xml_path,
            "layouts": [l.to_dict() for l in self.layouts],
            "decorations": [d.to_dict() for d in self.decorations],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MasterSpec":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            source_xml_path=d.get("source_xml_path", ""),
            layouts=[LayoutSpec.from_dict(l) for l in d.get("layouts", [])],
            decorations=[DecorationSpec.from_dict(dc) for dc in d.get("decorations", [])],
        )


@dataclass
class TemplateDNA:
    slide_width: float = 0.0
    slide_height: float = 0.0
    theme: ThemeSpec = field(default_factory=ThemeSpec)
    masters: List[MasterSpec] = field(default_factory=list)
    layouts: List[LayoutSpec] = field(default_factory=list)
    decorations: List[DecorationSpec] = field(default_factory=list)
    media: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_width": self.slide_width,
            "slide_height": self.slide_height,
            "theme": self.theme.to_dict(),
            "masters": [m.to_dict() for m in self.masters],
            "layouts": [l.to_dict() for l in self.layouts],
            "decorations": [d.to_dict() for d in self.decorations],
            "media": self.media,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TemplateDNA":
        return cls(
            slide_width=d.get("slide_width", 0.0),
            slide_height=d.get("slide_height", 0.0),
            theme=ThemeSpec.from_dict(d["theme"]) if "theme" in d else ThemeSpec(),
            masters=[MasterSpec.from_dict(m) for m in d.get("masters", [])],
            layouts=[LayoutSpec.from_dict(l) for l in d.get("layouts", [])],
            decorations=[DecorationSpec.from_dict(dc) for dc in d.get("decorations", [])],
            media=d.get("media", {}),
        )


@dataclass
class SourceFile:
    id: str = ""
    path: str = ""
    filename: str = ""
    extension: str = ""
    base_type: str = ""
    content_type: str = ""
    sequence: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "filename": self.filename,
            "extension": self.extension,
            "base_type": self.base_type,
            "content_type": self.content_type,
            "sequence": self.sequence,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SourceFile":
        return cls(
            id=d.get("id", ""),
            path=d.get("path", ""),
            filename=d.get("filename", ""),
            extension=d.get("extension", ""),
            base_type=d.get("base_type", ""),
            content_type=d.get("content_type", ""),
            sequence=d.get("sequence"),
            metadata=d.get("metadata", {}),
        )


@dataclass
class FileRecognitionResult:
    id: str = ""
    path: str = ""
    filename: str = ""
    extension: str = ""
    base_type: str = ""
    content_type: str = ""
    ppt_purpose: str = ""
    confidence: float = 0.0
    sequence_number: Optional[int] = None
    date: Optional[str] = None
    version: Optional[str] = None
    suggested_parser: str = ""
    suggested_slide_types: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "filename": self.filename,
            "extension": self.extension,
            "base_type": self.base_type,
            "content_type": self.content_type,
            "ppt_purpose": self.ppt_purpose,
            "confidence": self.confidence,
            "sequence_number": self.sequence_number,
            "date": self.date,
            "version": self.version,
            "suggested_parser": self.suggested_parser,
            "suggested_slide_types": self.suggested_slide_types,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FileRecognitionResult":
        return cls(
            id=d.get("id", ""),
            path=d.get("path", ""),
            filename=d.get("filename", ""),
            extension=d.get("extension", ""),
            base_type=d.get("base_type", ""),
            content_type=d.get("content_type", ""),
            ppt_purpose=d.get("ppt_purpose", ""),
            confidence=d.get("confidence", 0.0),
            sequence_number=d.get("sequence_number"),
            date=d.get("date"),
            version=d.get("version"),
            suggested_parser=d.get("suggested_parser", ""),
            suggested_slide_types=d.get("suggested_slide_types", []),
        )


@dataclass
class Evidence:
    id: str = ""
    source_file_id: str = ""
    location: str = ""
    quote: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_file_id": self.source_file_id,
            "location": self.location,
            "quote": self.quote,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Evidence":
        return cls(
            id=d.get("id", ""),
            source_file_id=d.get("source_file_id", ""),
            location=d.get("location", ""),
            quote=d.get("quote", ""),
            confidence=d.get("confidence", 0.0),
        )


@dataclass
class ContentUnit:
    id: str = ""
    kind: str = ""
    title: str = ""
    summary: str = ""
    details: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    priority: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
            "details": self.details,
            "evidence_ids": self.evidence_ids,
            "priority": self.priority,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ContentUnit":
        return cls(
            id=d.get("id", ""),
            kind=d.get("kind", ""),
            title=d.get("title", ""),
            summary=d.get("summary", ""),
            details=d.get("details", []),
            evidence_ids=d.get("evidence_ids", []),
            priority=d.get("priority", 0),
            tags=d.get("tags", []),
        )


@dataclass
class TableAsset:
    id: str = ""
    source_file_id: str = ""
    title: str = ""
    dataframe_ref: str = ""
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    summary: str = ""
    suggested_use: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_file_id": self.source_file_id,
            "title": self.title,
            "dataframe_ref": self.dataframe_ref,
            "columns": self.columns,
            "row_count": self.row_count,
            "summary": self.summary,
            "suggested_use": self.suggested_use,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TableAsset":
        return cls(
            id=d.get("id", ""),
            source_file_id=d.get("source_file_id", ""),
            title=d.get("title", ""),
            dataframe_ref=d.get("dataframe_ref", ""),
            columns=d.get("columns", []),
            row_count=d.get("row_count", 0),
            summary=d.get("summary", ""),
            suggested_use=d.get("suggested_use", ""),
        )


@dataclass
class FigureAsset:
    id: str = ""
    source_file_id: str = ""
    path: str = ""
    title: str = ""
    caption: str = ""
    image_type: str = ""
    suggested_use: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_file_id": self.source_file_id,
            "path": self.path,
            "title": self.title,
            "caption": self.caption,
            "image_type": self.image_type,
            "suggested_use": self.suggested_use,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FigureAsset":
        return cls(
            id=d.get("id", ""),
            source_file_id=d.get("source_file_id", ""),
            path=d.get("path", ""),
            title=d.get("title", ""),
            caption=d.get("caption", ""),
            image_type=d.get("image_type", ""),
            suggested_use=d.get("suggested_use", ""),
        )


@dataclass
class CodeAsset:
    id: str = ""
    source_file_id: str = ""
    language: str = ""
    purpose: str = ""
    entry_points: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_file_id": self.source_file_id,
            "language": self.language,
            "purpose": self.purpose,
            "entry_points": self.entry_points,
            "outputs": self.outputs,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CodeAsset":
        return cls(
            id=d.get("id", ""),
            source_file_id=d.get("source_file_id", ""),
            language=d.get("language", ""),
            purpose=d.get("purpose", ""),
            entry_points=d.get("entry_points", []),
            outputs=d.get("outputs", []),
            summary=d.get("summary", ""),
        )


@dataclass
class MetricAsset:
    id: str = ""
    name: str = ""
    value: Any = None
    unit: Optional[str] = None
    baseline: Optional[Any] = None
    delta: Optional[Any] = None
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "baseline": self.baseline,
            "delta": self.delta,
            "evidence_ids": self.evidence_ids,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MetricAsset":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            value=d.get("value"),
            unit=d.get("unit"),
            baseline=d.get("baseline"),
            delta=d.get("delta"),
            evidence_ids=d.get("evidence_ids", []),
        )


@dataclass
class AssetStore:
    source_files: Dict[str, SourceFile] = field(default_factory=dict)
    evidences: Dict[str, Evidence] = field(default_factory=dict)
    content_units: Dict[str, ContentUnit] = field(default_factory=dict)
    tables: Dict[str, TableAsset] = field(default_factory=dict)
    figures: Dict[str, FigureAsset] = field(default_factory=dict)
    code: Dict[str, CodeAsset] = field(default_factory=dict)
    metrics: Dict[str, MetricAsset] = field(default_factory=dict)

    def by_tag(self, tag: str) -> List[ContentUnit]:
        return [u for u in self.content_units.values() if tag in u.tags]

    def top_units(self, n: int = 10) -> List[ContentUnit]:
        sorted_units = sorted(self.content_units.values(), key=lambda u: u.priority, reverse=True)
        return sorted_units[:n]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_files": {k: v.to_dict() for k, v in self.source_files.items()},
            "evidences": {k: v.to_dict() for k, v in self.evidences.items()},
            "content_units": {k: v.to_dict() for k, v in self.content_units.items()},
            "tables": {k: v.to_dict() for k, v in self.tables.items()},
            "figures": {k: v.to_dict() for k, v in self.figures.items()},
            "code": {k: v.to_dict() for k, v in self.code.items()},
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AssetStore":
        return cls(
            source_files={k: SourceFile.from_dict(v) for k, v in d.get("source_files", {}).items()},
            evidences={k: Evidence.from_dict(v) for k, v in d.get("evidences", {}).items()},
            content_units={k: ContentUnit.from_dict(v) for k, v in d.get("content_units", {}).items()},
            tables={k: TableAsset.from_dict(v) for k, v in d.get("tables", {}).items()},
            figures={k: FigureAsset.from_dict(v) for k, v in d.get("figures", {}).items()},
            code={k: CodeAsset.from_dict(v) for k, v in d.get("code", {}).items()},
            metrics={k: MetricAsset.from_dict(v) for k, v in d.get("metrics", {}).items()},
        )


@dataclass
class SlideIntent:
    slide_type: str = ""
    content_roles: List[str] = field(default_factory=list)
    density: str = ""
    preferred_layout: Optional[str] = None
    must_have: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_type": self.slide_type,
            "content_roles": self.content_roles,
            "density": self.density,
            "preferred_layout": self.preferred_layout,
            "must_have": self.must_have,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SlideIntent":
        return cls(
            slide_type=d.get("slide_type", ""),
            content_roles=d.get("content_roles", []),
            density=d.get("density", ""),
            preferred_layout=d.get("preferred_layout"),
            must_have=d.get("must_have", []),
        )


@dataclass
class SlideElementSpec:
    role: str = ""
    content: Union[str, Dict[str, Any]] = ""
    asset_ids: List[str] = field(default_factory=list)
    required: bool = True
    visual_weight: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "asset_ids": self.asset_ids,
            "required": self.required,
            "visual_weight": self.visual_weight,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SlideElementSpec":
        return cls(
            role=d.get("role", ""),
            content=d.get("content", ""),
            asset_ids=d.get("asset_ids", []),
            required=d.get("required", True),
            visual_weight=d.get("visual_weight", 1),
        )


@dataclass
class SlideSpec:
    id: str = ""
    slide_type: str = ""
    title: str = ""
    message: str = ""
    elements: List[SlideElementSpec] = field(default_factory=list)
    intent: SlideIntent = field(default_factory=SlideIntent)
    candidate_layout_ids: List[str] = field(default_factory=list)
    selected_layout_id: Optional[str] = None
    speaker_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "slide_type": self.slide_type,
            "title": self.title,
            "message": self.message,
            "elements": [e.to_dict() for e in self.elements],
            "intent": self.intent.to_dict(),
            "candidate_layout_ids": self.candidate_layout_ids,
            "selected_layout_id": self.selected_layout_id,
            "speaker_notes": self.speaker_notes,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SlideSpec":
        return cls(
            id=d.get("id", ""),
            slide_type=d.get("slide_type", ""),
            title=d.get("title", ""),
            message=d.get("message", ""),
            elements=[SlideElementSpec.from_dict(e) for e in d.get("elements", [])],
            intent=SlideIntent.from_dict(d["intent"]) if "intent" in d else SlideIntent(),
            candidate_layout_ids=d.get("candidate_layout_ids", []),
            selected_layout_id=d.get("selected_layout_id"),
            speaker_notes=d.get("speaker_notes", ""),
        )


@dataclass
class UserConstraints:
    author: str = ""
    date: str = ""
    language: str = ""
    target_slide_count: Optional[int] = None
    max_slide_count: Optional[int] = None
    template_mode: str = ""
    style_preference: str = ""
    must_include: List[str] = field(default_factory=list)
    must_exclude: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "author": self.author,
            "date": self.date,
            "language": self.language,
            "target_slide_count": self.target_slide_count,
            "max_slide_count": self.max_slide_count,
            "template_mode": self.template_mode,
            "style_preference": self.style_preference,
            "must_include": self.must_include,
            "must_exclude": self.must_exclude,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "UserConstraints":
        return cls(
            author=d.get("author", ""),
            date=d.get("date", ""),
            language=d.get("language", ""),
            target_slide_count=d.get("target_slide_count"),
            max_slide_count=d.get("max_slide_count"),
            template_mode=d.get("template_mode", ""),
            style_preference=d.get("style_preference", ""),
            must_include=d.get("must_include", []),
            must_exclude=d.get("must_exclude", []),
        )


@dataclass
class ValidationIssue:
    id: str = ""
    severity: str = ""
    slide_id: Optional[str] = None
    element_id: Optional[str] = None
    issue_type: str = ""
    message: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "slide_id": self.slide_id,
            "element_id": self.element_id,
            "issue_type": self.issue_type,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ValidationIssue":
        return cls(
            id=d.get("id", ""),
            severity=d.get("severity", ""),
            slide_id=d.get("slide_id"),
            element_id=d.get("element_id"),
            issue_type=d.get("issue_type", ""),
            message=d.get("message", ""),
            suggested_fix=d.get("suggested_fix", ""),
        )


@dataclass
class SharedState:
    user_constraints: UserConstraints = field(default_factory=UserConstraints)
    file_recognition: List[FileRecognitionResult] = field(default_factory=list)
    asset_store: AssetStore = field(default_factory=AssetStore)
    template_dna: Optional[TemplateDNA] = None
    slide_specs: List[SlideSpec] = field(default_factory=list)
    render_log: Dict[str, Any] = field(default_factory=dict)
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    quality_report: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_constraints": self.user_constraints.to_dict(),
            "file_recognition": [f.to_dict() for f in self.file_recognition],
            "asset_store": self.asset_store.to_dict(),
            "template_dna": self.template_dna.to_dict() if self.template_dna else None,
            "slide_specs": [s.to_dict() for s in self.slide_specs],
            "render_log": self.render_log,
            "validation_issues": [v.to_dict() for v in self.validation_issues],
            "quality_report": self.quality_report,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SharedState":
        return cls(
            user_constraints=UserConstraints.from_dict(d["user_constraints"]) if "user_constraints" in d else UserConstraints(),
            file_recognition=[FileRecognitionResult.from_dict(f) for f in d.get("file_recognition", [])],
            asset_store=AssetStore.from_dict(d["asset_store"]) if "asset_store" in d else AssetStore(),
            template_dna=TemplateDNA.from_dict(d["template_dna"]) if d.get("template_dna") else None,
            slide_specs=[SlideSpec.from_dict(s) for s in d.get("slide_specs", [])],
            render_log=d.get("render_log", {}),
            validation_issues=[ValidationIssue.from_dict(v) for v in d.get("validation_issues", [])],
            quality_report=d.get("quality_report", {}),
        )


@dataclass
class ChartIntent:
    intent_type: str = ""
    title: str = ""
    data_asset_ids: List[str] = field(default_factory=list)
    x_field: Optional[str] = None
    y_fields: List[str] = field(default_factory=list)
    group_field: Optional[str] = None
    highlight: Optional[str] = None
    preferred_chart_type: Optional[str] = None
    fallback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type,
            "title": self.title,
            "data_asset_ids": self.data_asset_ids,
            "x_field": self.x_field,
            "y_fields": self.y_fields,
            "group_field": self.group_field,
            "highlight": self.highlight,
            "preferred_chart_type": self.preferred_chart_type,
            "fallback": self.fallback,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ChartIntent":
        return cls(
            intent_type=d.get("intent_type", ""),
            title=d.get("title", ""),
            data_asset_ids=d.get("data_asset_ids", []),
            x_field=d.get("x_field"),
            y_fields=d.get("y_fields", []),
            group_field=d.get("group_field"),
            highlight=d.get("highlight"),
            preferred_chart_type=d.get("preferred_chart_type"),
            fallback=d.get("fallback", ""),
        )
