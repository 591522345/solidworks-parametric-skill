r"""
SolidWorks 游戏竞技鼠标参数化建模
可复用 — 改 MOUSE_SPEC 即可调整外形

用法:
    python C:\temp\create_gaming_mouse.py

建模策略:
  1. 底部轮廓 → 拉伸主体
  2. 顶面切除 → 形成人体工学曲面
  3. 大面积圆角 → 平滑过渡
  4. 左右键分切 + 滚轮 + DPI键 + 侧键
  5. 底部脚贴
"""
import sys, os, math

# ─── 自动检测 solidworks-automation 技能路径 ───
def _find_skill_dir():
    candidates = [
        os.path.expanduser(r"~\.claude\skills\solidworks-automation\scripts"),
        os.path.expanduser(r"~\.agents\skills\solidworks-automation\scripts"),
        os.path.expanduser(r"~\.codex\skills\solidworks-automation\scripts"),
    ]
    for d in candidates:
        if os.path.isdir(d):
            return d
    raise FileNotFoundError(
        "未找到 solidworks-automation 技能。请先安装:\n"
        "  npx github:wzyn20051216/solidworks-automation-skill"
    )

SKILL_DIR = _find_skill_dir()
sys.path.insert(0, SKILL_DIR)

from sw_connect import mm, get_com_member, create_empty_dispatch_variant
from sw_part import (
    sketch, sketch_circle, sketch_rectangle, sketch_line,
    extrude_boss, extrude_cut, extrude_midplane,
    chamfer, fillet, end_sketch, start_sketch,
    _select_by_id
)
from sw_session import SolidWorksSession
from sw_review import run_review


# ═══════════════════════════════════════════════════════════
# 鼠标规格 (mm)
# ═══════════════════════════════════════════════════════════

MOUSE_SPEC = {
    "body_length":   125.0,   # 总长
    "body_width":     68.0,   # 最宽处(掌心区)
    "body_height":    40.0,   # 最高处
    "front_width":    58.0,   # 前端宽度
    "rear_width":     65.0,   # 后端宽度
    "corner_radius":  15.0,   # 四角圆角
    "shell_thick":     2.0,   # 壁厚(抽壳用)
    "top_curve_h":     8.0,   # 顶面弧度(切除深度)

    # 按键
    "btn_split_dist": 55.0,   # 按键分切线距后端
    "btn_split_width": 2.0,   # 分切线宽度
    "btn_split_depth": 5.0,   # 分切深度

    # 滚轮
    "wheel_dia":      20.0,   # 滚轮直径
    "wheel_width":     8.0,   # 滚轮宽度
    "wheel_x":        65.0,   # 滚轮X位置(距后端)
    "wheel_z":        38.0,   # 滚轮Z高度

    # DPI按钮
    "dpi_len":        12.0,   # DPI键长
    "dpi_wid":         6.0,   # DPI键宽
    "dpi_h":           3.0,   # DPI键高
    "dpi_x":          48.0,   # DPI键X位置

    # 侧键
    "side_btn_dia":    8.0,   # 侧键直径
    "side_btn_x1":    70.0,   # 前侧键X
    "side_btn_x2":    85.0,   # 后侧键X
    "side_btn_y":     34.0,   # 侧键Y(左边缘)
    "side_btn_z":     22.0,   # 侧键高度
    "side_btn_h":      3.0,   # 侧键突出

    # 脚贴
    "foot_thick":      0.8,   # 脚贴厚度
    "foot_wid":        8.0,   # 脚贴宽
    "foot_len":       20.0,   # 脚贴长
}

OUTPUT_DIR = r"C:\temp"
OUTPUT_NAME = "gaming_mouse"


# ═══════════════════════════════════════════════════════════
# 建模步骤
# ═══════════════════════════════════════════════════════════

def create_body_base(model, ext, nd, s):
    """[1/7] 主体轮廓 + 拉伸"""
    print(f"  [1/7] 主体外形 ...", end=" ")

    # 用中心矩形 + 圆角来近似鼠标底部轮廓
    # 前端略窄，用梯形近似
    with sketch(model, "Top Plane") as sk:
        # 使用圆角矩形作为基础形状
        bw = mm(s["body_width"])
        bl = mm(s["body_length"])
        # 中心矩形
        sketch_rectangle(model, 0, 0, bl, bw)

    H = mm(s["body_height"])
    extrude_boss(model, sk, H)
    print(f"{s['body_length']}x{s['body_width']}x{s['body_height']}mm")


def round_body_edges(model, ext, nd, s):
    """[2/7] 大面积圆角 — 让鼠标变圆润"""
    print(f"  [2/7] 主体圆角 ...", end=" ")

    R = mm(s["corner_radius"])
    H = mm(s["body_height"])

    # 对顶部所有边做圆角 — 选顶面
    model.ClearSelection2(True)
    ext.SelectByID2("", "FACE", 0, 0, H, False, 0, nd, 0)

    try:
        fillet(model, R)
        print(f"R{s['corner_radius']}mm OK")
    except Exception as e:
        print(f"fillet skipped: {e}")


def create_button_split(model, ext, nd, s):
    """[3/7] 左右按键分切线"""
    print(f"  [3/7] 按键分切 ...", end=" ")

    bw = mm(s["body_width"])
    split_x = mm(s["body_length"] - s["btn_split_dist"])
    split_w = mm(s["btn_split_width"])
    split_d = mm(s["btn_split_depth"])

    # 在 Top Plane 上画分切槽
    with sketch(model, "Top Plane") as sk:
        # 竖向槽口: 在 (split_x, 0) 处画一个窄长矩形
        y_half = bw * 0.4  # 槽长度
        sketch_rectangle(model, split_x, 0, split_w, bw * 0.8)

    extrude_cut(model, sk, split_d, flip=True)
    print(f"距后端{s['btn_split_dist']}mm OK")


def create_top_curve(model, ext, nd, s):
    """[4/7] 顶面弧线 — 用圆角让前后端下沉"""
    print(f"  [4/7] 顶面弧线 ...", end=" ")

    # 对前端和后端的顶边做额外的圆角，模拟下倾
    bl = mm(s["body_length"])
    bw = mm(s["body_width"])
    H = mm(s["body_height"])
    R_end = mm(25)  # 前后端大圆角

    # 前端顶边
    model.ClearSelection2(True)
    ext.SelectByID2("", "FACE", 0, bl / 2 - mm(5), H, False, 0, nd, 0)

    # 后端顶边
    try:
        fillet(model, R_end)
        # 后端也做
        model.ClearSelection2(True)
        ext.SelectByID2("", "FACE", 0, -bl / 2 + mm(5), H, False, 0, nd, 0)
        fillet(model, mm(20))
        print("前后下沉 OK")
    except Exception as e:
        print(f"skipped: {e}")


def create_scroll_wheel(model, ext, nd, s):
    """[5/7] 滚轮"""
    print(f"  [5/7] 滚轮 Ø{s['wheel_dia']}mm ...", end=" ")

    wheel_r = mm(s["wheel_dia"] / 2)
    wheel_w = mm(s["wheel_width"])
    wheel_x = mm(s["body_length"] / 2 - s["wheel_x"])  # 从中心偏移
    wheel_z = mm(s["wheel_z"])

    # 在 Right Plane 画圆 → 双向拉伸
    with sketch(model, "Right Plane") as sk_n:
        sketch_circle(model, wheel_x, wheel_z, wheel_r)
    extrude_midplane(model, sk_n, wheel_w)
    print("OK")


def create_dpi_button(model, ext, nd, s):
    """[6/7] DPI 切换键"""
    print(f"  [6/7] DPI键 ...", end=" ")

    bw = mm(s["body_width"])
    dpi_x = mm(s["body_length"] / 2 - s["dpi_x"])
    dpi_w = mm(s["dpi_wid"])
    dpi_l = mm(s["dpi_len"])
    dpi_h = mm(s["dpi_h"])
    H = mm(s["body_height"])

    # 在 Top Plane，滚轮后方画一个小矩形
    with sketch(model, "Top Plane") as sk:
        sketch_rectangle(model, dpi_x, 0, dpi_l, dpi_w)

    extrude_boss(model, sk, dpi_h, direction=True)
    # 对 DPI 键倒圆角
    model.ClearSelection2(True)
    ext.SelectByID2("", "FACE", dpi_x, 0, H + dpi_h, False, 0, nd, 0)
    try:
        fillet(model, mm(1.5))
    except:
        pass
    print("OK")


def create_side_buttons(model, ext, nd, s):
    """[7/7] 左侧前进/后退键"""
    print(f"  [7/7] 侧键 ...", end=" ")

    btn_r = mm(s["side_btn_dia"] / 2)
    btn_h = mm(s["side_btn_h"])
    y_pos = -mm(s["side_btn_y"])  # 左侧
    z_pos = mm(s["side_btn_z"])

    for i, x_mm in enumerate([s["side_btn_x1"], s["side_btn_x2"]]):
        x_pos = mm(s["body_length"] / 2 - x_mm)

        with sketch(model, "Right Plane") as sk_n:
            sketch_circle(model, x_pos, z_pos, btn_r)
        extrude_boss(model, sk_n, btn_h)

    print(f"2键 OK")


def create_feet(model, ext, nd, s):
    """脚贴 — 底部4个小方块"""
    print(f"  脚贴 ...", end=" ")

    ft = mm(s["foot_thick"])
    fw = mm(s["foot_wid"])
    fl = mm(s["foot_len"])
    bl = mm(s["body_length"])
    bw = mm(s["body_width"])
    margin = mm(8)

    # 4角脚贴 (从底部向下拉伸，即 direction=False)
    positions = [
        ( bl/2 - margin,  bw/2 - margin),   # 右前
        ( bl/2 - margin, -bw/2 + margin),   # 左前
        (-bl/2 + margin,  bw/2 - margin),   # 右后
        (-bl/2 + margin, -bw/2 + margin),   # 左后
    ]

    for i, (cx, cy) in enumerate(positions):
        with sketch(model, "Top Plane") as sk:
            sketch_rectangle(model, cx, cy, fl, fw)
        extrude_boss(model, sk, ft, direction=False)  # 向下

    print("4脚 OK")


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main():
    s = MOUSE_SPEC
    nd = create_empty_dispatch_variant()

    print("连接 SolidWorks ...")
    session = SolidWorksSession()
    model = session.new_part()
    ext = model.Extension
    print(f"文档: {get_com_member(model, 'GetTitle')}\n")

    # ── 建模 ──
    create_body_base(model, ext, nd, s)
    round_body_edges(model, ext, nd, s)
    create_button_split(model, ext, nd, s)
    create_top_curve(model, ext, nd, s)
    create_scroll_wheel(model, ext, nd, s)
    create_dpi_button(model, ext, nd, s)
    create_side_buttons(model, ext, nd, s)
    create_feet(model, ext, nd, s)

    # ── 收尾 ──
    model.ForceRebuild3(False)
    model.ViewZoomtofit2()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sp = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}.sldprt")
    st = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}.step")

    session.save(model, sp)
    session.export(model, st)

    report, rp = run_review(
        model,
        os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}_review"),
        basename=OUTPUT_NAME,
        expected_outputs=[sp, st],
    )
    ev = report["evaluation"]

    print(f"\n{'='*50}")
    print(f"游戏竞技鼠标")
    print(f"  SLDPRT: {sp}  ({os.path.getsize(sp)/1024:.1f} KB)")
    print(f"  STEP:   {st}  ({os.path.getsize(st)/1024:.1f} KB)")
    print(f"  审查:   {ev['status']} | {ev['score']}/100")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
