#!/usr/bin/env python3
"""CLI: validate_pptx - Validate PPTX against template DNA"""
import sys
import json
import argparse

from src.validation.visual_validator import VisualValidator
from src.validation.quality_reporter import QualityReporter
from src.common.json_io import load_json, save_json, model_from_dict
from src.common.models import TemplateDNA


def main():
    parser = argparse.ArgumentParser(description='Validate PPTX file')
    parser.add_argument('pptx', help='Path to PPTX file to validate')
    parser.add_argument('--template-dna', help='Path to template DNA JSON')
    parser.add_argument('--output', '-o', help='Output validation report JSON')
    args = parser.parse_args()

    template_dna = None
    if args.template_dna:
        dna_data = load_json(args.template_dna)
        template_dna = TemplateDNA.from_dict(dna_data)

    validator = VisualValidator()
    issues = validator.validate(
        pptx_path=args.pptx,
        template_dna=template_dna,
    )

    from pptx import Presentation
    prs = Presentation(args.pptx)
    slide_count = len(prs.slides)

    reporter = QualityReporter()
    report = reporter.generate_report(
        issues=issues,
        slide_count=slide_count,
        template_dna=template_dna,
    )

    output_data = {
        "pptx_path": args.pptx,
        "quality_report": report,
        "issues": [i.to_dict() for i in issues],
        "issue_count": len(issues),
        "grade": report.get("grade", "N/A"),
        "overall_score": report.get("overall_score", 0),
    }

    if args.output:
        save_json(output_data, args.output)
        print(json.dumps({
            "status": "ok",
            "output": args.output,
            "grade": report.get("grade", "N/A"),
            "overall_score": report.get("overall_score", 0),
            "issue_count": len(issues),
        }), file=sys.stdout)
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2), file=sys.stdout)


if __name__ == '__main__':
    main()
