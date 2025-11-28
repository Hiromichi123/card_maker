# Card Battle Master

![menu Overview Placeholder](docs/screenshots/menu_overview.png)

一款基于Pygame的卡牌对战原型，支持卡池生成、准备区冷却、技能触发动画等完整战斗流程。该项目主要用于实验各种卡牌机制并快速验证视觉/数值表现。

## 功能概览

- **自定义卡池**：读取 `assets/outputs` 下的卡牌数据，自动匹配图片与属性。
- **战斗场景**：包含手牌、战斗区、准备区、弃牌堆、血条、回合指示等 UI 元素。
- **技能系统**：支持多触发时机（上场、攻击前/后、受伤前后、死亡等），并内置 Blessing/Curse/Silence/Armor Break 等多种效果与动画。
- **动画框架**：所有技能/攻击/位移动画统一由队列管理，可叠加粒子、拖尾、光效等表现。

## 快速开始

1. 确保已安装 Python 3.10+ 与 pip。
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 运行游戏：

   ```bash
   python main.py
   ```

4. 制作自定义卡牌

   ```bash
   python maker.py
   ```

> ⚠️ Pygame 需要本地窗口环境；在无图形界面服务器上运行时请使用虚拟显示。

## 运行流程

1. **加载卡池**：启动时根据稀有度目录解析 `cards.json`，生成 `CardData` 实例。
2. **初始化场景**：创建战斗区/准备区槽位、手牌管理器、血条、按钮等组件。
3. **出牌与冷却**：手牌出牌后进入准备区，等待 CD 归零自动移入战斗槽位并触发 OnDeploy 技能。
4. **战斗阶段**：双方依次攻击，按技能触发时机执行动画与数值逻辑。
5. **结算与清理**：死亡卡进入弃牌堆，处理不死/复活等被动效果，回合结束前整理槽位。

## 技能示例

| 技能 | 触发 | 效果说明 |
| ---- | ---- | -------- |
| 祝福n / 群体祝福n | 攻击前 | 友方 ATK/HP 提升并播放金色光球+粒子动画 |
| 振奋n / 群体振奋n | 上场 | 友方 ATK 提升，展示剑形标记动画 |
| 沉默 | 被动 | 禁用对位敌方所有技能（但可普攻） |
| 诅咒n | 攻击前 | 降低对位敌方 ATK，同时播放紫色诅咒标记 |
| 破甲n | 攻击前 | 无视目标 n 点防御，盾牌动画同步出现裂纹标记 |

更多技能定义见 `game/skills/skill_effects.py` 与 `game/skills/skill_registry.py`。

## 界面预览

### 战斗主界面

![Battle Overview Placeholder](docs/screenshots/battle_overview.png)

### 抽卡界面

![gacah_menu Placeholder](docs/screenshots/gacha_menu.png)

### 卡牌编辑/生成界面

![Card Editor Placeholder](docs/screenshots/card_editor.png)

## 项目结构

```text
card_maker/
├─ assets/                # 图片与卡牌数据
├─ game/                  # 核心逻辑（技能、动画、数据结构）
├─ scenes/                # 场景与状态管理
├─ utils/                 # 通用工具（卡池、组件、缓存）
├─ maker.py               # 游戏入口
└─ README.md
```

## 开发计划

- [ ] 扩展 AI 行为与自动对战脚本。
- [ ] 增加更多被动/触发技能模板及可配置参数。
- [ ] 增强 UI（拖拽出牌、设置菜单、音效控制等）。
- [ ] 设计完整的剧情/关卡流程。

## 贡献

欢迎提交 Issue/PR 讨论新技能、UI 表现或性能优化。提交前请：

1. 使用 `black`/`flake8`（或项目内置脚本）格式化/检查代码。
2. 附上关键功能的运行截图或录像。
3. 简述改动范围及潜在影响。

## 许可

目前项目仅供个人学习与展示，暂未指定正式开源协议。如需引用，请注明来源并联系作者。
游戏可以免费下载
