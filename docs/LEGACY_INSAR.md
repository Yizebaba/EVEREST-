# 早期文档：InSAR 管线（存档）

> 这是项目最早的 README 内容，原样保留，方便追溯和复原。**其中的“预警”“风险评估”、固定的 0.66 mm 位移、Windy 插件等设想已不在平台范围内**：平台现在只监测、不预测、不发布预警；每日管线的位移改为读取云端干涉的真实结果，没有新结果就标“不可观测”。现行说明见仓库根目录 [README](../README.md)。


<a name="english"></a>
### English Overview

**Everest Anomaly Engine** is an autonomous, cloud-native Sentinel-1 InSAR processing, physical constraint screening, and multi-hazard early warning pipeline designed for the Mount Everest region. It implements the **L0~L4 Five-Layer Architecture** and enforces the supreme operational axiom:

$$\mathbf{Detection \neq Warning}$$
*(An anomaly does not equal a disaster warning; candidates must pass physical gating, cross-source validation, and human review before generating an alert).*

```text
                              Everest                                
                                │
        =================================================
        │                       │                       │
        ▼                       ▼                       ▼
   Sentinel-1              Sentinel-2                DEM
   SAR                     Optical                   Terrain
        │                       │                       │
        ▼                       ▼                       ▼
 SAR Feature             Optical Feature          Terrain Feature
 - Backscatter           - RGB                    - Elevation
 - Coherence             - NIR                    - Slope
 - Phase                 - SWIR                   - Aspect
 - Texture               - NDVI/NDSI              - Curvature
                         - Snow Index             - Glacier Basin
        │                       │                       │
        =========================                       │
                    │                                   │
                    ▼                                   │
        =================================               │
        │                              │                │
        ▼                              ▼                │
 Glacier Motion                  Glacier Mapping        │
 冰川运动                         冰川范围              │
        │                              │                │
        ▼                              ▼                │
 ITS_LIVE                         GlaViTU               │
 autoRIFT                         GlacierNet            │
 CC-ResSiamNet                    DeepLab/U-Net         │
        │                              │                │
        ▼                              ▼                │
 Glacier Velocity                 Glacier Mask          │
 Time Series                      Glacier Boundary      │
        │                              │                │
        ▼                              │                │
 Velocity Anomaly                  Glacier Change       │
 Detection                         Detection            │
        │                              │                │
        =================================                │
                         │                              │
                         ▼                              ▼
              Glacier State Database  <-----------------
              冰川状态数据库
============================================================
              Sentinel-1 SAR变化模块 ➔ InSAR ➔ Deformation Map ➔ Glacier Stability
              Sentinel-2 变化模块 ➔ AnyChange / ChangeFormer ➔ Crevasse Detection
              Sentinel-2 + SAR ➔ Lake Detection ➔ GLOF Module (冰湖溃决风险)
              Sentinel-2 + SAR + DEM ➔ Avalanche / Icefall Module (冰崩雪崩动力学)
              DEM Terrain Layer ➔ Physical Constraint Layer (陡坡/末端/重力硬门禁)
============================================================
                 外部环境数据: Weather (气象) + Seismic (地震动)
                                 │
                                 ▼
        Remote Sensing Foundation Models (Copernicus-FM / RobSense / Prithvi)
                                 │
                                 ▼
              Multi-modal Feature Fusion ➔ Everest Anomaly Engine
                                 │
                                 ▼
        Persistence + Spatial Consistency + Cross Validation + Physics Constraint
                                 │
                                 ▼
              Event Candidate ➔ Human Review ➔ Alert
```

### Key Technical Pillars
1. **L0 Data & Sensing**: Precise overpass sensing via Copernicus CDSE OData API (Burst 23790 IW1/VV, Orbit 12 Ascending).
2. **L1/L2 Glacier Dynamics**:
   - **NASA ITS_LIVE Streaming**: Direct cloud streaming from AWS S3 Zarr datacube, extracting 39-year baseline velocity (mean: `12.27 m/yr`) and Z-Score anomaly.
   - **Real 2D InSAR Inversion**: Adaptive bedrock anchor calibration at $(Y=285, X=613)$ with Coherence = `0.965`, yielding `0.66 mm` median LOS micro-creep across 20,278 pixels.
   - **RGI 7.0 & GlaViTU Bridge**: Spatial topology verification against Khumbu, Rongbuk, and Kangshung glaciers.
3. **L3 Multi-Hazard Pipelines**:
   - **Crevasse Detection**: Optical texture gradient and extensional fracture field modeling.
   - **GLOF Module**: Expansion tracking and moraine dam stability assessment.
   - **Avalanche Mechanics**: Gravitational potential energy on critical slopes ($28^\circ \sim 55^\circ$).
   - **DEM Physics Gate**: Hard veto on radar layover/shadow artifacts ($>38^\circ$) and physically impossible events.
4. **L4 Everest Anomaly Engine**: Quantitative multi-source fusion, persistence scoring, and uncertainty attribution.

---

## 📦 Package Release & Installation

The core engine is packaged and published as a standard Python Wheel package (`everest-glacier-engine`).

```bash
# Install directly via pip from GitHub Releases:
pip install https://github.com/Yizebaba/everest-insar-pipeline/releases/download/v1.0.0/everest_glacier_engine-1.0.0-py3-none-any.whl

# Or install from source:
pip install git+https://github.com/Yizebaba/everest-insar-pipeline.git
```

### CLI Execution
```bash
everest-glacier
```

### Python SDK & AI Agent Invocation
```python
from pipeline import run_real_pipeline
from models.glacier_state_database import GlacierStateDatabase
from models.cloud_services_adapter import CloudGlacierVelocityService, CloudInSARSAMAdapter
from models.dem_physical_constraint import DEMPhysicalConstraintLayer

# 1. Fetch real 39-year NASA ITS_LIVE velocity baseline from AWS S3 cloud
its = CloudGlacierVelocityService()
v_state = its.fetch_real_glacier_velocity_series()
print(f"39-year baseline: {v_state['historical_baseline_mean_m_yr']} m/yr, Z-score: {v_state['velocity_anomaly_z_score']}")

# 2. Evaluate DEM physical constraint gate
dem_gate = DEMPhysicalConstraintLayer()
physics = dem_gate.evaluate_physical_feasibility(elevation_m=5800, slope_deg=32.5, aspect_deg=185, hazard_type="insar_displacement")
print(f"Physical constraint status: {physics['physical_constraint_status']}")

# 3. Query persistent Glacier State Database
db = GlacierStateDatabase()
summary = db.get_latest_glacier_summary()
print(f"Recorded glacier state inventory count: {len(summary)}")
```

---

<a name="chinese"></a>
## 中文说明

**珠穆朗玛峰多源冰川与 InSAR 全自动解算分析引擎（v5.0 终极版）**。

### 核心设计与科学法则
本系统坚守防灾减灾最高科学红线：**检测到异常 $\neq$ 灾害预警（$\mathbf{Detection \neq Warning}$）**。
通过多源异构卫星（Sentinel-1/2、Landsat、Copernicus DEM）与外部环境（气象/地震），构建了五大平行物理管道与 DEM 物理约束门禁。

### 六大落地核心能力
1. **全自动卫星过境嗅探**：在北京时间晚间过境窗口期，自动通过 CDSE OData 接口捕获最新过境切片（Burst 23790）。
2. **NASA MEaSUREs ITS_LIVE 云端流式计算**：
   - 彻底摆脱本地繁重算力，直接通过 HTTP Range 零下载流式切片读取 AWS S3 上的 Zarr 数据立方体；
   - 提取珠峰孔布冰川 39 年（1985-2024）真实流速序列（均值 12.27 米/年），动态计算 Z-Score 速度异常度。
3. **真实 2D 矩阵 InSAR 毫米级位移反演**：
   - 消除硬编码，动态加载 20,278 像元真实数组；
   - 自动在坐标 $(Y=285, X=613)$ 锁定相干性高达 **0.965** 的天然不动基岩；
   - 算得视线向位移中位数 **`0.66 毫米`**，评估为微小缓慢蠕变（`HIGHLY_STABLE_MICRO_CREEP`）。
4. **专项灾害管道全面落地**：
   - **冰裂缝检测 (Crevasse)**：基于高频空间梯度与构造主应力走向，生成破裂斑块；
   - **冰湖溃决风险 (GLOF)**：以伊姆扎湖（Imja Tsho）为目标，结合扩张率与冰碛坝雷达相干性量化风险；
   - **雪崩/冰崩动力学**：输入高程落差与坡度，计算重力失稳指数；
   - **DEM 物理约束门禁**：对坡度 $>38^\circ$ 极易产生雷达叠掩/阴影的区域实施**一票否决**，杜绝假阳性。
5. **冰川状态数据库 (Glacier State Database)**：
   - 内置 SQLite 引擎，沉淀孔布、绒布、康雄三大冰川历史档案，每次过境自动写入动态物理状态日志。
6. **L4 Everest Anomaly Engine 综合判定**：
   - 整合持续性、空间一致性、多源交叉验证、物理门禁、置信度（62%）与不确定性（38%），给出最终综合裁决。

---

### 双仓全自动闭环架构
1. **后端算力调度仓**：[`Yizebaba/everest-insar-pipeline`](https://github.com/Yizebaba/everest-insar-pipeline)（本仓库，负责侦听、解算、平差、物理门禁与综合决策）。
2. **前端地图插件仓**：[`Yizebaba/hqmw-cryosphere-windy`](https://github.com/Yizebaba/hqmw-cryosphere-windy)（接收后端推来的成果，在 Windy 真实地图上渲染基岩不动点、形变连线、SAM 红色闭合面与 NASA 流速热力带）。
   - **在线插件加载地址**：`https://windy-plugins.com/17744505/windy-plugin-everest-mhews/3.1.14/plugin.min.js`
