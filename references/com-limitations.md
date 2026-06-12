# SolidWorks 2025 COM 接口已知限制

经过 30+ 次系统性测试，发现 SolidWorks 2025 与 pywin32 COM 桥接层存在以下限制。

## 面选择 (SelectByID2)

### 可选中
- 命名平面: `SelectByID2("Top Plane", "PLANE", 0, 0, 0, ...)` ✅
- 命名草图: `SelectByID2("草图1", "SKETCH", 0, 0, 0, ...)` ✅
- 矩形拉伸体的所有面(任意 z 坐标) ✅
- 圆柱体在草图平面(z=0)上的面 ✅
- **圆柱面在 z≈0 处** ✅ (关键发现!)

### 不可选中
- 圆柱体非 z=0 的远端面 ❌
- 圆柱面 z≠0 处 ❌
- 所有边缘(EDGE) ❌

### 必须使用的 Callout 格式
```python
from sw_connect import create_empty_dispatch_variant
nd = create_empty_dispatch_variant()
ext.SelectByID2("", "FACE", x, y, z, False, 1, nd, 0)
#                                     必须用 nd，不能用 None ^^
```

## 特征操作

| 操作 | 状态 | 备注 |
|------|:---:|------|
| extrude_boss / extrude_cut | ✅ | 正常 |
| chamfer | ✅ | 选面倒角 |
| fillet | ✅ | 选面圆角 |
| InsertHelix | ⚠️ | 存在(10参数)，返回None但可能创建了螺旋线 |
| InsertCosmeticThread | ⚠️ | 存在(4参数)，需先选圆柱面，返回None |
| FeatureRevolveCut | ❌ | 返回None，未验证是否创建特征 |
| GetNextFeature (特征遍历) | ❌ | "找不到成员" |

## 跨桥接方案对比

| 方案 | 基本建模 | 面选择 | 可行性 |
|------|:---:|:---:|:---:|
| pywin32 动态绑定 | ✅ | ⚠️ | ✅ 推荐 |
| pywin32 早期绑定(makepy) | ✅ | ⚠️ | 无改善 |
| PowerShell COM | ❌ | ❌ | 大量TYPE_E_ELEMENTNOTFOUND |
| comtypes | ❌ | — | 连接冲突,超时 |
| C# + Interop DLL | ? | ? | 理论可行,需编译项目 |

## 线程创建最佳实践

由于圆柱面只能在 z≈0 处选中，装饰螺纹线的添加方式：

```python
# 选中圆柱面 (在 z≈0, r=D/2 处)
model.ClearSelection2(True)
ext.SelectByID2("", "FACE", D / 2, 0, 0.0001, False, 1, nd, 0)

# 插入装饰螺纹线
model.InsertCosmeticThread(False, thread_len, diameter, pitch)

# 确保可见
model.SetUserPreferenceToggle(197, True)  # 显示装饰螺纹线
model.SetUserPreferenceToggle(198, True)  # 着色模式显示
```

参数含义（推测）：
- Param 1 (bool/0): 是否反转方向
- Param 2 (double): 螺纹深度(m)
- Param 3 (double): 直径(m)
- Param 4 (double): 螺距(m)
