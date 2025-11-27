"""图像缓存工具模块"""
import os
import pygame

_base_cache = {}
_scaled_cache = {}

def _normalize_path(path):
    return os.path.abspath(path)

def load_image(path):
    """加载并缓存图像"""
    if not path:
        return None
    norm = _normalize_path(path)
    if norm in _base_cache:
        return _base_cache[norm]
    if not os.path.exists(norm):
        return None
    image = pygame.image.load(norm).convert_alpha()
    _base_cache[norm] = image
    return image

def get_scaled_image(path, size, smooth=True):
    """返回请求尺寸的缓存缩放图像"""
    if not path or not size:
        return None
    base = load_image(path)
    if base is None:
        return None
    width, height = size
    key = (_normalize_path(path), int(width), int(height), bool(smooth))
    if key in _scaled_cache:
        return _scaled_cache[key]
    if smooth:
        scaled = pygame.transform.smoothscale(base, (width, height))
    else:
        scaled = pygame.transform.scale(base, (width, height))
    _scaled_cache[key] = scaled
    return scaled

def clear_cache(path=None):
    """清除缓存条目 如果提供路径则仅清除该图像的缓存。"""
    global _base_cache, _scaled_cache
    if not path:
        _base_cache.clear()
        _scaled_cache.clear()
        return
    norm = _normalize_path(path)
    _base_cache.pop(norm, None)
    keys_to_delete = [key for key in _scaled_cache if key[0] == norm]
    for key in keys_to_delete:
        _scaled_cache.pop(key, None)
