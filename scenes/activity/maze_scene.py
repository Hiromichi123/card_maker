"""活动迷宫场景"""
import json
import math
import os
import random
from collections import deque
from datetime import datetime
import pygame
from config import *
from scenes.base.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.menu_button import MenuButton
from ui.poster_detail_panel import PosterDetailPanel
from utils.card_database import get_card_database
from utils.scene_payload import set_payload

class ActivityMazeScene(BaseScene):
    SAVE_PATH = os.path.join("data", "activity", "floor1.json")
    TEMP_DECK_PATH = os.path.join("data", "activity", "temp_deck.json")
    MAZE_VERSION = 10
    NODE_COUNT_RANGE = (50, 60)
    BOSS_MIN_DISTANCE = 5
    BASE_TILE_SIZE = 225 * UI_SCALE
    BASE_TILE_GAP = 150 * UI_SCALE
    FLOOR_KEY = "floor1"
    FLOOR_SETTINGS = {
        "floor1": {
            "strength_base": 1.0,
            "enemy_base": 1.0,
            "deck_size": 12,
        }
    }
    ENEMY_TYPE_MULTIPLIERS = {
        "normal": 1.0,
        "elite": 1.5,
        "boss": 2.0,
    }
    RANDOM_STRENGTH_RANGE = (0.9, 1.2)
    EXPLORED_FACTOR_GAIN = 0.6
    TEMP_DECK_SIZE_LIMITS = (6, 16)
    RARITY_BUCKETS = {
        "low": ["D", "C", "C+"],
        "mid": ["B", "B+", "A", "A+"],
        "high": ["S", "S+", "SS", "SS+", "SSS"],
    }
    SHOP_CARD_COUNT = 3
    SHOP_TRAIT_COUNT_RANGE = (2, 3)
    SHOP_RARITY_WEIGHTS = {
        "SSS": 0.28,
        "SS+": 0.35,
        "SS": 0.45,
        "S+": 0.6,
        "S": 0.75,
        "A+": 0.9,
        "A": 1.0,
        "B+": 1.05,
        "B": 1.1,
        "C+": 1.18,
        "C": 1.22,
        "D": 1.25,
    }
    SHOP_TRAITS_POOL = [
        {"name": "锋刃研磨", "desc": "下一场战斗攻击卡牌获得 +1点 攻击。", "rarity": "A"},
        {"name": "防御矩阵", "desc": "战斗开始时获得 10 点护盾。", "rarity": "A"},
        {"name": "充能药剂", "desc": "本层第一次卡牌立即刷新冷却。", "rarity": "S"},
        {"name": "携行补给", "desc": "随机两张攻击卡的费用 -1。", "rarity": "B"},
        {"name": "侦查无人机", "desc": "下一场战斗敌方卡牌信息可见。", "rarity": "B"},
        {"name": "治疗滴剂", "desc": "恢复 20% 最大生命。", "rarity": "A"},
        {"name": "速攻程序", "desc": "本场战斗的第 1 张牌额外行动一次。", "rarity": "S"},
    ]
    EVENT_CARD_RARITY = "#elna"
    SHOP_EVENT_LABEL = "活动限定"
    SHOP_REGULAR_LABEL = "迷宫补给"
    SHOP_PRICE_RULES = {
        "SSS": {"currency": "crystal", "amount": 551},
        "SS+": {"currency": "crystal", "amount": 430},
        "SS": {"currency": "crystal", "amount": 324},
        "S+": {"currency": "crystal", "amount": 200},
        "S": {"currency": "crystal", "amount": 120},
        "A+": {"currency": "gold", "amount": 5200},
        "A": {"currency": "gold", "amount": 4153},
        "B+": {"currency": "gold", "amount": 3100},
        "B": {"currency": "gold", "amount": 2589},
        "C+": {"currency": "gold", "amount": 1900},
        "C": {"currency": "gold", "amount": 1354},
        "D": {"currency": "gold", "amount": 690},
    }
    EVENT_PRICE_MULTIPLIER = 1.2
    REGULAR_DISCOUNT = 0.85

    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/activity")
        self.title_font = get_font(int(70 * UI_SCALE))
        self.info_font = get_font(int(28 * UI_SCALE))
        self.small_font = get_font(int(22 * UI_SCALE))
        self.floor_key = self.FLOOR_KEY
        self.temp_deck_path = self.TEMP_DECK_PATH

        self.node_type_styles = {
            "entry": {"color": (170, 255, 200), "alpha": 230, "label": "入口"},
            "normal": {"color": (70, 75, 90), "alpha": 210, "label": "普通敌人"},
            "elite": {"color": (190, 120, 255), "alpha": 215, "label": "精英敌人"},
            "boss": {"color": (255, 90, 90), "alpha": 235, "label": "楼层Boss"},
            "supply": {"color": (255, 215, 120), "alpha": 220, "label": "商店补给"},
        }

        self.tile_size = int(self.BASE_TILE_SIZE * UI_SCALE)
        self.tile_gap = int(self.BASE_TILE_GAP * UI_SCALE)
        self.tile_front = int(max(20 * UI_SCALE, self.tile_size * 0.3))
        self.camera_offset = pygame.Vector2(0, 0)

        self.nodes = []
        self.nodes_by_id = {}
        self.connections = []
        self.entry_id = 0
        self.player_node_id = None
        self.player_orb_phase = 0.0
        self.hovered_node_id = None
        self.selected_target_id = None
        self.last_strength_snapshot = None

        btn_width = int(260 * UI_SCALE)
        btn_height = int(56 * UI_SCALE)
        self.back_button = MenuButton(
            int(WINDOW_WIDTH * 0.82), int(WINDOW_HEIGHT * 0.9),
            btn_width, btn_height,
            "返回活动大厅",
            color=(120, 200, 255), hover_color=(160, 230, 255), text_color=(225, 225, 225),
            on_click=lambda: self.switch_to("activity_scene")
        )
        self.reset_button = MenuButton(
            int(WINDOW_WIDTH * 0.08), int(WINDOW_HEIGHT * 0.9),
            btn_width, btn_height,
            "清空探索记录",
            color=(120, 200, 255), hover_color=(160, 230, 255), text_color=(225, 225, 225),
            on_click=self._reset_progress
        )

        panel_rect = pygame.Rect(
            int(WINDOW_WIDTH * 0.72),
            int(WINDOW_HEIGHT * 0.1),
            int(WINDOW_WIDTH * 0.24),
            int(WINDOW_HEIGHT * 0.8),
        )
        self.detail_panel = PosterDetailPanel(panel_rect)
        self.detail_panel.hide()
        self.hovered_node_id = None
        self.last_strength_snapshot = None

        self.is_moving = False
        self.move_start_id = None
        self.move_target_id = None
        self.move_progress = 0.0
        self.move_duration = 0.45
        self.move_start_pos = pygame.Vector2()
        self.move_end_pos = pygame.Vector2()

        self._ensure_data_directory()
        self._load_or_create_maze(force_reload=True)

    def enter(self):
        super().enter()
        # 重新加载以读取最新的探索进度
        self._load_or_create_maze(force_reload=True)

    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.switch_to("activity_scene")
        elif event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
            self._update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_node_click(event.pos)

        self.back_button.handle_event(event)
        self.reset_button.handle_event(event)

    def update(self, dt):
        self.background.update(dt)
        self.back_button.update(dt)
        self.reset_button.update(dt)
        self._update_move_animation(dt)
        self.player_orb_phase += dt * 2.5

    def draw(self):
        self.background.draw(self.screen)
        self._draw_title()
        self._draw_connections()
        self._draw_nodes()
        self._draw_player_orb()
        self.detail_panel.draw(self.screen)
        self._draw_legend()
        self.reset_button.draw(self.screen)
        self.back_button.draw(self.screen)
        self._draw_hint()

    # ------------------------------------------------------------------
    # 数据加载 & 生成
    # ------------------------------------------------------------------
    def _ensure_data_directory(self):
        os.makedirs(os.path.dirname(self.SAVE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(self.TEMP_DECK_PATH), exist_ok=True)

    def _load_or_create_maze(self, force_reload=False):
        if not force_reload and self.nodes:
            return
        data = self._read_maze_file()
        if data is None or data.get("version") != self.MAZE_VERSION:
            data = self._generate_maze_data()
            self._save_maze_data(data)
        self._apply_maze_data(data)

    def _read_maze_file(self):
        try:
            with open(self.SAVE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None

    def _save_maze_data(self, data):
        try:
            with open(self.SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as err:
            print(f"[ActivityMazeScene] 无法保存迷宫进度: {err}")

    def _generate_maze_data(self):
        target_nodes = random.randint(*self.NODE_COUNT_RANGE)
        best_nodes = []
        best_distances = {}
        boss_id = None
        for attempt in range(6):
            candidates = self._build_sparse_layout(target_nodes)
            distances = self._compute_distances(candidates, 0)
            if not distances:
                continue
            farthest_id = max(distances, key=distances.get)
            best_nodes = candidates
            best_distances = distances
            boss_id = farthest_id if distances[farthest_id] >= self.BOSS_MIN_DISTANCE else None
            if distances[farthest_id] >= self.BOSS_MIN_DISTANCE:
                break

        if not best_nodes:
            best_nodes = self._build_sparse_layout(max(5, target_nodes))
            best_distances = self._compute_distances(best_nodes, 0)
            boss_id = max(best_distances, key=best_distances.get) if best_distances else 0

        if boss_id == 0 and len(best_nodes) > 1:
            boss_candidates = [node["id"] for node in best_nodes if node["id"] != 0]
            boss_id = random.choice(boss_candidates)

        self._sanitize_neighbor_lists(best_nodes)
        self._assign_node_categories(best_nodes, entry_id=0, boss_id=boss_id)

        return {
            "version": self.MAZE_VERSION,
            "entry_id": 0,
            "player_node": 0,
            "nodes": best_nodes,
        }

    def _build_sparse_layout(self, target_nodes):
        node_list = []
        pos_to_id = {}
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        def add_node(pos, explored=False):
            node_id = len(node_list)
            node = {
                "id": node_id,
                "grid": [pos[0], pos[1]],
                "color": (120, 120, 120),
                "alpha": 200,
                "event": "未知",
                "explored": explored,
                "neighbors": [],
                "type": "normal",
            }
            node_list.append(node)
            pos_to_id[pos] = node_id
            return node_id

        def can_expand(node_id):
            limit = 4 if node_id == 0 else 3
            return len(node_list[node_id]["neighbors"]) < limit

        add_node((0, 0), explored=True)
        attempts = 0
        max_attempts = max(360, target_nodes * 85)
        while len(node_list) < target_nodes and attempts < max_attempts:
            attempts += 1
            expandable = [nid for nid in range(len(node_list)) if can_expand(nid)]
            if not expandable:
                break
            leaves = [nid for nid in expandable if len(node_list[nid]["neighbors"]) <= 1]
            sparse_nodes = [nid for nid in expandable if len(node_list[nid]["neighbors"]) <= 2]
            if leaves and random.random() < 0.4:
                base_id = random.choice(leaves)
            elif sparse_nodes and random.random() < 0.7:
                base_id = random.choice(sparse_nodes)
            else:
                base_id = random.choice(expandable)
            base_pos = tuple(node_list[base_id]["grid"])
            progress = len(node_list) / max(1, target_nodes)
            step_choices = directions[:]
            random.shuffle(step_choices)

            placed = False
            for delta_x, delta_y in step_choices:
                skip_factor = 0.35 if progress < 0.5 else 0.25
                if random.random() < skip_factor:
                    continue
                new_pos = (base_pos[0] + delta_x, base_pos[1] + delta_y)
                if new_pos in pos_to_id:
                    continue
                local_density = self._neighbor_density(new_pos, pos_to_id)
                if progress < 0.35:
                    density_limit = 2
                elif progress < 0.7:
                    density_limit = 3
                else:
                    density_limit = 4
                if local_density > density_limit:
                    continue
                new_id = add_node(new_pos)
                node_list[base_id]["neighbors"].append(new_id)
                node_list[new_id]["neighbors"].append(base_id)
                self._attach_side_links(node_list, pos_to_id, new_id)
                placed = True
                break

        self._add_extra_links(node_list)
        return node_list

    def _neighbor_density(self, pos, existing):
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if (pos[0] + dx, pos[1] + dy) in existing:
                    count += 1
        return count

    @staticmethod
    def _grid_step_distance(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _attach_side_links(self, node_list, pos_to_id, node_id):
        if node_id >= len(node_list):
            return
        node = node_list[node_id]
        grid = tuple(node["grid"])
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            neighbor_pos = (grid[0] + dx, grid[1] + dy)
            neighbor_id = pos_to_id.get(neighbor_pos)
            if neighbor_id is None or neighbor_id == node_id:
                continue
            if neighbor_id in node["neighbors"]:
                continue
            neighbor_node = node_list[neighbor_id]
            degree_sum = len(node["neighbors"]) + len(neighbor_node["neighbors"])
            chance = 0.25 if degree_sum < 5 else 0.12
            if random.random() < chance:
                node["neighbors"].append(neighbor_id)
                neighbor_node["neighbors"].append(node_id)

    def _add_extra_links(self, nodes):
        pos_map = {tuple(node["grid"]): node["id"] for node in nodes}
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for node in nodes:
            node_id = node["id"]
            base_neighbors = set(node["neighbors"])
            grid = tuple(node["grid"])
            for dx, dy in directions:
                neighbor_pos = (grid[0] + dx, grid[1] + dy)
                neighbor_id = pos_map.get(neighbor_pos)
                if neighbor_id is None or neighbor_id == node_id:
                    continue
                if neighbor_id in base_neighbors:
                    continue
                other = nodes[neighbor_id]
                combined = len(node["neighbors"]) + len(other["neighbors"])
                chance = 0.3 if combined < 5 else 0.12
                if random.random() < chance:
                    node["neighbors"].append(neighbor_id)
                    other["neighbors"].append(node_id)

    def _sanitize_neighbor_lists(self, nodes):
        id_map = {node["id"]: node for node in nodes}
        adjacency = {node_id: set() for node_id in id_map.keys()}
        for node in nodes:
            node_id = node["id"]
            grid_a = tuple(node.get("grid", (0, 0)))
            for neighbor in node.get("neighbors", []):
                target = id_map.get(neighbor)
                if not target:
                    continue
                if neighbor == node_id:
                    continue
                grid_b = tuple(target.get("grid", (0, 0)))
                if self._grid_step_distance(grid_a, grid_b) != 1:
                    continue
                adjacency[node_id].add(neighbor)
                adjacency[neighbor].add(node_id)
        for node in nodes:
            node["neighbors"] = sorted(adjacency[node["id"]])

    def _compute_distances(self, nodes, start_id):
        if start_id >= len(nodes):
            return {}
        distances = {start_id: 0}
        queue = deque([start_id])
        while queue:
            current = queue.popleft()
            current_dist = distances[current]
            for neighbor in nodes[current]["neighbors"]:
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)
        return distances

    def _assign_node_categories(self, nodes, entry_id, boss_id):
        if not nodes:
            return
        entry_id = max(0, min(entry_id, len(nodes) - 1))
        if boss_id == entry_id:
            candidates = [node["id"] for node in nodes if node["id"] != entry_id]
            if candidates:
                boss_id = random.choice(candidates)
        boss_id = max(0, min(boss_id, len(nodes) - 1))

        ratio = {"elite": 1, "supply": 2, "normal": 8}
        available_ids = [node["id"] for node in nodes if node["id"] not in (entry_id, boss_id)]
        random.shuffle(available_ids)

        remaining = len(available_ids)
        total_ratio = sum(ratio.values())
        counts = {
            key: int(remaining * value / total_ratio)
            for key, value in ratio.items()
        }
        assigned = sum(counts.values())
        remainder = remaining - assigned
        ratio_order = sorted(ratio.items(), key=lambda item: -item[1])
        idx = 0
        while remainder > 0 and ratio_order:
            counts[ratio_order[idx % len(ratio_order)][0]] += 1
            remainder -= 1
            idx += 1

        nodes[entry_id]["type"] = "entry"
        nodes[boss_id]["type"] = "boss"
        nodes[entry_id]["explored"] = True
        nodes[boss_id]["explored"] = nodes[boss_id].get("explored", False)

        for node_type in ("elite", "supply", "normal"):
            quota = counts.get(node_type, 0)
            for _ in range(quota):
                if not available_ids:
                    break
                node_id = available_ids.pop()
                nodes[node_id]["type"] = node_type

        for node_id in available_ids:
            nodes[node_id]["type"] = "normal"

        for node in nodes:
            self._apply_type_style(node)

    def _apply_type_style(self, node):
        node_type = node.get("type", "normal")
        style = self.node_type_styles.get(node_type, self.node_type_styles["normal"])
        node["color"] = style["color"]
        node["alpha"] = style.get("alpha", 210)
        node["event"] = style["label"]

    def _apply_maze_data(self, data):
        raw_nodes = data.get("nodes", [])
        self.nodes = []
        self.nodes_by_id = {}
        self.entry_id = data.get("entry_id", 0)
        player_target = data.get("player_node", self.entry_id)

        for raw in raw_nodes:
            node_id = raw.get("id", len(self.nodes))
            node_type = raw.get("type")
            if not node_type:
                node_type = "entry" if node_id == self.entry_id else "normal"
            node = {
                "id": node_id,
                "grid": tuple(raw.get("grid", (0, 0))),
                "color": tuple(raw.get("color", (200, 200, 200))),
                "alpha": int(raw.get("alpha", 180)),
                "event": raw.get("event", "未知"),
                "explored": bool(raw.get("explored", False)),
                "neighbors": list(raw.get("neighbors", [])),
                "type": node_type,
            }
            if raw.get("shop_state"):
                node["shop_state"] = raw.get("shop_state")
            if node_id == self.entry_id:
                node["explored"] = True
            self._apply_type_style(node)
            self.nodes.append(node)
            self.nodes_by_id[node_id] = node

        if player_target not in self.nodes_by_id:
            player_target = self.entry_id
        self.player_node_id = player_target

        self._enforce_bidirectional_links()
        self._layout_nodes()
        self._focus_on_player()
        self._build_connections()

    def _enforce_bidirectional_links(self):
        adjacency = {node_id: set() for node_id in self.nodes_by_id.keys()}
        for node in self.nodes:
            node_id = node["id"]
            grid_a = node.get("grid", (0, 0))
            for neighbor in node.get("neighbors", []):
                target = self.nodes_by_id.get(neighbor)
                if not target or neighbor == node_id:
                    continue
                if self._grid_step_distance(grid_a, target.get("grid", (0, 0))) != 1:
                    continue
                adjacency[node_id].add(neighbor)
                adjacency[target["id"]].add(node_id)
        for node in self.nodes:
            node["neighbors"] = sorted(adjacency[node["id"]])

    def _layout_nodes(self):
        if not self.nodes:
            return
        min_x = min(node["grid"][0] for node in self.nodes)
        max_x = max(node["grid"][0] for node in self.nodes)
        min_y = min(node["grid"][1] for node in self.nodes)
        max_y = max(node["grid"][1] for node in self.nodes)

        pitch = self.tile_size + self.tile_gap
        maze_width = (max_x - min_x) * pitch + self.tile_size
        maze_height = (max_y - min_y) * pitch + self.tile_size + self.tile_front
        start_x = int((WINDOW_WIDTH - maze_width) / 2)
        start_y = int((WINDOW_HEIGHT - maze_height) / 2)

        for node in self.nodes:
            grid_x = node["grid"][0] - min_x
            grid_y = node["grid"][1] - min_y
            px = start_x + grid_x * pitch
            py = start_y + grid_y * pitch
            node["base_rect"] = pygame.Rect(px, py, self.tile_size, self.tile_size)
            node["top_rect"] = node["base_rect"].copy()

    def _update_screen_rects(self):
        offset_x = int(self.camera_offset.x)
        offset_y = int(self.camera_offset.y)
        for node in self.nodes:
            base_rect = node.get("base_rect")
            if base_rect:
                top_rect = base_rect.move(offset_x, offset_y)
                node["top_rect"] = top_rect
                node["screen_pos"] = top_rect.center

    def _focus_on_player(self):
        node = self.nodes_by_id.get(self.player_node_id)
        if not node:
            self._update_screen_rects()
            return
        base_rect = node.get("base_rect")
        if not base_rect:
            self._update_screen_rects()
            return
        self._focus_on_world_point(pygame.Vector2(base_rect.center))

    def _focus_on_world_point(self, world_point):
        desired = pygame.Vector2(WINDOW_WIDTH * 0.5, WINDOW_HEIGHT * 0.45)
        current = pygame.Vector2(world_point)
        self.camera_offset = desired - current
        self._update_screen_rects()

    def _get_player_world_position(self):
        if self.is_moving and self.move_start_id is not None and self.move_target_id is not None:
            return self.move_start_pos.lerp(self.move_end_pos, self.move_progress)
        node = self.nodes_by_id.get(self.player_node_id)
        if node:
            base_rect = node.get("base_rect")
            if base_rect:
                return pygame.Vector2(base_rect.center)
        return pygame.Vector2(WINDOW_WIDTH * 0.5, WINDOW_HEIGHT * 0.5)

    def _build_connections(self):
        pairs = set()
        for node in self.nodes:
            for neighbor in node["neighbors"]:
                pair = tuple(sorted((node["id"], neighbor)))
                pairs.add(pair)
        self.connections = list(pairs)

    # ------------------------------------------------------------------
    # 交互
    # ------------------------------------------------------------------
    def _update_hover(self, mouse_pos):
        node = self._get_node_at_position(mouse_pos)
        self.hovered_node_id = node["id"] if node else None

    def _handle_node_click(self, mouse_pos):
        if self.player_node_id is None:
            return
        if self.is_moving:
            return
        node = self._get_node_at_position(mouse_pos)
        if not node:
            self._clear_selection()
            return
        node_id = node["id"]
        if node_id == self.player_node_id:
            self._clear_selection()
            return
        if not self._can_move_to(node_id):
            self._clear_selection()
            return
        if self.selected_target_id != node_id:
            self.selected_target_id = node_id
            self._show_node_detail(node)
            return
        self._start_move_animation(node_id)

    def _get_node_at_position(self, mouse_pos):
        for node in self.nodes:
            rect = node.get("top_rect")
            if rect and rect.collidepoint(mouse_pos):
                return node
        return None

    def _can_move_to(self, node_id):
        if self.player_node_id is None:
            return False
        player_node = self.nodes_by_id.get(self.player_node_id)
        if not player_node:
            return False
        return node_id in player_node.get("neighbors", [])

    def _clear_selection(self):
        self.selected_target_id = None
        self.detail_panel.hide()

    def _show_node_detail(self, node):
        entry = self._build_node_detail_entry(node)
        self.detail_panel.set_entry(entry)

    def _build_node_detail_entry(self, node):
        node_type = node.get("type", "normal")
        style = self.node_type_styles.get(node_type, self.node_type_styles["normal"])
        explored_text = "已探索" if node.get("explored") else "未探索"
        neighbors = len(node.get("neighbors", []))
        tags = [style["label"], f"相邻 {neighbors} 格"]
        entry = {
            "title": node.get("event", "未知事件"),
            "subtitle": f"节点 #{node['id']}",
            "description": f"类型：{style['label']} 状态：{explored_text}。",
            "tags": tags,
            "rewards": [self._node_reward_hint(node_type)],
        }
        if self._is_battle_node(node_type):
            ctx = self._build_strength_context(node_type, use_average_random=True)
            entry["description"] += f" 预估强度系数：{ctx['total']:.2f}。"
            estimated_size = self._calc_deck_size(ctx["total"])
            entry.setdefault("rewards", []).append(f"敌方牌组约 {estimated_size} 张")
        return entry

    def _node_reward_hint(self, node_type):
        mapping = {
            "entry": "安全区域",
            "normal": "普通奖励",
            "elite": "稀有战利品",
            "boss": "进入下一层",
            "supply": "补给资源",
        }
        return mapping.get(node_type, "未知")

    def _is_battle_node(self, node_type):
        return node_type in ("normal", "elite", "boss")

    def _handle_node_arrival(self, node):
        if not node:
            return
        node_type = node.get("type", "normal")
        if self._is_battle_node(node_type):
            deck_payload = self._generate_temp_enemy_deck(node)
            self._write_temp_deck(deck_payload)
            stage_id = f"{self.floor_key}-{node.get('id')}"
            battle_payload = {
                "stage_id": stage_id,
                "stage_name": node.get("event", "迷宫战斗"),
                "enemy_deck": self.temp_deck_path,
                "background": None,
                "node_type": node_type,
                "floor": self.floor_key,
            }
            set_payload("simple_battle", battle_payload)
            self.switch_to("simple_battle")
            return
        if node_type == "supply":
            shop_payload = self._build_floor_shop_payload(node)
            set_payload("floor_shop", shop_payload)
            self.switch_to("floor_shop")

    def _generate_temp_enemy_deck(self, node):
        node_type = node.get("type", "normal")
        ctx = self._build_strength_context(node_type)
        self.last_strength_snapshot = ctx
        deck_size = self._calc_deck_size(ctx["total"])
        cards = self._sample_enemy_cards(deck_size, ctx["total"])
        payload = {
            "deck": cards,
            "meta": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "node_id": node.get("id"),
                "node_type": node_type,
                "strength": ctx,
                "deck_size": deck_size,
            }
        }
        return payload

    def _write_temp_deck(self, payload):
        try:
            with open(self.temp_deck_path, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=2)
            print(f"[ActivityMazeScene] 已生成临时卡组 -> {self.temp_deck_path}")
        except OSError as err:
            print(f"[ActivityMazeScene] 无法写入临时卡组: {err}")

    def _build_floor_shop_payload(self, node):
        state = node.get("shop_state")
        if not state or not state.get("cards"):
            state = self._generate_shop_state(node)
            node["shop_state"] = state
            self._persist_state()
        return {
            "floor": self.floor_key,
            "node_id": node.get("id"),
            "node_type": node.get("type"),
            "node_event": node.get("event"),
            "traits": state.get("traits", []),
            "cards": state.get("cards", []),
            "generated_at": state.get("generated_at"),
            "shop_state": state,
            "save_path": self.SAVE_PATH,
        }

    def _generate_shop_state(self, node):
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        traits = self._roll_shop_traits()
        cards = self._build_shop_inventory()
        return {
            "node_id": node.get("id"),
            "generated_at": generated_at,
            "traits": traits,
            "cards": cards,
        }

    def _build_shop_inventory(self):
        inventory = []
        event_card = self._pick_event_card()
        if event_card:
            inventory.append(self._create_shop_entry(event_card, self.SHOP_EVENT_LABEL, source="event"))
        regular_needed = max(0, self.SHOP_CARD_COUNT - len(inventory))
        for card in self._roll_shop_cards(count=regular_needed):
            inventory.append(self._create_shop_entry(card, self.SHOP_REGULAR_LABEL, source="regular"))
        for idx, entry in enumerate(inventory):
            entry["slot"] = idx
        return inventory

    def _create_shop_entry(self, card_info, label, source="regular"):
        return {
            "slot": -1,
            "card": card_info,
            "label": label,
            "quantity": 1,
            "sold": False,
            "source": source,
            "price": self._calc_shop_price(card_info, source),
        }

    def _calc_shop_price(self, card_info, source):
        rarity = (card_info or {}).get("rarity", "A")
        base_rule = self.SHOP_PRICE_RULES.get(rarity, {"currency": "gold", "amount": 1200})
        price = {
            "currency": base_rule.get("currency", "gold"),
            "amount": int(base_rule.get("amount", 0))
        }
        if source == "regular":
            price["amount"] = max(50, int(price["amount"] * self.REGULAR_DISCOUNT))
        elif source == "event":
            price["currency"] = "crystal"
            price["amount"] = max(75, int(price["amount"] * self.EVENT_PRICE_MULTIPLIER))
        return price

    def _calc_deck_size(self, strength_value):
        floor_cfg = self.FLOOR_SETTINGS.get(self.floor_key, self.FLOOR_SETTINGS[self.FLOOR_KEY])
        base_size = floor_cfg.get("deck_size", 8)
        scaled = base_size * (0.8 + min(strength_value, 3.0) * 0.35)
        deck_size = int(round(scaled))
        min_size, max_size = self.TEMP_DECK_SIZE_LIMITS
        return max(min_size, min(max_size, deck_size))

    def _build_strength_context(self, node_type, use_average_random=False):
        floor_cfg = self.FLOOR_SETTINGS.get(self.floor_key, self.FLOOR_SETTINGS[self.FLOOR_KEY])
        floor_base = floor_cfg.get("strength_base", 1.0)
        enemy_base = floor_cfg.get("enemy_base", 1.0)
        explored_ratio = self._get_explored_ratio()
        dynamic_factor = 1.0 + explored_ratio * self.EXPLORED_FACTOR_GAIN
        if use_average_random:
            random_factor = sum(self.RANDOM_STRENGTH_RANGE) / 2
        else:
            random_factor = random.uniform(*self.RANDOM_STRENGTH_RANGE)
        type_multiplier = self.ENEMY_TYPE_MULTIPLIERS.get(node_type, 1.0)
        total = floor_base * enemy_base * dynamic_factor * type_multiplier * random_factor
        return {
            "total": total,
            "floor_base": floor_base,
            "enemy_base": enemy_base,
            "dynamic_factor": dynamic_factor,
            "type_multiplier": type_multiplier,
            "random_factor": random_factor,
            "explored_ratio": explored_ratio,
        }

    def _get_explored_ratio(self):
        if not self.nodes:
            return 0.0
        explored = sum(1 for node in self.nodes if node.get("explored"))
        return explored / max(1, len(self.nodes))

    def _sample_enemy_cards(self, deck_size, strength_value):
        db = get_card_database()
        all_cards = db.get_all_cards()
        if not all_cards:
            return [self._build_fallback_card_entry(strength_value, idx) for idx in range(deck_size)]
        grouped = {rarity: list(db.get_cards_by_rarity(rarity)) for rarity in {card.rarity for card in all_cards}}
        cards = []
        high_bias = max(0.05, min(0.75, 0.25 + (strength_value - 1.0) * 0.2))
        mid_bias = max(0.2, min(0.9, 0.4 + (strength_value - 0.8) * 0.2))
        for _ in range(deck_size):
            roll = random.random()
            if roll < high_bias and self._rarity_pool_available(grouped, self.RARITY_BUCKETS["high"]):
                rarity = self._pick_rarity(grouped, self.RARITY_BUCKETS["high"])
            elif roll < mid_bias and self._rarity_pool_available(grouped, self.RARITY_BUCKETS["mid"]):
                rarity = self._pick_rarity(grouped, self.RARITY_BUCKETS["mid"])
            else:
                rarity = self._pick_rarity(grouped, self.RARITY_BUCKETS["low"], fallback=True)
            pool = grouped.get(rarity) or all_cards
            card = random.choice(pool)
            path = (card.image_path or "").replace("/", os.sep)
            cards.append({"path": path, "rarity": card.rarity})
        return cards

    def _rarity_pool_available(self, grouped, rarities):
        for rarity in rarities:
            if grouped.get(rarity):
                return True
        return False

    def _pick_rarity(self, grouped, rarities, fallback=False):
        available = [r for r in rarities if grouped.get(r)]
        if available:
            return random.choice(available)
        if fallback:
            all_available = [r for r, cards in grouped.items() if cards]
            if all_available:
                return random.choice(all_available)
        return random.choice(rarities)

    def _build_fallback_card_entry(self, strength_value, idx):
        atk = int(40 + strength_value * 30 + random.randint(-5, 10))
        hp = int(120 + strength_value * 60 + random.randint(-10, 15))
        cd = max(1, int(3 - min(1.5, strength_value * 0.5)))
        return {
            "path": f"generated/temp_enemy_card_{idx}.png",
            "rarity": "C",
            "atk": atk,
            "hp": hp,
            "cd": cd,
            "name": f"临时敌人 {idx + 1}",
        }

    def _roll_shop_traits(self):
        if not self.SHOP_TRAITS_POOL:
            return []
        choices = self.SHOP_TRAITS_POOL[:]
        random.shuffle(choices)
        min_count = min(len(choices), self.SHOP_TRAIT_COUNT_RANGE[0])
        max_count = min(len(choices), self.SHOP_TRAIT_COUNT_RANGE[1])
        if min_count > max_count:
            min_count = max_count
        count = random.randint(min_count, max_count) if max_count else 0
        return [dict(trait) for trait in choices[:count]]

    def _roll_shop_cards(self, count=None):
        desired = count or self.SHOP_CARD_COUNT
        db = get_card_database()
        pool = [card for card in db.get_all_cards() if not getattr(card, "is_event_card", False)]
        if not pool:
            return []
        selected = []
        available = pool[:]
        for _ in range(desired):
            if not available:
                available = pool[:]
            weights = [self.SHOP_RARITY_WEIGHTS.get(card.rarity, 1.0) for card in available]
            choice = random.choices(available, weights=weights, k=1)[0]
            selected.append(self._serialize_card_for_shop(choice))
            if choice in available:
                available.remove(choice)
        return selected

    def _serialize_card_for_shop(self, card):
        return {
            "card_id": card.card_id,
            "name": card.name,
            "rarity": card.rarity,
            "atk": card.atk,
            "hp": card.hp,
            "cd": card.cd,
            "traits": card.traits,
            "image_path": card.image_path,
        }

    def _pick_event_card(self):
        db = get_card_database()
        event_cards = db.get_cards_by_rarity(self.EVENT_CARD_RARITY)
        if not event_cards:
            return None
        card = random.choice(event_cards)
        return self._serialize_card_for_shop(card)

    def _start_move_animation(self, target_id):
        if self.player_node_id is None or self.is_moving:
            return
        start_node = self.nodes_by_id.get(self.player_node_id)
        end_node = self.nodes_by_id.get(target_id)
        if not start_node or not end_node:
            return
        start_rect = start_node.get("base_rect")
        end_rect = end_node.get("base_rect")
        if not start_rect or not end_rect:
            return
        self.is_moving = True
        self.move_start_id = self.player_node_id
        self.move_target_id = target_id
        self.move_progress = 0.0
        self.move_duration = 0.45
        self.move_start_pos = pygame.Vector2(start_rect.center)
        self.move_end_pos = pygame.Vector2(end_rect.center)
        self._clear_selection()
        self._focus_on_world_point(self.move_start_pos)

    def _update_move_animation(self, dt):
        if not self.is_moving:
            return
        if self.move_duration <= 0:
            self.move_progress = 1.0
        else:
            self.move_progress = min(1.0, self.move_progress + dt / self.move_duration)
        world_pos = self._get_player_world_position()
        self._focus_on_world_point(world_pos)
        if self.move_progress >= 1.0:
            self._complete_move_animation()

    def _complete_move_animation(self):
        target_id = self.move_target_id
        self.is_moving = False
        self.move_start_id = None
        self.move_target_id = None
        self.move_start_pos = pygame.Vector2()
        self.move_end_pos = pygame.Vector2()
        if target_id is not None:
            self._move_player_to(target_id)

    def _move_player_to(self, node_id):
        self._clear_selection()
        self.player_node_id = node_id
        node = self.nodes_by_id.get(node_id)
        if node:
            node["explored"] = True
        self._persist_state()
        self._focus_on_player()
        self._handle_node_arrival(node)

    def _persist_state(self):
        nodes_payload = []
        for node in self.nodes:
            entry = {
                "id": node["id"],
                "grid": list(node["grid"]),
                "color": list(node["color"]),
                "alpha": node["alpha"],
                "event": node["event"],
                "explored": node.get("explored", False),
                "neighbors": node["neighbors"],
                "type": node.get("type", "normal"),
            }
            if node.get("shop_state"):
                entry["shop_state"] = node["shop_state"]
            nodes_payload.append(entry)

        data = {
            "version": self.MAZE_VERSION,
            "entry_id": self.entry_id,
            "player_node": self.player_node_id,
            "nodes": nodes_payload,
        }
        self._save_maze_data(data)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def _draw_title(self):
        title = self.title_font.render("迷宫挑战·第一层", True, (255, 240, 210))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.08)))
        shadow = self.title_font.render("迷宫挑战·第一层", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(title_rect.centerx + int(4 * UI_SCALE), title_rect.centery + int(4 * UI_SCALE)))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)

        subtitle = self.info_font.render("点击相邻节点前进，探索记录将自动保存", True, (220, 230, 255))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.13)))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_connections(self):
        if not self.connections:
            return
        line_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for a_id, b_id in self.connections:
            node_a = self.nodes_by_id.get(a_id)
            node_b = self.nodes_by_id.get(b_id)
            if not node_a or not node_b:
                continue
            rect_a = node_a.get("top_rect")
            rect_b = node_b.get("top_rect")
            if not rect_a or not rect_b:
                continue
            start = rect_a.center
            end = rect_b.center
            pygame.draw.line(line_surface, (120, 190, 255, 120), start, end, width=max(2, int(3 * UI_SCALE)))
        self.screen.blit(line_surface, (0, 0))

    def _draw_nodes(self):
        if not self.nodes:
            return
        bevel = max(4, int(self.tile_size * 0.08))
        for node in sorted(self.nodes, key=lambda n: (n["screen_pos"][1], n["screen_pos"][0])):
            top_rect = node.get("top_rect")
            if not top_rect:
                continue
            color = node["color"]
            alpha = node["alpha"]
            explored = node.get("explored", False)

            # 顶部面
            top_surface = pygame.Surface(top_rect.size, pygame.SRCALPHA)
            top_surface.fill((*color, alpha))
            if not explored:
                dim = pygame.Surface(top_rect.size, pygame.SRCALPHA)
                dim.fill((10, 10, 20, 160))
                top_surface.blit(dim, (0, 0))
            self.screen.blit(top_surface, top_rect.topleft)

            # 立体前侧
            bottom_y = top_rect.bottom
            front_points = [
                (top_rect.left, bottom_y),
                (top_rect.right, bottom_y),
                (top_rect.right - bevel, bottom_y + self.tile_front),
                (top_rect.left + bevel, bottom_y + self.tile_front)
            ]
            darker = tuple(max(0, c - 40) for c in color)
            pygame.draw.polygon(self.screen, (*darker, min(255, alpha + 10)), front_points)

            if node["id"] == self.selected_target_id:
                selected_rect = top_rect.inflate(int(10 * UI_SCALE), int(10 * UI_SCALE))
                pygame.draw.rect(
                    self.screen,
                    (255, 210, 140),
                    selected_rect,
                    width=max(2, int(4 * UI_SCALE)),
                )

            # 高亮悬停节点
            if node["id"] == self.hovered_node_id:
                highlight_rect = top_rect.inflate(int(6 * UI_SCALE), int(6 * UI_SCALE))
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    highlight_rect,
                    width=max(2, int(3 * UI_SCALE))
                )

            # 事件文字
            label = self.small_font.render(node["event"], True, (230, 235, 255))
            label_rect = label.get_rect(center=(top_rect.centerx, top_rect.bottom + int(self.tile_front * 1.2)))
            self.screen.blit(label, label_rect)

    def _draw_player_orb(self):
        if self.player_node_id is None and not self.is_moving:
            return
        world_pos = self._get_player_world_position()
        center = (
            int(world_pos.x + self.camera_offset.x),
            int(world_pos.y + self.camera_offset.y - int(self.tile_size * 0.18)),
        )
        base_radius = int(self.tile_size * 0.18)
        pulse = 1 + 0.12 * math.sin(self.player_orb_phase * 2)
        radius = max(6, int(base_radius * pulse))
        orb_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(orb_surface, (80, 255, 180, 60), (radius * 2, radius * 2), radius)
        pygame.draw.circle(orb_surface, (120, 255, 200, 160), (radius * 2, radius * 2), int(radius * 0.7))
        pygame.draw.circle(orb_surface, (200, 255, 200, 220), (radius * 2, radius * 2), int(radius * 0.35))
        orb_rect = orb_surface.get_rect(center=center)
        self.screen.blit(orb_surface, orb_rect)

    def _draw_hint(self):
        hint_text = "绿色光球表示当前位置，先点击相邻节点查看详情，再次点击确认并播放移动动画。"
        hint = self.info_font.render(hint_text, True, (210, 220, 240))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.95)))
        self.screen.blit(hint, hint_rect)

    def _draw_legend(self):
        types_order = ["entry", "normal", "elite", "boss", "supply"]
        margin = int(24 * UI_SCALE)
        box_size = int(26 * UI_SCALE)
        gap = int(10 * UI_SCALE)
        vertical_gap = int(8 * UI_SCALE)
        max_text_width = 0
        labels = []
        for node_type in types_order:
            style = self.node_type_styles.get(node_type)
            if not style:
                continue
            text_surface = self.small_font.render(style["label"], True, (235, 240, 255))
            labels.append((node_type, style, text_surface))
            max_text_width = max(max_text_width, text_surface.get_width())
        if not labels:
            return

        panel_width = margin * 2 + box_size + gap + max_text_width
        panel_height = margin + len(labels) * box_size + max(0, len(labels) - 1) * vertical_gap + margin // 2
        panel_rect = pygame.Rect(margin, int(WINDOW_HEIGHT * 0.16), panel_width, panel_height)

        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        border_radius = int(12 * UI_SCALE)
        pygame.draw.rect(panel_surface, (10, 18, 30, 170), panel_surface.get_rect(), border_radius=border_radius)
        pygame.draw.rect(panel_surface, (40, 80, 110, 200), panel_surface.get_rect(), width=2, border_radius=border_radius)

        y = margin // 2
        for node_type, style, text_surface in labels:
            box_rect = pygame.Rect(margin, y, box_size, box_size)
            box_surface = pygame.Surface((box_size, box_size), pygame.SRCALPHA)
            box_surface.fill((*style["color"], style.get("alpha", 220)))
            pygame.draw.rect(box_surface, (0, 0, 0, 60), box_surface.get_rect(), width=1, border_radius=int(box_size * 0.2))
            panel_surface.blit(box_surface, box_rect.topleft)
            text_rect = text_surface.get_rect(midleft=(box_rect.right + gap, box_rect.centery))
            panel_surface.blit(text_surface, text_rect)
            y += box_size + vertical_gap

        self.screen.blit(panel_surface, panel_rect.topleft)

    def get_hovered_card(self, mouse_pos):
        """迷宫场景没有卡牌提示"""
        return None

    def _reset_progress(self):
        self.is_moving = False
        self.move_start_id = None
        self.move_target_id = None
        self.move_progress = 0.0
        self.selected_target_id = None
        self.detail_panel.hide()
        try:
            if os.path.exists(self.SAVE_PATH):
                os.remove(self.SAVE_PATH)
        except OSError as err:
            print(f"[ActivityMazeScene] 无法删除存档: {err}")
        try:
            if os.path.exists(self.temp_deck_path):
                os.remove(self.temp_deck_path)
        except OSError as err:
            print(f"[ActivityMazeScene] 无法删除临时卡组: {err}")
        self.nodes = []
        self.nodes_by_id = {}
        self.connections = []
        self.player_node_id = None
        self._load_or_create_maze(force_reload=True)
