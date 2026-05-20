# 🎬 SnapBatch Pro

> **让视频帧提取，变得更快、更稳、更优雅。**
> *A High-Performance, Minimalist, and Desktop-Optimized Video Frame Batch Extraction Engine Driven by PySide6 & OpenCV.*

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.8%20%7C%203.14-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework PySide6](https://img.shields.io/badge/PySide6-6.11.1-green?style=flat-square&logo=qt&logoColor=white)](https://pyside.org/)
[![Engine OpenCV](https://img.shields.io/badge/OpenCV-4.13.0-red?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org/)
[![Binary Size](https://img.shields.io/badge/Binary%20Size-55%20MB%20(Optimized)-brightgreen?style=flat-square&logo=webassembly&logoColor=white)](#-生产级编译与二进制体积压榨指南-93mb--55mb)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

[🪐 核心功能](#-核心亮点与卓越交互) • [🛠️ 技术架构](#-底层技术栈与架构设计) • [📦 立即下载](#-分发与下载通道) • [🚀 开发者指南](#-开发者快速上手) • [⚡ 编译优化](#-生产级编译与二进制体积压榨指南-93mb---55mb)

</div>

## 📖 项目深度定位

**SnapBatch Pro** 是一款专为视频创作者、多媒体素材整理师以及 AI 算法工程师（数据集预处理）打造的**现代化桌面级视频帧批量提取工具**。

市面上常见的截图工具往往操作繁琐、无法批量处理，或界面粗糙、后台同步阻塞导致软件卡死。SnapBatch 从诞生之初就确立了**“像素级界面美学”与“工业级底层并发”**双轮驱动的原则。它不仅是一个开箱即用的高效率生产力工具，更是一个极具含金量的 Python GUI 高级进阶实战作品。

---

## 🪐 核心亮点与卓越交互

<div align="center">
  <img src="assets/首页.png" alt="SnapBatch Pro 运行界面" width="85%">
  <br>
  <p><i>▲ SnapBatch Pro - 极简与暗黑美学交织的操作界面</i></p>
</div>

### 1. 💎 奢华暗黑无边框美学
摒弃了 Windows 传统的死板原生边框，像素级定制了现代化暗黑美学视窗。
* 🖥️ **物理边缘吸附 (Windows Snap Assist)**：深度重写拖拽流，完美支持双击最大化、拖动至屏幕边缘触发半屏/全屏预览及自动拉伸布局。
* 🧪 **微秒级流式动画**：侧边参数面板、动态蒙版闪烁均采用 `QPropertyAnimation` 与 `QEasingCurve.OutCubic` 缓冲曲线，提供丝滑不掉帧的动态视觉反馈。

### 2. 🧵 后台非阻塞式异步架构 (`QThread`)
拒绝界面假死。核心解码任务完全交付给独立的后台 `VideoWorker` 线程，与主 UI 线程通过 Qt 信号槽（Signals & Slots）进行微秒级异步通信，在处理成百上千个超大 4K 视频时，前台界面依旧轻盈丝滑。

### 3. 🎯 精准到毫秒的时间点截取
支持精确到小数点的秒数输入（如输入 `2.5` 提取第 2.5 秒的画面），并在底层自动计算视频总帧数与 FPS，利用 FFMPEG 硬件层加速定位，智能防御越界行为（超出时自动截取最后一帧）。

### 4. 🧠 智能日志跟随与手势拦截算法
独创的日志输出控制逻辑（`LogTextWidget`），完美解决长日志滚动条临界点漂移 Bug：
* ⚙️ **动作判定**：当鼠标滚轮向上拨动或键盘触发向上翻页时，零延迟锁死自动跟随，方便用户复盘历史日志。
* 📐 **绝对像素差值算法**：滑块距离底部绝对差值 $\le 10$ 像素时自动恢复跟随，交互体验极其直观。

### 5. 🧲 智能拖拽识别 (`Drag & Drop`)
输入框无缝集成 `ModernLineEdit` 底层引擎，用户无需繁琐地点击浏览，直接从资源管理器中将包含视频的文件夹拖拽掷入界面，即可瞬间完成路径解析。

---

## 🛠️ 底层技术栈与架构设计

项目采用纯本地化离线架构，无任何外部网络依赖，数据安全性达到企业级标准。

| 架构分层 | 核心技术组件 | 职责描述 |
| :--- | :--- | :--- |
| **🎨 表现层 (UI)** | `PySide6` (v6.11.1) | 基于 Qt6 原生 C++ 渲染引擎的 Python 绑定，构建高吞吐量图形视窗 |
| **🎞️ 多媒体内核** | `OpenCV Headless` (v4.13) | 移除冗余 GUI 模块，纯后台调用核心 `VideoCapture` 进行高速解码 |
| **⚙️ 硬件加速层** | `FFmpeg Core` | 底层集成视频编解码硬件加速器，实现毫秒级关键帧（I-Frame）动态检索 |
| **🧮 科学计算层** | `NumPy` (v2.4.4) | 高性能矩阵级图像内存编码，加速 Frame 转 Buffer 并持久化为 JPEG |
| **📦 构建分发层** | `PyInstaller` + `UPX 5.1` | 生产级二进制加壳与资源内嵌，将整个运行环境压缩至单个独立可执行文件 |

---

## 🚀 开发者快速上手

### 1. 🪐 克隆项目与环境隔离
建议在完全干净、纯净的虚拟环境中配置依赖，以隔绝全局多余第三方库的干扰：

```powershell
# 克隆仓库
git clone https://github.com/crazyzhang277/SnapBatchPro.git
cd SnapBatch

# 创建纯净虚拟环境
python -m venv snap_env

# 激活虚拟环境 (Windows)
.\snap_env\Scripts\activate
```

### 2. 📦 生产级专属依赖安装
为了确保打包体积的极度精简，请**务必安装无头 (headless) 版本的 OpenCV**，它移除了冗余的 C++ 视窗引擎，但保留了完美的解码内核：

```powershell
# 升级基础包管理器
python -m pip install --upgrade pip

# 精准安装核心运行依赖
pip install opencv-python-headless==4.13.0.92
pip install numpy==2.4.4 PySide6==6.11.1

# 安装现代构建工具
pip install pyinstaller==6.20.0
```

### 3. 🏃 运行主程序
激活 `snap_env` 虚拟环境后，在项目根目录下直接执行以下命令启动图形界面：

```bash
python snap_env/SnapBatch.py
```

## ⚡ 生产级编译与二进制体积压榨指南 (93MB → 55MB)
在 Windows 平台分发时，默认的 PyInstaller 打包方式会将整个 Qt 框架和无用库全盘封装，导致体积飙升至 93MB+。本项目通过深度定制配置文件与 UPX 二进制级加壳，成功将体极压榨至 55MB。

### 1. ⚙️ 二进制极简构建流程

1. **获取加壳工具**：下载适合 Windows 64-bit 的 [UPX 5.1+ 核心压缩包](https://github.com/upx/upx/releases)。
2. **环境路径配置**：将解压出来的 `upx.exe` 直接放入项目的根目录下（确保与 `SnapBatch.spec` 在同一层级）。
3. **极速一键编译**：激活虚拟环境后，在终端复制并执行以下全火力轰炸编译命令：

```powershell
# 1. 强制物理粉碎旧的编译残留缓存（防止粘连旧中间件）
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

# 2. 显式调用当前目录下的 upx.exe 启动极限加壳压缩编译
pyinstaller --clean --noconfirm --upx-dir="." SnapBatch.spec
```

### 2. 🧠 精准裁剪策略解析 (`SnapBatch.spec` 黑魔法)

我们的高级 `spec` 配置文件中实现了三大硬核裁切策略，精准直击体积痛点：

* ✂️ **模块强行切除** 在 `excludes` 列表中彻底切断 `QtNetwork`、`QtQml`、`Qt3DCore`、`QtWebEngineCore` 等关于图形渲染外延、网络通信等对于视频帧处理毫无用处的巨型动态库，从源头阻止冗余模块流入。
* 🔬 **NumPy 2.x 科学库深度剥离** 在二进制收集阶段（`Analysis.binaries`），利用自定义 Python 过滤器进行动态扫描，强行抹除 NumPy 2.x 自带的超大数学加速矩阵动态库（如 `libscipy_openblas64_*.dll` 等），在保证解码核心完好的前提下，**立减 30MB+** 冗余权重。
* 🛡️ **微软 CFG 安全避让** 通过 `upx_exclude` 设立底层系统白名单，精准保护 `ucrtbase.dll`、`python3.dll` 等 Windows 系统微型核心链接库。避免 UPX 强行加壳时触发 `NotCompressibleException` 异常，**确保打包流程 100% 成功率**。

---

## 📦 分发与下载通道

如果您只想将它作为一个纯工具开箱即用，无需配置 Python 环境，可以直接获取我们为您编译好、**且完美整合了专属自绘影视图标**的纯净独立单文件版本：

* **📥 蓝奏云不限速高速分发（国内极力推荐）** 👉 [点击前往高速下载直链](https://wwbhe.lanzouu.com/inw7N3pwgryd)
* 🔑 **提取密码**：`1234`

> 💡 **提示**：蓝奏云链接下载完全免登录、满速跑满带宽。由于 Windows 的资源管理器图标缓存机制，下载后如发现图标未显示，请将其复制到桌面或重命名即可瞬间恢复高清精美图标！

---

## 🔧 最佳生产配置建议

为了在日常大批量处理中获得最优的性能与文件管理体验，建议在侧边栏中按以下阈值进行配置：

* 🕒 **帧截取时间**：`0.0` 秒（代表提取纯正视频第一帧，作为封面大图的最佳选择）。
* 📷 **输出品质**：底层默认已锁定 `cv2.IMWRITE_JPEG_QUALITY` 为 `100` 最高品质无损导出。
* 📝 **自动命名**：默认继承 `原视频文件名.jpg`，保持素材的绝对关联性。

---

## 🤝 开源共享与社会化贡献

本项目基于 **MIT 许可证** 完全开源。代码逻辑完全透明，绝无任何商业捆绑、弹窗广告或后台隐私上传行为。

欢迎各位开发者提交 [打开新 Issue](https://github.com/crazyzhang277/SnapBatch/issues) 或发起 [提交 Pull Request](https://github.com/crazyzhang277/SnapBatch/pulls) 参与美化 UI、增强编解码兼容性或优化打包算法！


## 🎯 长期路线图 (Roadmap)

- [x] **基于纯 PySide6 自绘的超高颜值无边框暗黑视窗**
- [x] **多线程后台异步架构**：核心解码交付后台线程，前台 UI 彻底杜绝假死崩溃。
- [x] **毫秒级帧定位**：支持精确到小数点后两位的秒数输入与精准截取。
- [ ] 🚧 **灵活导出多规则命名引擎（开发中）**：未来将支持按 `[原文件名]` + `[分辨率]` + `[截取时间戳]` 自定义组合命名规则。

欢迎各位开发者提交 [打开新 Issue](https://github.com/crazyzhang277/SnapBatch/issues) 或发起 [提交 Pull Request](https://github.com/crazyzhang277/SnapBatch/pulls) 参与美化 UI、增强编解码兼容性或优化打包算法！

---

## 📜 法律授权声明

```text
MIT License

Copyright (c) 2026 crazyzhang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
