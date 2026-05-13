import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from src.models import (
    TemplateDNA, StructuredPresentation, ValidationResult, ComplianceReport,
)
from src.parsers.document_parser import UniversalDocumentParser
from src.parsers.template_extractor import TemplateDNAExtractor
from src.parsers.content_structurer import ContentStructuringEngine
from src.agents.planner import PlannerAgent
from src.agents.generator import GeneratorAgent
from src.agents.refiner import RefinerAgent
from src.agents.validator import ValidatorAgent
from src.generators.pptx_builder import PPTXBuilder
from src.generators.chart_generator import ChartGenerator
from src.generators.style_lock import StyleLockEngine
from src.generators.layout_engine import LayoutEngine

logger = logging.getLogger(__name__)

MAX_FIX_ROUNDS = 3


@dataclass
class GenerationConfig:
    author: str = ""
    date: str = ""
    output_dir: str = "./output"
    template_path: Optional[str] = None
    llm_model: str = "gpt-4o"
    use_docling: bool = False
    max_fix_rounds: int = MAX_FIX_ROUNDS
    skip_llm: bool = False


@dataclass
class GenerationResult:
    pptx_path: str
    template_dna: TemplateDNA
    presentation: StructuredPresentation
    validation: ValidationResult
    compliance: Optional[ComplianceReport] = None
    duration_seconds: float = 0.0


class GroupMeetingPPTAgent:
    """组会PPT自动制作智能体 - 主入口"""

    def __init__(self, llm_client=None, config: Optional[GenerationConfig] = None):
        self._llm_client = llm_client
        self._config = config or GenerationConfig()

        self._parser = UniversalDocumentParser(use_docling=self._config.use_docling)
        self._template_extractor = TemplateDNAExtractor()
        self._structurer = ContentStructuringEngine(
            llm_client=llm_client if not self._config.skip_llm else None,
            model=self._config.llm_model,
        )
        self._planner = PlannerAgent(
            llm_client=llm_client if not self._config.skip_llm else None,
            model=self._config.llm_model,
        )
        self._generator = GeneratorAgent(
            llm_client=llm_client if not self._config.skip_llm else None,
            model=self._config.llm_model,
        )
        self._refiner = RefinerAgent(
            llm_client=llm_client if not self._config.skip_llm else None,
            model=self._config.llm_model,
        )
        self._chart_generator = None
        self._style_lock = None
        self._layout_engine = None

        self._on_progress: Optional[Callable[[str, float], None]] = None

    def on_progress(self, callback: Callable[[str, float], None]):
        self._on_progress = callback

    def _emit_progress(self, message: str, percent: float):
        logger.info(f"[{percent:.0f}%] {message}")
        if self._on_progress:
            self._on_progress(message, percent)

    def generate(self, input_files: list[str], config: Optional[GenerationConfig] = None) -> GenerationResult:
        import time
        start_time = time.time()

        cfg = config or self._config
        output_dir = Path(cfg.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self._emit_progress("Phase 1: 输入与解析", 5)

        template_dna = self._extract_template(cfg)
        self._chart_generator = ChartGenerator(template_dna)
        self._style_lock = StyleLockEngine(template_dna)
        self._layout_engine = LayoutEngine(template_dna)

        self._emit_progress("解析文档...", 15)
        parsed_docs = self._parser.parse_multiple(input_files)
        if not parsed_docs:
            raise ValueError("No documents could be parsed")

        merged_doc = self._parser.merge_documents(parsed_docs)

        self._emit_progress("LLM内容结构化...", 25)
        presentation = self._structurer.structure(
            merged_doc, author=cfg.author, date=cfg.date
        )

        self._emit_progress("Phase 2: 智能规划", 35)
        presentation = self._planner.plan(presentation, template_dna)

        self._emit_progress("Phase 3: 生成与优化", 50)
        presentation = self._generator.generate(presentation, template_dna)

        self._emit_progress("内容优化...", 65)
        presentation = self._refiner.refine(presentation, template_dna)

        validator = ValidatorAgent(template_dna)
        presentation = validator.auto_fix(presentation, max_rounds=cfg.max_fix_rounds)

        self._emit_progress("构建PPTX...", 75)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in presentation.title if c.isalnum() or c in "._- ")[:30]
        output_filename = f"{safe_title}_{timestamp}.pptx"
        output_path = str(output_dir / output_filename)

        builder = PPTXBuilder(template_dna=template_dna, template_path=cfg.template_path, chart_generator=self._chart_generator)
        builder.build(presentation, output_path)

        self._emit_progress("样式锁定...", 85)
        self._style_lock.apply(output_path)

        self._emit_progress("Phase 4: 验证与交付", 90)
        validation = validator.validate_pptx(output_path)
        compliance = self._style_lock.validate_compliance(output_path)

        if not validation.all_passed:
            self._emit_progress("验证未完全通过，尝试修复...", 93)
            self._attempt_auto_fix(output_path, validation, cfg)

        duration = time.time() - start_time
        self._emit_progress(f"完成！模板遵循度: {compliance.overall_score:.0%}", 100)

        return GenerationResult(
            pptx_path=output_path,
            template_dna=template_dna,
            presentation=presentation,
            validation=validation,
            compliance=compliance,
            duration_seconds=duration,
        )

    def _extract_template(self, cfg: GenerationConfig) -> TemplateDNA:
        if cfg.template_path and Path(cfg.template_path).exists():
            self._emit_progress(f"提取模板DNA: {cfg.template_path}", 10)
            return self._template_extractor.extract(cfg.template_path)
        else:
            self._emit_progress("使用默认学术模板", 10)
            return TemplateDNA()

    def _attempt_auto_fix(self, pptx_path: str, validation: ValidationResult, cfg: GenerationConfig):
        p0_issues = [i for i in validation.issues if i["level"] == "P0"]
        if not p0_issues:
            return

        logger.warning(f"Found {len(p0_issues)} P0 issues, attempting auto-fix")

    def get_outline(self, input_files: list[str], config: Optional[GenerationConfig] = None) -> StructuredPresentation:
        cfg = config or self._config

        parsed_docs = self._parser.parse_multiple(input_files)
        if not parsed_docs:
            raise ValueError("No documents could be parsed")

        merged_doc = self._parser.merge_documents(parsed_docs)
        presentation = self._structurer.structure(
            merged_doc, author=cfg.author, date=cfg.date
        )

        template_dna = self._extract_template(cfg)
        presentation = self._planner.plan(presentation, template_dna)

        return presentation

    def format_outline(self, presentation: StructuredPresentation) -> str:
        lines = []
        lines.append(f"标题: {presentation.title}")
        lines.append(f"类型: {presentation.doc_type.value}")
        lines.append(f"概述: {presentation.summary}")
        lines.append(f"共 {len(presentation.slides)} 页")
        lines.append("")

        for i, slide in enumerate(presentation.slides, 1):
            lines.append(f"第{i}页: {slide.title} [{slide.layout.value}]")
            for p in slide.points:
                lines.append(f"  - {p}")
            if slide.chart_desc:
                lines.append(f"  [图表: {slide.chart_desc}]")
            lines.append("")

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="组会PPT自动制作智能体")
    parser.add_argument("input_files", nargs="+", help="输入文件路径")
    parser.add_argument("-t", "--template", help="模板PPTX路径", default=None)
    parser.add_argument("-a", "--author", help="汇报人", default="")
    parser.add_argument("-d", "--date", help="日期", default="")
    parser.add_argument("-o", "--output-dir", help="输出目录", default="./output")
    parser.add_argument("--api-key", help="OpenAI API Key", default=None)
    parser.add_argument("--model", help="LLM模型", default="gpt-4o")
    parser.add_argument("--skip-llm", action="store_true", help="跳过LLM调用（仅规则引擎）")
    parser.add_argument("--outline-only", action="store_true", help="仅输出大纲")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    llm_client = None
    if not args.skip_llm and args.api_key:
        from openai import OpenAI
        llm_client = OpenAI(api_key=args.api_key)

    config = GenerationConfig(
        author=args.author,
        date=args.date,
        output_dir=args.output_dir,
        template_path=args.template,
        llm_model=args.model,
        skip_llm=args.skip_llm,
    )

    agent = GroupMeetingPPTAgent(llm_client=llm_client, config=config)

    if args.outline_only:
        presentation = agent.get_outline(args.input_files, config)
        print(agent.format_outline(presentation))
    else:
        result = agent.generate(args.input_files, config)
        print(f"\n生成完成！")
        print(f"  文件: {result.pptx_path}")
        print(f"  页数: {len(result.presentation.slides)}")
        print(f"  模板遵循度: {result.compliance.overall_score:.0%}" if result.compliance else "  模板遵循度: N/A")
        print(f"  耗时: {result.duration_seconds:.1f}s")

        if result.validation.issues:
            print(f"\n  验证问题 ({len(result.validation.issues)}):")
            for issue in result.validation.issues[:5]:
                print(f"    [{issue['level']}] {issue['message']}")


if __name__ == "__main__":
    main()
