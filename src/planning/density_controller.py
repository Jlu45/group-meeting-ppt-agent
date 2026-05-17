import copy
import uuid

from src.common.models import SlideSpec, SlideElementSpec, SlideIntent, TemplateDNA


class DensityController:
    MAX_BULLETS_PER_SLIDE = 6
    MAX_CHARS_PER_BULLET = 80
    MAX_CHARS_PER_TITLE = 40
    DENSITY_THRESHOLDS = {"sparse": 3, "normal": 5, "dense": 7}

    def control(self, slide_specs: list[SlideSpec], template_dna: TemplateDNA = None) -> list[SlideSpec]:
        result = []
        for spec in slide_specs:
            compressed = self._compress_content(spec)
            density = self._estimate_density(compressed)
            if density == "dense":
                split = self._split_slide(compressed)
                result.extend(split)
            else:
                result.append(compressed)
        result = self._try_merge_adjacent(result)
        return result

    def _estimate_density(self, spec: SlideSpec) -> str:
        bullet_count = 0
        total_chars = 0
        for elem in spec.elements:
            if elem.role == "key_points":
                if isinstance(elem.content, list):
                    bullet_count += len(elem.content)
                    for item in elem.content:
                        total_chars += len(str(item))
                elif isinstance(elem.content, str) and elem.content:
                    lines = [l for l in elem.content.split("\n") if l.strip()]
                    bullet_count += len(lines)
                    total_chars += len(elem.content)
            elif elem.role in ("body", "subtitle"):
                text = elem.content if isinstance(elem.content, str) else str(elem.content)
                total_chars += len(text)
        if bullet_count <= self.DENSITY_THRESHOLDS["sparse"]:
            return "sparse"
        elif bullet_count <= self.DENSITY_THRESHOLDS["normal"]:
            return "normal"
        else:
            return "dense"

    def _split_slide(self, spec: SlideSpec) -> list[SlideSpec]:
        key_points_elem = None
        other_elements = []
        for elem in spec.elements:
            if elem.role == "key_points" and key_points_elem is None:
                key_points_elem = elem
            else:
                other_elements.append(elem)

        if key_points_elem is None:
            return [spec]

        if isinstance(key_points_elem.content, list):
            bullets = list(key_points_elem.content)
        elif isinstance(key_points_elem.content, str):
            bullets = [l for l in key_points_elem.content.split("\n") if l.strip()]
        else:
            return [spec]

        if len(bullets) <= self.MAX_BULLETS_PER_SLIDE:
            return [spec]

        chunks = []
        for i in range(0, len(bullets), self.MAX_BULLETS_PER_SLIDE):
            chunks.append(bullets[i:i + self.MAX_BULLETS_PER_SLIDE])

        result = []
        for idx, chunk in enumerate(chunks):
            new_spec = copy.deepcopy(spec)
            new_spec.id = f"{spec.id}_split_{idx}" if spec.id else str(uuid.uuid4())[:8]
            if idx > 0:
                new_spec.title = spec.title + "(续)"
            new_elements = []
            new_kp = SlideElementSpec(
                role="key_points",
                content=chunk,
                asset_ids=list(key_points_elem.asset_ids),
                required=key_points_elem.required,
                visual_weight=key_points_elem.visual_weight,
            )
            new_elements.append(new_kp)
            if idx == 0:
                for elem in other_elements:
                    if elem.role not in ("key_points",):
                        new_elements.append(copy.deepcopy(elem))
            else:
                for elem in other_elements:
                    if elem.role in ("subtitle", "footer"):
                        new_elements.append(copy.deepcopy(elem))
            new_spec.elements = new_elements
            new_spec.intent = SlideIntent(
                slide_type=spec.intent.slide_type,
                content_roles=list(spec.intent.content_roles),
                density="normal",
                preferred_layout=spec.intent.preferred_layout,
                must_have=list(spec.intent.must_have),
            )
            result.append(new_spec)
        return result

    def _compress_content(self, spec: SlideSpec) -> SlideSpec:
        spec = copy.deepcopy(spec)
        if len(spec.title) > self.MAX_CHARS_PER_TITLE:
            spec.title = spec.title[:self.MAX_CHARS_PER_TITLE - 1] + "…"

        new_elements = []
        for elem in spec.elements:
            if elem.role == "key_points":
                if isinstance(elem.content, list):
                    truncated = []
                    for item in elem.content[:self.MAX_BULLETS_PER_SLIDE]:
                        text = str(item)
                        if len(text) > self.MAX_CHARS_PER_BULLET:
                            text = text[:self.MAX_CHARS_PER_BULLET - 1] + "…"
                        truncated.append(text)
                    elem.content = truncated
                elif isinstance(elem.content, str):
                    lines = [l for l in elem.content.split("\n") if l.strip()]
                    truncated = []
                    for line in lines[:self.MAX_BULLETS_PER_SLIDE]:
                        if len(line) > self.MAX_CHARS_PER_BULLET:
                            line = line[:self.MAX_CHARS_PER_BULLET - 1] + "…"
                        truncated.append(line)
                    elem.content = "\n".join(truncated)
            elif isinstance(elem.content, str) and len(elem.content) > self.MAX_CHARS_PER_BULLET * 2:
                elem.content = elem.content[:self.MAX_CHARS_PER_BULLET * 2 - 1] + "…"
            new_elements.append(elem)
        spec.elements = new_elements
        return spec

    def _try_merge_adjacent(self, specs: list[SlideSpec]) -> list[SlideSpec]:
        if len(specs) <= 1:
            return specs

        result = [specs[0]]
        for i in range(1, len(specs)):
            prev = result[-1]
            curr = specs[i]
            prev_density = self._estimate_density(prev)
            curr_density = self._estimate_density(curr)
            if (prev_density == "sparse" and curr_density == "sparse"
                    and prev.slide_type == curr.slide_type):
                merged = copy.deepcopy(prev)
                merged.id = prev.id
                if curr.title and curr.title != prev.title:
                    merged.title = prev.title + " & " + curr.title
                    if len(merged.title) > self.MAX_CHARS_PER_TITLE:
                        merged.title = merged.title[:self.MAX_CHARS_PER_TITLE - 1] + "…"
                merged_elements = list(prev.elements)
                for elem in curr.elements:
                    if elem.role == "key_points":
                        existing_kp = None
                        for e in merged_elements:
                            if e.role == "key_points":
                                existing_kp = e
                                break
                        if existing_kp is not None:
                            if isinstance(existing_kp.content, list) and isinstance(elem.content, list):
                                merged_content = list(existing_kp.content) + list(elem.content)
                                if len(merged_content) <= self.MAX_BULLETS_PER_SLIDE:
                                    existing_kp.content = merged_content
                                else:
                                    merged_elements.append(copy.deepcopy(elem))
                            elif isinstance(existing_kp.content, str) and isinstance(elem.content, str):
                                combined = existing_kp.content + "\n" + elem.content
                                lines = [l for l in combined.split("\n") if l.strip()]
                                if len(lines) <= self.MAX_BULLETS_PER_SLIDE:
                                    existing_kp.content = combined
                                else:
                                    merged_elements.append(copy.deepcopy(elem))
                            else:
                                merged_elements.append(copy.deepcopy(elem))
                        else:
                            merged_elements.append(copy.deepcopy(elem))
                    elif elem.role not in ("title",):
                        merged_elements.append(copy.deepcopy(elem))
                merged.elements = merged_elements
                if curr.speaker_notes:
                    merged.speaker_notes = merged.speaker_notes + "\n" + curr.speaker_notes if merged.speaker_notes else curr.speaker_notes
                result[-1] = merged
            else:
                result.append(curr)
        return result
