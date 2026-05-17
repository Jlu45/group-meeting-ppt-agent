import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.common.json_io import load_json, save_json, model_to_dict
from src.common.models import (
    AssetStore,
    ContentUnit,
    FileRecognitionResult,
    SharedState,
    SlideElementSpec,
    SlideIntent,
    SlideSpec,
    TemplateDNA,
    UserConstraints,
    ValidationIssue,
)
from src.recognition.file_recognizer import SmartFileRecognizer
from src.parsers.document_parser import UniversalDocumentParser
from src.assets.asset_builder import AssetBuilder
from src.template.ooxml_parser import OOXMLTemplateParser
from src.planning.density_controller import DensityController
from src.rendering.pptx_renderer import LayoutDrivenRenderer
from src.validation.visual_validator import VisualValidator
from src.validation.quality_reporter import QualityReporter

logger = logging.getLogger(__name__)

MAX_FIX_ROUNDS = 3


@dataclass
class GenerationConfig:
    author: str = ""
    date: str = ""
    output_dir: str = "./output"
    template_path: Optional[str] = None
    skip_llm: bool = False
    max_fix_rounds: int = MAX_FIX_ROUNDS


@dataclass
class GenerationResult:
    pptx_path: str
    template_dna: TemplateDNA
    state: SharedState
    duration_seconds: float = 0.0


class GroupMeetingPPTAgent:

    def __init__(self, config: Optional[GenerationConfig] = None):
        self._config = config or GenerationConfig()
        self._recognizer = SmartFileRecognizer()
        self._parser = UniversalDocumentParser()
        self._asset_builder = AssetBuilder()
        self._template_parser = OOXMLTemplateParser()
        self._density_controller = DensityController()
        self._renderer = None
        self._validator = VisualValidator()
        self._reporter = QualityReporter()

    def generate(self, input_files: list[str], config: Optional[GenerationConfig] = None) -> GenerationResult:
        start_time = time.time()
        cfg = config or self._config
        output_dir = Path(cfg.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = output_dir / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        state = SharedState(
            user_constraints=UserConstraints(
                author=cfg.author,
                date=cfg.date or datetime.now().strftime("%Y-%m-%d"),
                template_mode="fidelity",
            )
        )

        self._log("Step 1/8: 文件识别", 5)
        state.file_recognition = self._step_file_recognition(input_files)
        save_json({"files": [model_to_dict(r) for r in state.file_recognition]}, str(cache_dir / "file_recognition.json"))

        self._log("Step 2/8: 文档解析", 15)
        parsed_docs = self._step_document_parsing(input_files)
        save_json(parsed_docs, str(cache_dir / "parsed_documents.json"))

        self._log("Step 3/8: 资产构建", 25)
        state.asset_store = self._step_asset_building(state.file_recognition, parsed_docs)
        save_json(model_to_dict(state.asset_store), str(cache_dir / "asset_store.json"))

        self._log("Step 4/8: 模板DNA提取", 35)
        state.template_dna = self._step_template_dna(cfg.template_path)
        save_json(model_to_dict(state.template_dna), str(cache_dir / "template_dna.json"))

        self._log("Step 5/8: 幻灯片规划（规则引擎）", 45)
        state.slide_specs = self._step_slide_planning(state.asset_store, state.user_constraints, state.template_dna)
        save_json({"slides": [model_to_dict(s) for s in state.slide_specs]}, str(cache_dir / "slide_spec.json"))

        self._log("Step 6/8: 密度控制", 60)
        state.slide_specs = self._density_controller.control(state.slide_specs, state.template_dna)
        save_json({"slides": [model_to_dict(s) for s in state.slide_specs]}, str(cache_dir / "slide_spec_controlled.json"))

        self._log("Step 7/8: 渲染PPTX", 70)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title_text = self._derive_title(state.asset_store, state.user_constraints)
        safe_title = "".join(c for c in title_text if c.isalnum() or c in "._- ")[:30]
        output_filename = f"{safe_title}_{timestamp}.pptx"
        output_path = str(output_dir / output_filename)

        self._renderer = LayoutDrivenRenderer(state.template_dna)
        state.render_log = self._renderer.render(state.slide_specs, output_path, state.asset_store)

        self._log("Step 8/8: 验证与质量报告", 85)
        state.validation_issues = self._validator.validate(output_path, state.template_dna, state.slide_specs)
        state.quality_report = self._reporter.generate_report(state.validation_issues, len(state.slide_specs), state.template_dna)
        save_json(model_to_dict(state.quality_report), str(cache_dir / "quality_report.json"))

        if state.validation_issues:
            critical = [i for i in state.validation_issues if i.severity in ("critical", "error")]
            if critical and cfg.max_fix_rounds > 0:
                self._log(f"发现 {len(critical)} 个严重问题，尝试自动修复...", 90)
                fixed_path, remaining = self._validator.auto_fix(
                    output_path, state.validation_issues, max_rounds=cfg.max_fix_rounds
                )
                if os.path.isfile(fixed_path):
                    output_path = fixed_path
                    state.validation_issues = remaining
                    state.quality_report = self._reporter.generate_report(
                        remaining, len(state.slide_specs), state.template_dna
                    )
                    save_json(model_to_dict(state.quality_report), str(cache_dir / "quality_report.json"))

        duration = time.time() - start_time
        self._log(f"完成！耗时 {duration:.1f}s", 100)

        return GenerationResult(
            pptx_path=output_path,
            template_dna=state.template_dna,
            state=state,
            duration_seconds=duration,
        )

    def _step_file_recognition(self, input_files: list[str]) -> list[FileRecognitionResult]:
        return self._recognizer.recognize(input_files)

    def _step_document_parsing(self, input_files: list[str]) -> dict:
        documents = []
        for fp in input_files:
            try:
                doc = self._parser.parse(fp)
                documents.append({
                    "source_path": doc.source_path,
                    "file_type": doc.file_type,
                    "markdown_content": doc.markdown_content,
                    "content_length": len(doc.markdown_content),
                })
            except Exception as e:
                logger.error(f"Failed to parse {fp}: {e}")
        return {"documents": documents, "total": len(documents)}

    def _step_asset_building(self, file_recognition: list[FileRecognitionResult], parsed_docs: dict) -> AssetStore:
        stores = []
        doc_list = parsed_docs.get("documents", [])
        frec_map = {r.path: r for r in file_recognition}

        for doc in doc_list:
            source_path = doc.get("source_path", "")
            frec = frec_map.get(source_path)
            if frec is None:
                frec = FileRecognitionResult(
                    id=f"frec-{uuid.uuid4().hex[:8]}",
                    path=source_path,
                    filename=Path(source_path).name,
                    extension=Path(source_path).suffix.lower(),
                    base_type="document",
                    confidence=0.5,
                )
            markdown = doc.get("markdown_content", "")
            store = self._asset_builder.build_from_parsed(frec, markdown)
            stores.append(store)

        if not stores:
            return AssetStore()
        return self._asset_builder.merge_stores(stores)

    def _step_template_dna(self, template_path: Optional[str]) -> TemplateDNA:
        if template_path and Path(template_path).exists():
            return self._template_parser.parse(template_path)
        default_template = Path(__file__).parent / "templates" / "default_academic.pptx"
        if default_template.exists():
            return self._template_parser.parse(str(default_template))
        return TemplateDNA()

    def _step_slide_planning(self, asset_store: AssetStore, constraints: UserConstraints, template_dna: TemplateDNA) -> list[SlideSpec]:
        specs = []
        layout_ids = [l.id for l in template_dna.layouts] if template_dna.layouts else []

        specs.append(self._make_cover_slide(asset_store, constraints, layout_ids))

        top_units = asset_store.top_units(5)
        if top_units:
            specs.append(self._make_overview_slide(top_units, layout_ids))

        kind_groups = self._group_units_by_kind(asset_store)
        for kind, units in kind_groups.items():
            for unit in units:
                specs.append(self._make_body_slide(unit, kind, layout_ids))

        claim_units = [u for u in asset_store.content_units.values() if u.kind == "claim"]
        if claim_units:
            specs.append(self._make_summary_slide(claim_units, layout_ids))

        next_step_units = [u for u in asset_store.content_units.values() if u.kind == "next_step"]
        if next_step_units:
            specs.append(self._make_discussion_slide(next_step_units, layout_ids))

        if len(specs) < 2:
            specs.append(self._make_fallback_slide(asset_store, layout_ids))

        return specs

    def _make_cover_slide(self, asset_store: AssetStore, constraints: UserConstraints, layout_ids: list[str]) -> SlideSpec:
        title = self._derive_title(asset_store, constraints)
        subtitle_parts = []
        if constraints.author:
            subtitle_parts.append(f"汇报人: {constraints.author}")
        if constraints.date:
            subtitle_parts.append(constraints.date)
        subtitle = " | ".join(subtitle_parts)

        candidates = self._pick_layout_candidates(layout_ids, "cover")

        return SlideSpec(
            id=f"slide-{uuid.uuid4().hex[:8]}",
            slide_type="cover",
            title=title,
            message="封面",
            elements=[
                SlideElementSpec(role="title", content=title, required=True, visual_weight=10),
                SlideElementSpec(role="subtitle", content=subtitle, required=False, visual_weight=5),
            ],
            intent=SlideIntent(
                slide_type="cover",
                content_roles=["slide_title", "cover_title", "subtitle"],
                density="sparse",
                preferred_layout="cover",
                must_have=["title"],
            ),
            candidate_layout_ids=candidates,
        )

    def _make_overview_slide(self, top_units: list[ContentUnit], layout_ids: list[str]) -> SlideSpec:
        points = [f"{u.title}: {u.summary[:60]}" for u in top_units if u.title]
        candidates = self._pick_layout_candidates(layout_ids, "bullet_list")

        return SlideSpec(
            id=f"slide-{uuid.uuid4().hex[:8]}",
            slide_type="overview",
            title="内容概览",
            message="本次汇报的主要内容",
            elements=[
                SlideElementSpec(role="title", content="内容概览", required=True, visual_weight=8),
                SlideElementSpec(role="key_points", content=points, required=True, visual_weight=7),
            ],
            intent=SlideIntent(
                slide_type="overview",
                content_roles=["slide_title", "body_text"],
                density="normal",
                preferred_layout="bullet_list",
                must_have=["title", "key_points"],
            ),
            candidate_layout_ids=candidates,
        )

    def _make_body_slide(self, unit: ContentUnit, kind: str, layout_ids: list[str]) -> SlideSpec:
        details = unit.details[:6] if unit.details else [unit.summary[:80]] if unit.summary else []
        candidates = self._pick_layout_candidates(layout_ids, "bullet_list")

        figure_ids = [fid for fid, fig in [] if fid in []]
        has_figure = False

        slide_type = self._kind_to_slide_type(kind)

        return SlideSpec(
            id=f"slide-{uuid.uuid4().hex[:8]}",
            slide_type=slide_type,
            title=unit.title[:40] if unit.title else kind,
            message=unit.summary[:100] if unit.summary else "",
            elements=[
                SlideElementSpec(role="title", content=unit.title[:40] if unit.title else kind, required=True, visual_weight=8),
                SlideElementSpec(role="key_points", content=details, required=True, visual_weight=7, asset_ids=unit.evidence_ids),
            ],
            intent=SlideIntent(
                slide_type=slide_type,
                content_roles=["slide_title", "body_text"],
                density="normal",
                preferred_layout="bullet_list",
                must_have=["title", "key_points"],
            ),
            candidate_layout_ids=candidates,
            speaker_notes=unit.summary if unit.summary else "",
        )

    def _make_summary_slide(self, claim_units: list[ContentUnit], layout_ids: list[str]) -> SlideSpec:
        points = [u.summary[:80] if u.summary else u.title for u in claim_units[:6]]
        candidates = self._pick_layout_candidates(layout_ids, "bullet_list")

        return SlideSpec(
            id=f"slide-{uuid.uuid4().hex[:8]}",
            slide_type="summary",
            title="总结",
            message="核心结论与贡献",
            elements=[
                SlideElementSpec(role="title", content="总结", required=True, visual_weight=8),
                SlideElementSpec(role="key_points", content=points, required=True, visual_weight=7),
            ],
            intent=SlideIntent(
                slide_type="summary",
                content_roles=["slide_title", "body_text"],
                density="normal",
                preferred_layout="bullet_list",
                must_have=["title", "key_points"],
            ),
            candidate_layout_ids=candidates,
        )

    def _make_discussion_slide(self, next_step_units: list[ContentUnit], layout_ids: list[str]) -> SlideSpec:
        points = [u.summary[:80] if u.summary else u.title for u in next_step_units[:6]]
        candidates = self._pick_layout_candidates(layout_ids, "bullet_list")

        return SlideSpec(
            id=f"slide-{uuid.uuid4().hex[:8]}",
            slide_type="discussion",
            title="讨论与展望",
            message="下一步计划",
            elements=[
                SlideElementSpec(role="title", content="讨论与展望", required=True, visual_weight=8),
                SlideElementSpec(role="key_points", content=points, required=True, visual_weight=7),
            ],
            intent=SlideIntent(
                slide_type="discussion",
                content_roles=["slide_title", "body_text"],
                density="normal",
                preferred_layout="bullet_list",
                must_have=["title", "key_points"],
            ),
            candidate_layout_ids=candidates,
        )

    def _make_fallback_slide(self, asset_store: AssetStore, layout_ids: list[str]) -> SlideSpec:
        all_details = []
        for unit in asset_store.content_units.values():
            all_details.extend(unit.details[:3])
        candidates = self._pick_layout_candidates(layout_ids, "bullet_list")

        return SlideSpec(
            id=f"slide-{uuid.uuid4().hex[:8]}",
            slide_type="content",
            title="主要内容",
            message="",
            elements=[
                SlideElementSpec(role="title", content="主要内容", required=True, visual_weight=8),
                SlideElementSpec(role="key_points", content=all_details[:6], required=True, visual_weight=7),
            ],
            intent=SlideIntent(
                slide_type="content",
                content_roles=["slide_title", "body_text"],
                density="normal",
                preferred_layout="bullet_list",
                must_have=["title", "key_points"],
            ),
            candidate_layout_ids=candidates,
        )

    def _group_units_by_kind(self, asset_store: AssetStore) -> dict[str, list[ContentUnit]]:
        groups: dict[str, list[ContentUnit]] = {}
        for unit in asset_store.content_units.values():
            kind = unit.kind or "claim"
            groups.setdefault(kind, []).append(unit)
        for kind in groups:
            groups[kind].sort(key=lambda u: u.priority, reverse=True)
        return groups

    def _kind_to_slide_type(self, kind: str) -> str:
        mapping = {
            "method": "method",
            "result": "result",
            "background": "background",
            "limitation": "discussion",
            "next_step": "discussion",
            "claim": "summary",
        }
        return mapping.get(kind, "content")

    def _pick_layout_candidates(self, layout_ids: list[str], layout_type: str) -> list[str]:
        if not layout_ids:
            return []
        type_prefix_map = {
            "cover": ["cover", "title"],
            "section": ["section"],
            "bullet_list": ["content", "title"],
            "two_column": ["two", "content"],
            "blank": ["blank"],
        }
        prefixes = type_prefix_map.get(layout_type, ["content"])
        candidates = [lid for lid in layout_ids if any(p in lid.lower() for p in prefixes)]
        if not candidates:
            candidates = layout_ids[:3]
        return candidates

    def _derive_title(self, asset_store: AssetStore, constraints: UserConstraints) -> str:
        if constraints.author:
            return f"{constraints.author} 组会汇报"
        for unit in asset_store.top_units(1):
            if unit.title:
                return unit.title[:40]
        return "组会汇报"

    def _log(self, message: str, percent: float):
        logger.info(f"[{percent:.0f}%] {message}")
        print(f"[{percent:.0f}%] {message}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="组会PPT自动制作智能体")
    parser.add_argument("input_files", nargs="+", help="输入文件路径")
    parser.add_argument("-t", "--template", help="模板PPTX路径", default=None)
    parser.add_argument("-a", "--author", help="汇报人", default="")
    parser.add_argument("-d", "--date", help="日期", default="")
    parser.add_argument("-o", "--output-dir", help="输出目录", default="./output")
    parser.add_argument("--skip-llm", action="store_true", help="跳过LLM调用（仅规则引擎，默认行为）")
    parser.add_argument("--api-key", help="OpenAI API Key（已弃用，保留兼容）", default=None)
    parser.add_argument("--model", help="LLM模型（已弃用，保留兼容）", default="gpt-4o")
    parser.add_argument("--outline-only", action="store_true", help="仅输出大纲")
    parser.add_argument("--max-fix-rounds", type=int, default=MAX_FIX_ROUNDS, help="最大修复轮数")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    config = GenerationConfig(
        author=args.author,
        date=args.date,
        output_dir=args.output_dir,
        template_path=args.template,
        skip_llm=True,
        max_fix_rounds=args.max_fix_rounds,
    )

    agent = GroupMeetingPPTAgent(config=config)

    if args.outline_only:
        state = SharedState(
            user_constraints=UserConstraints(
                author=args.author,
                date=args.date or datetime.now().strftime("%Y-%m-%d"),
            )
        )
        state.file_recognition = agent._step_file_recognition(args.input_files)
        parsed_docs = agent._step_document_parsing(args.input_files)
        state.asset_store = agent._step_asset_building(state.file_recognition, parsed_docs)
        state.template_dna = agent._step_template_dna(config.template_path)
        state.slide_specs = agent._step_slide_planning(state.asset_store, state.user_constraints, state.template_dna)

        print(f"标题: {agent._derive_title(state.asset_store, state.user_constraints)}")
        print(f"共 {len(state.slide_specs)} 页")
        print()
        for i, spec in enumerate(state.slide_specs, 1):
            print(f"第{i}页: {spec.title} [{spec.slide_type}]")
            for elem in spec.elements:
                if elem.role == "key_points" and elem.content:
                    items = elem.content if isinstance(elem.content, list) else [elem.content]
                    for item in items[:4]:
                        print(f"  - {item}")
            print()
    else:
        result = agent.generate(args.input_files, config)
        print(f"\n生成完成！")
        print(f"  文件: {result.pptx_path}")
        print(f"  页数: {len(result.state.slide_specs)}")
        print(f"  耗时: {result.duration_seconds:.1f}s")

        report = result.state.quality_report
        if report:
            print(f"\n  综合评分: {report.get('overall_score', 0)} / 100  [{report.get('grade', 'N/A')}]")
            print(f"  L1 结构完整性: {report.get('structure_score', 100):.1f}")
            print(f"  L2 布局合理性: {report.get('layout_score', 100):.1f}")
            print(f"  L3 模板合规性: {report.get('compliance_score', 100):.1f}")
            print(f"  L4 内容完整性: {report.get('content_score', 100):.1f}")

        if result.state.validation_issues:
            print(f"\n  验证问题 ({len(result.state.validation_issues)}):")
            for issue in result.state.validation_issues[:5]:
                print(f"    [{issue.severity}] {issue.message}")


if __name__ == "__main__":
    main()
