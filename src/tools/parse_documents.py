#!/usr/bin/env python3
"""CLI: parse_documents - Parse documents to markdown"""
import sys
import json
import argparse

from src.parsers.document_parser import UniversalDocumentParser
from src.common.json_io import save_json


def main():
    parser = argparse.ArgumentParser(description='Parse documents to markdown')
    parser.add_argument('files', nargs='+', help='File paths to parse')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    args = parser.parse_args()

    doc_parser = UniversalDocumentParser()
    results = []
    errors = []

    for fp in args.files:
        try:
            doc = doc_parser.parse(fp)
            results.append({
                "source_path": doc.source_path,
                "file_type": doc.file_type,
                "markdown_content": doc.markdown_content,
                "content_length": len(doc.markdown_content),
            })
        except Exception as e:
            errors.append({"path": fp, "error": str(e)})

    output_data = {
        "documents": results,
        "total": len(results),
        "errors": errors,
    }

    if args.output:
        save_json(output_data, args.output)
        print(json.dumps({"status": "ok", "output": args.output, "total": len(results)}), file=sys.stdout)
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2), file=sys.stdout)


if __name__ == '__main__':
    main()
