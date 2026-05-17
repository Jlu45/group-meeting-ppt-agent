#!/usr/bin/env python3
import sys
import json
import argparse
import os

from src.validation.visual_validator import VisualValidator
from src.validation.quality_reporter import QualityReporter
from src.common.json_io import load_json, save_json, model_to_dict
from src.common.models import TemplateDNA, ValidationIssue


def main():
    parser = argparse.ArgumentParser(description="Repair PPTX based on validation issues")
    parser.add_argument("--pptx", required=True, help="Path to input PPTX file")
    parser.add_argument("--issues", required=True, help="Path to validation issues JSON file")
    parser.add_argument("--template-dna", help="Optional path to template_dna.json for compliance repair")
    parser.add_argument("--output", "-o", help="Output repaired PPTX path (default: <input>_repaired.pptx)")
    parser.add_argument("--max-rounds", type=int, default=3, help="Maximum repair rounds")
    args = parser.parse_args()

    if not os.path.isfile(args.pptx):
        print(json.dumps({"error": f"PPTX file not found: {args.pptx}"}), file=sys.stderr)
        sys.exit(1)

    issues_data = load_json(args.issues)
    issues = []
    issue_list = issues_data if isinstance(issues_data, list) else issues_data.get("issues", issues_data.get("validation_issues", []))
    for item in issue_list:
        issues.append(ValidationIssue.from_dict(item))

    template_dna = None
    if args.template_dna and os.path.isfile(args.template_dna):
        td_data = load_json(args.template_dna)
        template_dna = TemplateDNA.from_dict(td_data)

    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(args.pptx)
        output_path = f"{base}_repaired{ext}"

    validator = VisualValidator()
    fixed_path, remaining = validator.auto_fix(args.pptx, issues, max_rounds=args.max_rounds)

    if fixed_path != output_path and os.path.isfile(fixed_path):
        import shutil
        shutil.copy2(fixed_path, output_path)

    reporter = QualityReporter()
    from pptx import Presentation
    prs = Presentation(output_path)
    slide_count = len(prs.slides)
    report = reporter.generate_report(remaining, slide_count, template_dna)

    remaining_data = [model_to_dict(i) for i in remaining]
    result = {
        "status": "ok",
        "input": args.pptx,
        "output": output_path,
        "original_issues": len(issues),
        "remaining_issues": len(remaining),
        "fixed_issues": len(issues) - len(remaining),
        "quality_report": report,
        "remaining": remaining_data,
    }

    report_path = os.path.splitext(output_path)[0] + "_report.json"
    save_json(result, report_path)

    print(json.dumps({
        "status": "ok",
        "output": output_path,
        "report": report_path,
        "fixed": len(issues) - len(remaining),
        "remaining": len(remaining),
        "overall_score": report.get("overall_score", 0),
        "grade": report.get("grade", "N/A"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
