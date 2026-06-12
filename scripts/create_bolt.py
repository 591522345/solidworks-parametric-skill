r"""
SolidWorks 螺栓参数化建模脚本
可复用、可修改 — 改顶部参数即可生成不同规格螺栓

用法:
    python C:\temp\create_bolt.py

修改螺栓规格只需改 BOLT_SPEC 字典，然后重新运行。
"""
import sys, os, math

# ─── 自动检测 solidworks-automation 技能路径 ───
def _find_skill_dir():
    """查找 solidworks-automation 技能的 scripts 目录"""
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
    sketch, sketch_circle, sketch_polygon,
    extrude_boss, chamfer, end_sketch, start_sketch
)
from sw_session import SolidWorksSession
from sw_review import run_review


# ═══════════════════════════════════════════════════════════
# 螺栓规格参数 — 改这里即可生成不同螺栓
# ═══════════════════════════════════════════════════════════

BOLT_SPEC = {
    # 六角头部
    "head_across_flats": 10.0,   # mm, 对边宽度 (M6=10)
    "head_thickness":     4.0,   # mm, 头部厚度 (M6=4)
    "head_chamfer":       0.5,   # mm, 头部倒角

    # 螺杆
    "shaft_diameter":     6.0,   # mm, 螺杆直径 (M6=6)
    "shaft_length":      30.0,   # mm, 螺杆长度

    # 螺纹
    "thread_pitch":       1.0,   # mm, 螺距 (M6粗牙=1.0)
    "thread_depth_pct": 0.6134,  # 牙深系数 (ISO外螺纹=0.6134*螺距)
    "thread_length":     24.0,   # mm, 螺纹段长度
}

# 输出路径
OUTPUT_DIR = r"C:\temp"
OUTPUT_NAME = "bolt"  # 输出文件名(不含扩展名)


# ═══════════════════════════════════════════════════════════
# 建模函数
# ═══════════════════════════════════════════════════════════

def create_bolt_head(model, ext, nd, spec):
    """创建六角头部"""
    S = mm(spec["head_across_flats"])
    H = mm(spec["head_thickness"])
    hex_r = S / math.sqrt(3)  # 六边形内切圆半径

    with sketch(model, "Top Plane") as sk:
        sketch_polygon(model, 0, 0, hex_r, sides=6)
    extrude_boss(model, sk, H)
    print(f"  [1/5] 六角头: S={spec['head_across_flats']}mm x H={spec['head_thickness']}mm")


def create_shaft(model, ext, nd, spec):
    """创建螺杆 (从 Top Plane 向下拉伸)"""
    D = mm(spec["shaft_diameter"])
    L = mm(spec["shaft_length"])

    with sketch(model, "Top Plane") as sk:
        sketch_circle(model, 0, 0, D / 2)
    extrude_boss(model, sk, L, direction=False)
    print(f"  [2/5] 螺杆: D={spec['shaft_diameter']}mm x L={spec['shaft_length']}mm")


def chamfer_head(model, ext, nd, spec):
    """头部倒角 — 选顶面自动对所有棱边倒角"""
    H = mm(spec["head_thickness"])
    CH = mm(spec["head_chamfer"])

    model.ClearSelection2(True)
    ext.SelectByID2("", "FACE", 0, 0, H, False, 0, nd, 0)
    chamfer(model, CH)
    print(f"  [3/5] 头部倒角: {spec['head_chamfer']}mm x 45°")


def add_thread(model, ext, nd, spec):
    """添加装饰螺纹线"""
    D = mm(spec["shaft_diameter"])
    thread_len = mm(spec["thread_length"])
    pitch = mm(spec["thread_pitch"])

    print(f"  [4/5] 螺纹: M{spec['shaft_diameter']}x{spec['thread_pitch']} "
          f"深度{spec['thread_length']}mm ...", end=" ")

    # 关键: 在 z≈0, r=D/2 处选中圆柱面
    model.ClearSelection2(True)
    ok = ext.SelectByID2("", "FACE", D / 2, 0, 0.0001, False, 1, nd, 0)

    if not ok:
        print("⚠ 未能选中圆柱面，跳过螺纹")
        return

    # 插入装饰螺纹线
    model.InsertCosmeticThread(False, thread_len, D, pitch)
    # 确保螺纹可见
    model.SetUserPreferenceToggle(197, True)   # 显示装饰螺纹线
    model.SetUserPreferenceToggle(198, True)   # 着色模式显示
    print("OK")


def add_end_chamfer(model, ext, nd, spec):
    """螺杆末端倒角 (可选)"""
    print(f"  [5/5] 末端倒角: 0.3mm x 45° ...", end=" ")
    # 此步可能因面选择限制而失败，不影响主体
    print("跳过 (COM限制)")


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main():
    spec = BOLT_SPEC
    nd = create_empty_dispatch_variant()

    # ── 连接 SolidWorks ──
    print("连接 SolidWorks ...")
    session = SolidWorksSession()
    model = session.new_part()
    ext = model.Extension
    print(f"新建文档: {get_com_member(model, 'GetTitle')}\n")

    # ── 建模 ──
    create_bolt_head(model, ext, nd, spec)
    create_shaft(model, ext, nd, spec)
    chamfer_head(model, ext, nd, spec)
    add_thread(model, ext, nd, spec)  # 螺纹
    add_end_chamfer(model, ext, nd, spec)

    # ── 收尾 ──
    model.ForceRebuild3(False)
    model.ViewZoomtofit2()

    # ── 保存 + 导出 ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sp = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}.sldprt")
    st = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}.step")

    session.save(model, sp)
    session.export(model, st)

    # ── 自审查 ──
    report, rp = run_review(
        model,
        os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}_review"),
        basename=OUTPUT_NAME,
        expected_outputs=[sp, st],
    )
    ev = report["evaluation"]

    # ── 报告 ──
    print(f"\n{'='*50}")
    print(f"M{spec['shaft_diameter']} x {spec['shaft_length']}mm 螺栓")
    print(f"  SLDPRT: {sp}  ({os.path.getsize(sp)/1024:.1f} KB)")
    print(f"  STEP:   {st}  ({os.path.getsize(st)/1024:.1f} KB)")
    print(f"  审查:   {ev['status']} | {ev['score']}/100")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
