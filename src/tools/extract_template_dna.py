#!/usr/bin/env python3
"""CLI: extract_template_dna - Extract template DNA from PPTX"""
import sys
import json
import argparse

from src.template.ooxml_parser import OOXMLTemplateParser
from src.common.json_io import save_json, model_to_dict


def main():
    parser = argparse.ArgumentParser(description='Extract template DNA from PPTX')
    parser.add_argument('template', help='Path to PPTX template file')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    args = parser.parse_args()

    ooxml_parser = OOXMLTemplateParser()
    template_dna = ooxml_parser.parse(args.template)

    output_data = model_to_dict(template_dna)
    output_data["source_path"] = args.template

    layout_summary = []
    for layout in template_dna.layouts:
        layout_summary.append({
            "id": layout.id,
            "name": layout.name,
            "layout_type": layout.layout_type,
            "placeholder_count": len(layout.placeholders),
            "tags": layout.tags,
        })

    output_data["layout_summary"] = layout_summary

    if args.output:
        save_json(output_data, args.output)
        print(json.dumps({
            "status": "ok",
            "output": args.output,
            "layouts": len(template_dna.layouts),
            "masters": len(template_dna.masters),
        }), file=sys.stdout)
    else:
        save_json(output_data, "__stdout__.json")
        with open("__stdout__.json", "r", encoding="utf-8") as f:
            print(f.read())


if __name__ == '__main__':
    main()
