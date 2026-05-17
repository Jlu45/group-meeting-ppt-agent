from src.common.models import LayoutSpec, PlaceholderSpec, SlideSpec, SlideElementSpec


BINDING_PRIORITY = [
    ("title", {"title", "ctrTitle"}),
    ("chart", {"chart", "obj"}),
    ("image", {"pic", "media", "obj"}),
    ("key_points", {"body", "obj"}),
    ("table", {"tbl", "obj", "body"}),
    ("subtitle", {"subtitle"}),
    ("footer", {"ftr", "sldNum"}),
]


class PlaceholderBinder:
    def bind(self, slide_spec: SlideSpec, layout: LayoutSpec) -> dict[str, str]:
        available: list[PlaceholderSpec] = list(layout.placeholders)
        binding: dict[str, str] = {}

        element_roles = [elem.role for elem in slide_spec.elements]

        if slide_spec.title:
            element_roles = ["title"] + element_roles

        ordered_roles = self._order_roles(element_roles)

        for role in ordered_roles:
            preferred = self._get_preferred_types(role)
            if preferred is None:
                continue
            elem_id = self._find_element_id(slide_spec, role)
            result = self._bind_role(slide_spec, role, available, preferred)
            if result is not None:
                binding[elem_id or role] = result.id
                available = [p for p in available if p.id != result.id]

        return binding

    def _bind_role(
        self,
        spec: SlideSpec,
        role: str,
        available_placeholders: list[PlaceholderSpec],
        preferred_types: set[str],
    ) -> PlaceholderSpec | None:
        for ph in available_placeholders:
            if ph.ph_type in preferred_types:
                return ph
        for ph in available_placeholders:
            if ph.ph_type == "obj":
                return ph
        for ph in available_placeholders:
            if ph.ph_type == "body":
                return ph
        return None

    def _order_roles(self, roles: list[str]) -> list[str]:
        priority_map = {r: i for i, (r, _) in enumerate(BINDING_PRIORITY)}
        return sorted(roles, key=lambda r: priority_map.get(r, len(BINDING_PRIORITY)))

    def _get_preferred_types(self, role: str) -> set[str] | None:
        for r, types in BINDING_PRIORITY:
            if r == role:
                return types
        return None

    def _find_element_id(self, spec: SlideSpec, role: str) -> str | None:
        for elem in spec.elements:
            if elem.role == role:
                return elem.role
        if role == "title" and spec.title:
            return "title"
        return role
