# 🔄 APK / AAB / APKS 批量转换工具

[![GitHub](https://img.shields.io/badge/GitHub-planspieldaxe--commits-blue?logo=github)](https://github.com/planspieldaxe-commits)
[![Telegram](https://img.shields.io/badge/Telegram-@webasp-blue?logo=telegram)](https://t.me/webasp)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Android应用包格式批量转换工具，支持 **APK**、**AAB**、**APKS** 格式互转，提供图形界面(GUI)和命令行(CLI)两种操作方式。

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 📦 **APK → AAB** | 将普通APK转换为Android App Bundle格式 |
| 📦 **AAB → APKS** | 将AAB转换为APKS拆分安装包（支持多种模式） |
| 🔄 **全流程转换** | 一键完成 APK → AAB → APKS |
| 📱 **拆分包提取** | APKS/XAPK/APKM 转换为普通APK |
| 🔐 **自动签名** | 自动生成随机签名（符合Google Play要求） |
| 🖥️ **图形界面** | 现代化GUI，操作简单直观 |
| 📁 **批量转换** | 支持文件夹批量处理 |
| 📂 **自定义输出** | 可选择输出目录 |

## 📸 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│  💬 Telegram联系  │  📢 Telegram频道  │  🐙 GitHub         │
├─────────────────────────────────────────────────────────────┤
│  [APK→AAB] [AAB→APKS] [全流程转换] [拆分包→APK]            │
├─────────────────────────────────────────────────────────────┤
│  📂 输入文件/文件夹: [浏览文件] [浏览文件夹]                │
│  📋 文件信息: 包名、版本、大小...                          │
│  📁 输出目录: [浏览]                                       │
│  🔐 签名设置: ☑ 自动生成随机签名                           │
│                    [🚀 开始转换]                            │
├─────────────────────────────────────────────────────────────┤
│  📜 日志输出...                                            │
│  ████████████████░░░░ 80%                                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 下载项目
```bash
git clone https://github.com/planspieldaxe-commits/apk-aab-converter.git
cd apk-aab-converter
```

### 2. 安装依赖工具
参考 [INSTALL.txt](INSTALL.txt) 下载以下工具到 `tools/` 目录：
- **bundletool.jar** - [下载](https://github.com/google/bundletool/releases)
- **JDK 17+** - [下载](https://adoptium.net/)
- **Android Build Tools** - [下载](https://developer.android.com/studio)

### 3. 安装 Python 依赖（可选，用于美化界面）
```bash
pip install customtkinter
```

### 4. 启动程序

**图形界面（推荐）：**
```bash
# Windows: 双击 启动GUI.bat
# 或命令行:
python converter_gui.py
```

**命令行模式：**
```bash
python converter.py
```

## 📖 使用说明

### GUI图形界面

1. **APK → AAB**: 选择APK文件 → 设置签名 → 开始转换
2. **AAB → APKS**: 选择AAB文件 → 选择模式 → 开始转换
3. **全流程转换**: 选择APK → 一键完成 APK→AAB→APKS
4. **拆分包 → APK**: 选择APKS/XAPK/APKM → 提取/合并

### 命令行模式

```bash
# APK转AAB
python converter.py 1

# AAB转APKS (universal模式)
python converter.py 2 universal

# 全流程转换
python converter.py 3

# APKS/XAPK/APKM转APK
python converter.py 9
```

## 📁 目录结构

```
apk-aab-converter/
├── apk/              # 放入待转换的APK文件
├── aab/              # AAB输出目录
├── apks/             # APKS输出目录
├── apk2/             # 拆分包转换输出目录
├── split_apk/        # 放入APKS/XAPK/APKM文件
├── keystore/         # 签名文件目录
├── tools/            # 工具目录（需自行下载）
├── converter.py      # 命令行程序
├── converter_gui.py  # GUI程序
├── 启动GUI.bat       # Windows启动脚本
└── README.md         # 本文件
```

## 🔧 转换模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `default` | 拆分APK集合 | Google Play分发 |
| `universal` | 通用单APK（推荐） | 侧载安装、第三方商店 |
| `system` | 系统APK | OEM预装 |
| `instant` | 即时应用 | Google Play即时体验 |

## 📝 支持的格式

| 格式 | 说明 |
|------|------|
| `.apk` | Android应用程序包 |
| `.aab` | Android App Bundle |
| `.apks` | bundletool生成的拆分包 |
| `.xapk` | APKPure格式 |
| `.apkm` | APKMirror格式 |

## ❓ 常见问题

<details>
<summary><b>Q: 转换失败怎么办？</b></summary>

检查以下几点：
1. tools目录下是否有完整的工具文件
2. JDK版本是否为17+
3. 输入文件是否完整无损
</details>

<details>
<summary><b>Q: 如何使用自己的签名？</b></summary>

将 `.jks` 签名文件和对应的 `.json` 配置文件放入 `keystore/` 目录，文件名与AAB一致即可。
</details>

<details>
<summary><b>Q: GUI界面不够美观？</b></summary>

安装 customtkinter 获得现代化界面：
```bash
pip install customtkinter
```
</details>

## 📞 联系方式

- **Telegram**: [@webasp](https://t.me/webasp)
- **Telegram频道**: [@webjsp](https://t.me/webjsp)

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

⭐ 如果这个项目对你有帮助，请给个 Star！

