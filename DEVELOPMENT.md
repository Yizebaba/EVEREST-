# Everest InSAR Pipeline - Development & Deployment Guide (开发与部署运维指南)

[English](#english-deployment-guide) | [中文部署指南](#chinese-deployment-guide)

---

<a name="english-deployment-guide"></a>
## English Deployment Guide

This guide describes how to configure credentials, deploy the autonomous daily cron runner, and invoke the Everest Glacier Pipeline locally or in production.

### 1. Repository Secrets Configuration (GitHub Actions)
For automated daily overpass sensing, openEO processing, and cross-repo syncing to the Windy plugin, configure the following secrets under **Settings ➔ Secrets and variables ➔ Actions**:

| Secret Name | Required | Description | Example / Link |
| :--- | :---: | :--- | :--- |
| `CDSE_USERNAME` | Yes | Copernicus Data Space Ecosystem login email | Registered at `https://dataspace.copernicus.eu/` |
| `CDSE_PASSWORD` | Yes | Copernicus Data Space Ecosystem password | - |
| `GH_PAT` | Optional | GitHub Personal Access Token with `repo` and `workflow` scopes | Used to dispatch builds to `hqmw-cryosphere-windy` |
| `WINDY_API_KEY` | Optional | API key for Windy.com plugin upload node | Configured in `hqmw-cryosphere-windy` |

*Note: If `GH_PAT` is not explicitly set, the pipeline automatically falls back to GitHub Actions default `GITHUB_TOKEN`.*

### 2. Local Environment Setup & CLI Testing

#### Step A: Clone and Install
```bash
git clone https://github.com/Yizebaba/EVEREST-.git
cd everest-insar-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install package with all cloud streaming dependencies
pip install -r requirements.txt
pip install -e .
```

#### Step B: Run Verification Commands
```bash
# 1. Run the full real pipeline (L0 to L4):
everest-glacier

# 2. Run RGI 7.0 boundary extractor:
python -c "from models import GlaViTURGIBridge; b = GlaViTURGIBridge(); print(b.get_glacier_boundary_geojson()['name'])"

# 3. Stream real NASA ITS_LIVE 39-year velocity baseline from AWS S3:
python -c "from models import CloudGlacierVelocityService; s = CloudGlacierVelocityService(); print(s.fetch_real_glacier_velocity_series()['historical_baseline_mean_m_yr'])"
```

### 3. Architecture Component Verification Checklist
- [x] **L0 Data Sensing**: Connects to Copernicus OData API for Sentinel-1 Track 12 overpasses.
- [x] **L1/L2 InSAR Calibration**: Evaluates 20,278 pixels from `data/everest_insar_los_displacement_candidates_mm.npy` against bedrock anchor $(Y=285, X=613)$.
- [x] **L1/L2 NASA Velocity**: Directly reads AWS S3 cloud Zarr via `s3fs`/`fsspec` without local heavy download.
- [x] **L3 Hazard Gates**: Evaluates GLOF lake expansion, Crevasse spatial gradient, Avalanche potential, and DEM layover veto.
- [x] **L4 Anomaly Decision**: Computes Persistence, Spatial Consistency, Confidence, and Uncertainty before candidate promotion.

---

<a name="chinese-deployment-guide"></a>
## 中文部署指南

本指南详细说明了环境变量配置、自动化定时调度部署以及本地开发运行步骤。

### 1. GitHub 仓库密钥配置 (GitHub Actions 必需)
在您的 Fork 仓库或主仓库的 **Settings ➔ Secrets and variables ➔ Actions** 中配置以下密钥变量：

1. **`CDSE_USERNAME`**：欧空局哥白尼账号（邮箱），用于登录 CDSE OData 与 openEO 服务；
2. **`CDSE_PASSWORD`**：欧空局哥白尼账号密码；
3. **`GH_PAT`**：具有 `repo` 和 `workflow` 权限的 GitHub 访问令牌（用于后端算完后自动把数据写入 `hqmw-cryosphere-windy` 并触发构建，若不填则默认仅在当前仓内更新）；
4. **`WINDY_API_KEY`**：Windy 插件官方上传秘钥（在前端插件仓 `hqmw-cryosphere-windy` 中配置）。

### 2. 自动化触发机制 (CI/CD Schedule)
工作流文件 `.github/workflows/daily-pipeline.yml` 预置了两个触发通道：
- **定时卫星侦听 (Cron)**：在 Sentinel-1 升轨 12 轨过境数据下发黄金窗口期（北京时间 22:00, 00:00, 02:00）每 2 小时精准检测一次；每天早晨 10:00 保底运行一次；
- **手动调度 (Workflow Dispatch)**：在 GitHub Actions 界面随时点击 **Run workflow** 即可全量触发。

### 3. 常见问题与排查 (Troubleshooting)
- **Q: 为什么提示 `No module named zarr` 或 `s3fs`？**  
  A: 本项目采用 S3 云流式零拷贝切片读取，需安装完整依赖：`pip install -r requirements.txt`。
- **Q: `everest-glacier` 命令报找不到？**  
  A: 请确保使用 `pip install -e .` 或直接安装发布的 Wheel 轮子包（v1.0.1+），此时控制台命令 `everest-glacier` 会自动注册到 PATH 中。