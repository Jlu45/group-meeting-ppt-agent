#!/usr/bin/env python3
"""CLI: recognize_files - Identify file types and PPT purposes"""
import sys
import json
import argparse

from src.recognition.file_recognizer import SmartFileRecognizer
from src.common.json_io import save_json, model_to_dict


def main():
    parser = argparse.ArgumentParser(description='Recognize file types for PPT generation')
    parser.add_argument('files', nargs='*', help='File paths to recognize')
    parser.add_argument('--input-json', help='JSON file containing file paths array')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    args = parser.parse_args()

    file_paths = list(args.files)

    if args.input_json:
        with open(args.input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            file_paths.extend(data)
        elif isinstance(data, dict) and 'files' in data:
            file_paths.extend(data['files'])

    if not sys.stdin.isatty():
        try:
            stdin_data = json.load(sys.stdin)
            if isinstance(stdin_data, list):
                file_paths.extend(stdin_data)
            elif isinstance(stdin_data, dict) and 'files' in stdin_data:
                file_paths.extend(stdin_data['files'])
        except (json.JSONDecodeError, EOFError):
            pass

    if not file_paths:
        print(json.dumps({"files": [], "error": "No file paths provided"}), file=sys.stdout)
        sys.exit(1)

    recognizer = SmartFileRecognizer()
    results = recognizer.recognize(file_paths)

    output_data = {
        "files": [model_to_dict(r) for r in results],
        "total": len(results),
    }

    if args.output:
        save_json(output_data, args.output)
        print(json.dumps({"status": "ok", "output": args.output, "total": len(results)}), file=sys.stdout)
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2), file=sys.stdout)


if __name__ == '__main__':
    main()
