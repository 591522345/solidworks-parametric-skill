# SolidWorks Parametric Modeling Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 [solidworks-automation](https://github.com/wzyn20051216/solidworks-automation-skill) 的参数化零件生成技能。

通过修改顶部参数字典，一键生成不同规格的 CAD 零件。

## 前置依赖

```bash
npx github:wzyn20051216/solidworks-automation-skill
```

## 快速开始

### M6 螺栓
```bash
python scripts/create_bolt.py
```

输出: `C:\temp\bolt.sldprt` + `bolt.step`

改 `BOLT_SPEC` 字典生成 M8/M10/... 任意规格。

### 游戏鼠标
```bash
python scripts/create_gaming_mouse.py
```

输出: `C:\temp\gaming_mouse.sldprt` + `gaming_mouse.step`

改 `MOUSE_SPEC` 字典调整外形尺寸。

## 目录结构

```
solidworks-parametric/
├── SKILL.md                      # 技能文件(Claude/Codex 读取)
├── README.md                     # GitHub 说明
├── scripts/
│   ├── create_bolt.py            # 螺栓参数化生成器
│   └── create_gaming_mouse.py    # 游戏鼠标参数化生成器
└── references/
    └── com-limitations.md        # SW2025 COM 接口限制记录
```

## 添加新零件

1. 复制 `create_bolt.py`
2. 改顶部 `X_SPEC` 字典
3. 改写建模函数
4. `python scripts/新脚本.py`

## 技能安装

### Claude Code
```bash
# 克隆到 skills 目录
git clone https://github.com/YOUR_USERNAME/solidworks-parametric-skill.git \
  ~/.claude/skills/solidworks-parametric
```

### OpenClaw / Codex
```bash
git clone https://github.com/YOUR_USERNAME/solidworks-parametric-skill.git \
  ~/.agents/skills/solidworks-parametric
```

## License

MIT — 详见 [LICENSE](LICENSE)
