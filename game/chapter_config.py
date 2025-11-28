"""chapter配置，包含章节和关卡的基本信息。"""
from __future__ import annotations
import os

ASSETS_DIR = os.path.join("assets", "poster")

def poster_path(filename: str) -> str:
    return os.path.join(ASSETS_DIR, filename)

def stage_entry(stage_id: str, name: str) -> dict:
    """创建关卡条目"""
    return {
        "id": stage_id,
        "name": name,
        "poster": poster_path(f"{stage_id}.png"),
    }

WORLD_CHAPTERS = [
    {
        "id": "chapter_1",
        "name": "人界",
        "poster": poster_path("chapter_1_enter.png"),
        "bg_type": "bg/chapter_1_map",
        "stages": [
            stage_entry("1-1", "古海要塞"),
            stage_entry("1-2", "幻想森林"),
            stage_entry("1-3", "冬城废墟"),
            stage_entry("1-4", "史诗一战"),
        ],
    },
    {
        "id": "chapter_2",
        "name": "魔域",
        "poster": poster_path("chapter_2_enter.png"),
        "bg_type": "bg/chapter_2_map",
        "stages": [
            stage_entry("2-1", "异界门扉"),
            stage_entry("2-2", "伟大阶梯"),
            stage_entry("2-3", "远古神庙"),
            stage_entry("2-4", "终焉黑洞"),
        ],
    },
    {
        "id": "chapter_3",
        "name": "神宫",
        "poster": poster_path("chapter_3_enter.jpg"),
        "bg_type": "bg/chapter_3_map",
        "stages": [
            stage_entry("3-1", "上升"),
            stage_entry("3-2", "大魔法世界"),
            stage_entry("3-3", "圣山"),
            stage_entry("3-4", "太初秘境"),
        ],
    },
    {
        "id": "chapter_4",
        "name": "月之都",
        "poster": poster_path("chapter_4_enter.png"),
        "bg_type": "bg/chapter_4_map",
        "stages": [
        ],
    }
]

CHAPTER_LOOKUP = {chapter["id"]: chapter for chapter in WORLD_CHAPTERS}
