import base64
import json
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any, Dict, Type, TypeVar, get_type_hints

T = TypeVar("T")


def model_to_dict(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: model_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [model_to_dict(item) for item in obj]
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    return obj


def model_from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
    if is_dataclass(cls) and hasattr(cls, "from_dict"):
        return cls.from_dict(d)
    if is_dataclass(cls):
        field_names = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in d.items() if k in field_names}
        return cls(**filtered)
    return d


def save_json(data: Any, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if is_dataclass(data) and not isinstance(data, type):
        serialized = model_to_dict(data)
    elif isinstance(data, dict):
        serialized = model_to_dict(data)
    else:
        serialized = data
    with open(p, "w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
