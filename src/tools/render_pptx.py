#!/usr/bin/env python3
"""CLI: render_pptx - Render PPTX from slide specs and template DNA"""
import sys
import json
import argparse

from src.rendering.pptx_renderer import LayoutDrivenRenderer
from src.common.json_io import load_json, save_json, model_to_dict
from src.common.models import TemplateDNA, SlideSpec, SharedState


def main():
    parser = argparse.ArgumentParser(description='Render PPTX from specs')
    parser.add_argument('--state', required=True, help='Path to shared state JSON')
    parser.add_argument('--output', '-o', required=True, help='Output PPTX file path')
    args = parser.parse_args()

    state_data = load_json(args.state)
    state = SharedState.from_dict(state_data)

    if not state.slide_specs:
        print(json.dumps({"status": "error", "message": "No slide_specs in state"}), file=sys.stdout)
        sys.exit(1)

    template_dna = state.template_dna
    if template_dna is None:
        template_dna = TemplateDNA()

    renderer = LayoutDrivenRenderer(template_dna)
    render_log = renderer.render(
        slide_specs=state.slide_specs,
        output_path=args.output,
        asset_store=state.asset_store,
    )

    for spec in state.slide_specs:
        if spec.selected_layout_id:
            for i, s in enumerate(state.slide_specs):
                if s.id == spec.id:
                    state.slide_specs[i] = spec
                    break

    state.render_log = render_log

    state_output_path = args.state
    save_json(model_to_dict(state), state_output_path)

    print(json.dumps({
        "status": "ok",
        "output": args.output,
        "slide_count": render_log.get("slide_count", 0),
        "layout_usage": render_log.get("layout_usage", {}),
        "warnings": render_log.get("warnings", []),
        "errors": render_log.get("errors", []),
    }), file=sys.stdout)


if __name__ == '__main__':
    main()
