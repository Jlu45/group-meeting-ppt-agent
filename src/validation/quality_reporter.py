from src.common.models import ValidationIssue, TemplateDNA


class QualityReporter:
    WEIGHTS = {
        "structure": 0.30,
        "layout": 0.30,
        "compliance": 0.20,
        "content": 0.20,
    }

    SEVERITY_PENALTY = {
        "critical": 25,
        "error": 15,
        "warning": 8,
        "info": 3,
    }

    ISSUE_TYPE_LEVEL = {
        "structure": "structure",
        "blank_slide": "structure",
        "missing_title": "structure",
        "text_overflow": "layout",
        "element_overlap": "layout",
        "margin_violation": "layout",
        "font_too_small": "layout",
        "font_mismatch": "compliance",
        "color_mismatch": "compliance",
        "placeholder_text": "content",
        "incomplete_content": "content",
    }

    def generate_report(self, issues: list[ValidationIssue], slide_count: int,
                        template_dna: TemplateDNA = None) -> dict:
        level_issues = {"structure": [], "layout": [], "compliance": [], "content": []}
        for issue in issues:
            level = self.ISSUE_TYPE_LEVEL.get(issue.issue_type, "content")
            level_issues[level].append(issue)

        scores = {}
        for level, level_list in level_issues.items():
            penalty = sum(self.SEVERITY_PENALTY.get(i.severity, 5) for i in level_list)
            score = max(0, 100 - penalty)
            scores[f"{level}_score"] = score

        overall = sum(
            scores.get(f"{level}_score", 100) * weight
            for level, weight in self.WEIGHTS.items()
        )
        overall = round(overall, 1)

        issue_summary = {
            "total": len(issues),
            "by_severity": {},
            "by_level": {},
            "by_type": {},
        }
        for issue in issues:
            issue_summary["by_severity"][issue.severity] = (
                issue_summary["by_severity"].get(issue.severity, 0) + 1
            )
            level = self.ISSUE_TYPE_LEVEL.get(issue.issue_type, "content")
            issue_summary["by_level"][level] = (
                issue_summary["by_level"].get(level, 0) + 1
            )
            issue_summary["by_type"][issue.issue_type] = (
                issue_summary["by_type"].get(issue.issue_type, 0) + 1
            )

        grade = "A"
        if overall < 60:
            grade = "D"
        elif overall < 70:
            grade = "C"
        elif overall < 85:
            grade = "B"

        return {
            "structure_score": scores.get("structure_score", 100),
            "layout_score": scores.get("layout_score", 100),
            "compliance_score": scores.get("compliance_score", 100),
            "content_score": scores.get("content_score", 100),
            "overall_score": overall,
            "grade": grade,
            "slide_count": slide_count,
            "issue_summary": issue_summary,
        }

    def format_report(self, report: dict) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("          PPT 质量检测报告")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"  幻灯片数量: {report.get('slide_count', 0)}")
        lines.append(f"  综合评分:   {report.get('overall_score', 0)} / 100  [{report.get('grade', 'N/A')}]")
        lines.append("")
        lines.append("-" * 50)
        lines.append("  分项评分:")
        lines.append("-" * 50)
        lines.append(f"  L1 结构完整性: {report.get('structure_score', 100):>6.1f} / 100")
        lines.append(f"  L2 布局合理性: {report.get('layout_score', 100):>6.1f} / 100")
        lines.append(f"  L3 模板合规性: {report.get('compliance_score', 100):>6.1f} / 100")
        lines.append(f"  L4 内容完整性: {report.get('content_score', 100):>6.1f} / 100")
        lines.append("")

        summary = report.get("issue_summary", {})
        lines.append("-" * 50)
        lines.append("  问题统计:")
        lines.append("-" * 50)
        lines.append(f"  问题总数: {summary.get('total', 0)}")

        by_severity = summary.get("by_severity", {})
        if by_severity:
            lines.append("")
            lines.append("  按严重程度:")
            for sev in ("critical", "error", "warning", "info"):
                count = by_severity.get(sev, 0)
                if count > 0:
                    lines.append(f"    {sev:>8}: {count}")

        by_level = summary.get("by_level", {})
        if by_level:
            lines.append("")
            lines.append("  按检测层级:")
            level_names = {"structure": "L1结构", "layout": "L2布局", "compliance": "L3合规", "content": "L4内容"}
            for level, count in by_level.items():
                lines.append(f"    {level_names.get(level, level):>8}: {count}")

        by_type = summary.get("by_type", {})
        if by_type:
            lines.append("")
            lines.append("  按问题类型:")
            for itype, count in by_type.items():
                lines.append(f"    {itype:>20}: {count}")

        lines.append("")
        lines.append("=" * 50)
        return "\n".join(lines)
