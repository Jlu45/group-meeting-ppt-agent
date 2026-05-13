import logging
from typing import Optional

from src.models import (
    StructuredPresentation, SlidePlan, LayoutType, TemplateDNA,
    ValidationResult, ComplianceReport,
)
from src.validators.layout_validator import LayoutValidator
from src.validators.compliance_checker import ComplianceChecker
from src.validators.content_checker import ContentChecker

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """验证智能体 - 布局验证、模板检查、内容完整性"""

    def __init__(self, template_dna: Optional[TemplateDNA] = None):
        self._template_dna = template_dna
        self._layout_validator = LayoutValidator()
        self._compliance_checker = ComplianceChecker(template_dna)
        self._content_checker = ContentChecker()

    def validate_structure(self, presentation: StructuredPresentation) -> ValidationResult:
        issues = []

        if not presentation.slides:
            issues.append({"level": "P0", "message": "No slides in presentation"})
            return ValidationResult(issues=issues)

        cover = presentation.slides[0]
        if cover.layout != LayoutType.COVER:
            issues.append({"level": "P1", "message": "First slide is not a cover"})

        if len(presentation.slides) >= 3:
            has_summary = any(
                s.layout == LayoutType.SUMMARY or "总结" in s.title
                for s in presentation.slides[-3:]
            )
            if not has_summary:
                issues.append({"level": "P1", "message": "Missing summary slide"})

            has_discussion = any(
                s.layout == LayoutType.DISCUSSION or "讨论" in s.title
                for s in presentation.slides[-2:]
            )
            if not has_discussion:
                issues.append({"level": "P2", "message": "Missing discussion slide"})

        for i, slide in enumerate(presentation.slides):
            if not slide.title.strip():
                issues.append({"level": "P1", "message": f"Slide {i + 1} has no title"})

            if slide.layout not in (LayoutType.COVER, LayoutType.TABLE, LayoutType.IMAGE_GRID):
                if not slide.points and not slide.chart_desc:
                    issues.append({"level": "P2", "message": f"Slide {i + 1} '{slide.title}' has no content"})

            if len(slide.points) > 6:
                issues.append({"level": "P2", "message": f"Slide {i + 1} '{slide.title}' has too many points ({len(slide.points)})"})

        level1_passed = not any(i["level"] == "P0" for i in issues)
        return ValidationResult(
            level1_passed=level1_passed,
            issues=issues,
        )

    def validate_pptx(self, pptx_path: str) -> ValidationResult:
        issues = []

        layout_issues = self._layout_validator.validate(pptx_path)
        issues.extend(layout_issues)

        level1_passed = not any(i["level"] == "P0" for i in issues)

        compliance = self._compliance_checker.check(pptx_path)
        level2_passed = compliance.passed

        content_issues = self._content_checker.check(pptx_path)
        issues.extend(content_issues)
        level3_passed = not any(i["level"] == "P0" for i in content_issues)

        return ValidationResult(
            level1_passed=level1_passed,
            level2_passed=level2_passed,
            level3_passed=level3_passed,
            issues=issues,
            compliance=compliance,
        )

    def auto_fix(self, presentation: StructuredPresentation, max_rounds: int = 3) -> StructuredPresentation:
        for round_num in range(max_rounds):
            result = self.validate_structure(presentation)
            if result.all_passed:
                logger.info(f"Validation passed at round {round_num + 1}")
                break

            p0_issues = [i for i in result.issues if i["level"] == "P0"]
            p1_issues = [i for i in result.issues if i["level"] == "P1"]

            if not p0_issues and not p1_issues:
                logger.info(f"Only P2 issues remain at round {round_num + 1}")
                break

            presentation = self._apply_fixes(presentation, result.issues)
            logger.info(f"Applied fixes at round {round_num + 1}")

        return presentation

    def _apply_fixes(self, presentation: StructuredPresentation, issues: list) -> StructuredPresentation:
        for issue in issues:
            msg = issue["message"]
            level = issue["level"]

            if "First slide is not a cover" in msg:
                if presentation.slides and presentation.slides[0].layout != LayoutType.COVER:
                    presentation.slides.insert(0, SlidePlan(
                        title=presentation.title, layout=LayoutType.COVER, points=[]
                    ))

            elif "Missing summary slide" in msg:
                presentation.slides.insert(
                    -1,
                    SlidePlan(title="总结", layout=LayoutType.SUMMARY, points=["待补充"])
                )

            elif "Missing discussion slide" in msg:
                presentation.slides.append(
                    SlidePlan(title="讨论与下一步", layout=LayoutType.DISCUSSION, points=["待补充"])
                )

            elif "has no title" in msg:
                import re
                match = re.search(r"Slide (\d+)", msg)
                if match:
                    idx = int(match.group(1)) - 1
                    if 0 <= idx < len(presentation.slides):
                        presentation.slides[idx].title = f"内容 {idx + 1}"

            elif "has too many points" in msg:
                import re
                match = re.search(r"Slide (\d+)", msg)
                if match:
                    idx = int(match.group(1)) - 1
                    if 0 <= idx < len(presentation.slides):
                        presentation.slides[idx].points = presentation.slides[idx].points[:6]

        return presentation
