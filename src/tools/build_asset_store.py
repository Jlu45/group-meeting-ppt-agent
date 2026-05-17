#!/usr/bin/env python3
import sys
import json
import argparse

from src.assets.asset_builder import AssetBuilder
from src.common.json_io import load_json, save_json, model_to_dict
from src.common.models import AssetStore, FileRecognitionResult


def main():
    parser = argparse.ArgumentParser(description="Build semantic asset store from parsed documents")
    parser.add_argument("--parsed-docs", required=True, help="Path to parsed_documents.json")
    parser.add_argument("--file-recognition", required=True, help="Path to file_recognition.json")
    parser.add_argument("--output", "-o", required=True, help="Output asset_store.json path")
    args = parser.parse_args()

    parsed_data = load_json(args.parsed_docs)
    frec_data = load_json(args.file_recognition)

    frec_results = []
    for f in frec_data.get("files", []):
        frec_results.append(FileRecognitionResult.from_dict(f))

    frec_map = {r.path: r for r in frec_results}

    builder = AssetBuilder()
    stores = []

    for doc in parsed_data.get("documents", []):
        source_path = doc.get("source_path", "")
        frec = frec_map.get(source_path)
        if frec is None:
            frec = FileRecognitionResult(
                id=f"frec-fallback",
                path=source_path,
                filename=source_path.split("/")[-1].split("\\")[-1],
                extension="." + doc.get("file_type", "txt"),
                base_type="document",
                confidence=0.5,
            )
        markdown = doc.get("markdown_content", "")
        store = builder.build_from_parsed(frec, markdown)
        stores.append(store)

    if not stores:
        merged = AssetStore()
    else:
        merged = builder.merge_stores(stores)

    save_json(model_to_dict(merged), args.output)

    summary = {
        "status": "ok",
        "output": args.output,
        "source_files": len(merged.source_files),
        "content_units": len(merged.content_units),
        "evidences": len(merged.evidences),
        "tables": len(merged.tables),
        "figures": len(merged.figures),
        "metrics": len(merged.metrics),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
