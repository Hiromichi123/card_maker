"""共享场景参数的简单存储"""
from typing import Any, Dict

_scene_payloads: Dict[str, Dict[str, Any]] = {}


def set_payload(scene_name: str, data: Dict[str, Any]) -> None:
    """为指定场景设置一次性参数"""
    _scene_payloads[scene_name] = data


def pop_payload(scene_name: str, default: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """读取并删除指定场景的参数"""
    return _scene_payloads.pop(scene_name, default)
