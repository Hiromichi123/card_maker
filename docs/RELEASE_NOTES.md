# Card Battle Master v1.0.0 🎮

**发布日期：** 2024-12-02

## 简介

Card Battle Master 是一款基于 Pygame 的卡牌对战游戏，提供完整的卡牌收集、卡组构建和战斗系统。

## 🌟 核心特性

- **完整战斗系统** - 支持玩家 vs AI 和本地双人对战
- **丰富游戏模式** - 关卡挑战、迷宫探索、工坊融合
- **技能系统** - 多种触发时机和技能效果
- **卡牌管理** - 抽卡、收藏、卡组构建一应俱全
- **制作工具** - 内置卡牌制作工具，支持自定义卡牌

## ⚡ 性能优化

经过全面优化，游戏性能提升 **2-4 倍**：
- Battle 场景：40 → 100 FPS (2.5x)
- Menu 场景：40 → 120 FPS (3x)
- WorldMap 场景：30 → 120 FPS (4x)
- Maze 场景：20 → 80 FPS (4x)

## 📦 安装运行

### 系统要求
- Python 3.10+
- Windows / macOS / Linux
- 图形界面支持

### 快速开始
```bash
# 1. 克隆项目
git clone https://github.com/Hiromichi123/card_maker.git
cd card_maker

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行游戏
python main.py

# 4. （可选）运行卡牌制作工具
python maker.py
```

## 🎮 游戏玩法

### 战斗系统
- 出牌到准备区，等待 CD 结束自动进入战斗
- 战斗区卡牌依次攻击对手
- HP 归零或无卡牌时判负

### 技能系统
支持多种触发时机：
- 上场（OnDeploy）
- 攻击前后（BeforeAttack, AfterAttack）
- 受伤前后（BeforeDamaged, AfterDamaged）
- 死亡（OnDeath）
- 回合开始/结束（OnTurnStart, OnTurnEnd）

### 游戏模式
- **关卡模式** - 挑战预设关卡
- **迷宫探索** - 随机事件和奖励
- **本地对战** - 双人 Draft 模式
- **工坊融合** - 消耗卡牌合成新卡

## 📖 详细文档

- [完整文档](README.md)
- [更新日志](CHANGELOG.md)
- [优化报告](docs/OPTIMIZATION_REPORT.md)
- [发布检查清单](docs/RELEASE_CHECKLIST.md)

## 🛠️ 技术栈

- **游戏引擎** - Pygame 2.5+
- **图像处理** - OpenCV, Pillow
- **数据处理** - NumPy
- **语言** - Python 3.11

## 📸 游戏截图

![Battle Scene](docs/screenshots/battle_overview.png)
![Gacha Menu](docs/screenshots/gacha_menu.png)
![Card Editor](docs/screenshots/card_editor.png)
![Main Menu](docs/screenshots/menu_overview.png)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

提交前请：
1. 确保代码风格一致
2. 测试功能正常
3. 附上必要的说明

## 📄 许可

本项目供个人学习与展示使用。游戏可免费下载和游玩。

## 👤 作者

**Hiromichi123**

## 🎯 未来计划

- [ ] 联机对战支持
- [ ] 音效和背景音乐
- [ ] 更多卡牌和技能
- [ ] 剧情模式
- [ ] 成就系统
- [ ] 增强 AI

---

**享受游戏！** 🎉
