---
name: solidworks-parametric
description: Use whenever the user mentions CAD, SolidWorks, SW, 3D建模, 零件, 螺栓, 鼠标, 参数化, or any mechanical part design — even in passing. Triggers on "CAD", "画个", "create a", "建模", "M6/M8/M10", "gaming mouse", "SolidWorks". Requires solidworks-automation skill. Use for any CAD part request — modify the SPEC dictionary at the top of the matching script and re-run.
---

# SolidWorks 参数化建模

基于 `solidworks-automation` 的扩展技能，提供可复用的参数化零件生成器。

## 依赖

必须先安装 `solidworks-automation` 技能：
```bash
npx github:wzyn20051216/solidworks-automation-skill
```

## 工作流程

```
用户说"创建XXX" → 找对应脚本 → 改顶部参数 → python 执行 → 验证文件
```

## 可用脚本

| 脚本 | 用途 | 参数修改 |
|------|------|----------|
| `scripts/create_bolt.py` | 螺栓(六角头+螺杆+螺纹+倒角) | 改 `BOLT_SPEC` 字典 |
| `scripts/create_gaming_mouse.py` | 游戏鼠标(主体+按键+滚轮+侧键) | 改 `MOUSE_SPEC` 字典 |

## 使用方法

### 螺栓

```bash
python scripts/create_bolt.py
```

顶部 `BOLT_SPEC` 可改：
- `head_across_flats` — 六角对边宽 (M6=10, M8=13, M10=17)
- `shaft_diameter` — 螺杆直径 (M6=6, M8=8, M10=10)
- `shaft_length` — 螺杆长度
- `thread_pitch` — 螺距 (M6粗牙=1.0, M8=1.25, M10=1.5)
- `thread_length` — 螺纹段长度

### 游戏鼠标

```bash
python scripts/create_gaming_mouse.py
```

顶部 `MOUSE_SPEC` 可改：
- `body_length/width/height` — 外形尺寸
- `wheel_dia` — 滚轮直径
- `btn_split_dist` — 按键分切线位置
- 侧键、DPI键、脚贴尺寸

## 输出

每个脚本自动：
1. 保存 `.sldprt` (SolidWorks 原生格式)
2. 导出 `.step` (通用交换格式)
3. 运行 `run_review()` 生成预览图和审查报告

输出到 `C:\temp\` (可改脚本中的 `OUTPUT_DIR`)。

## 添加新零件

复制任一脚本，改顶部 SPEC 字典和建模函数。遵循模式：

```python
# 1. 定义规格
SPEC = { "param": value, ... }

# 2. 分步建模函数
def create_body(model, ext, nd, spec): ...
def add_features(model, ext, nd, spec): ...

# 3. 主流程
def main():
    session = SolidWorksSession()
    model = session.new_part()
    # 调用建模函数...
    session.save(model, path)
    session.export(model, step_path)
```

## COM 接口限制

SolidWorks 2025 的 pywin32 COM 桥接存在已知限制，详见 `references/com-limitations.md`。

关键点：
- 平面面选择正常，圆柱面仅草图平面(z=0)可选中
- `SelectByID2` 必须用 `create_empty_dispatch_variant()` 而非 `None`
- `InsertCosmeticThread` 需先选中圆柱面(在 z≈0 处选)
- 特征树遍历和 RunMacro2 不兼容
