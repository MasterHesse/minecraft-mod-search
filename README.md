# Agent Skills：Minecraft Mod 搜索助手
---

一个用于在 Minecraft Java Edition 生态中搜索和推荐模组的 AI Agent 技能。支持 Modrinth、CurseForge 多平台搜索，智能排序，依赖解析，版本过滤和卡片化结果展示。

## 功能特性

- 🔍 **多平台搜索**：支持 Modrinth（主平台）和 CurseForge（备选）
- 🎯 **版本过滤**：自动过滤与指定 Minecraft 版本不兼容的 Mod
- 🔧 **加载器支持**：Fabric、Forge、Quilt、Rift
- 📦 **整合包分析**：分析整合包需求，推荐兼容的 Mod 组合
- ⚠️ **冲突检测**：检测已知的 Mod 冲突和兼容性问题
- 📊 **智能排序**：基于下载量、更新频率和兼容性综合评分
- 🌐 **中文友好**：用户交互使用中文描述

## 快速开始

### 前置要求

- 已安装任意可搭载 skills 的 Agent
- Python 3.8+（用于脚本）

### 安装方法

1. 克隆本仓库：
```bash
git clone https://github.com/MasterHesse/minecraft-mod-search.git
```

2. 将 `SKILL.md` 文件复制到你的 WorkBuddy 技能目录：
```bash
# Windows 以 workbuddy 为例
copy minecraft-mod-search\SKILL.md %USERPROFILE%\.workbuddy\skills\

# Linux/macOS 以 workbuddy 为例
cp minecraft-mod-search/SKILL.md ~/.workbuddy/skills/
```

3. 重启 Agent 以加载新技能。

## 使用示例

### 基础搜索

```
"帮我找个帧率优化的mod"
"搜索 OptiFine 替代品"
"1.20.4 fabric 模组推荐"
"我的世界1.20.4 forge 整合包"
```

### 整合包分析

```
"我要做一个科技整合包，1.20.4，forge，包含自动化、能源、物流"
"推荐一个生存向的1.19.2整合包"
"帮我配一个魔法包"
```

## 文件结构

```
minecraft-mod-search/
├── SKILL.md              # 技能主配置文件
├── README.md             # 英文说明文档
├── README_zh-CN.md       # 中文说明文档
├── LICENSE               # MIT 开源许可证
├── references/
│   ├── modrinth_api.md   # Modrinth API 文档
│   ├── curseforge_api.md  # CurseForge API 文档
│   ├── mc_versions.md     # Minecraft 版本兼容性
│   └── mod_compat.md      # Mod 冲突矩阵
└── scripts/
    └── search_mods.py    # 核心搜索脚本
```

## API 参考

### Modrinth API

主要搜索平台，无需 API Key。

- **接口地址**：`https://api.modrinth.com/v2/search`
- **参数**：`query`, `facets=[categories, versions, loaders]`
- **频率限制**：无认证 100 次/分钟
- **文档**：[Modrinth API 文档](https://docs.modrinth.com/api/)

### CurseForge API

备用搜索平台，需要 API Key。

- **接口地址**：`https://api.curseforge.com/v1/mods/search`
- **参数**：`gameId=432`, `searchFilter`, `classId=6`
- **频率限制**：4290 次/天
- **文档**：[CurseForge API 文档](https://docs.curseforge.com/)

## 支持的 Minecraft 版本

| 版本 | 状态 | 备注 |
|------|------|------|
| 1.21.x | ✅ 活跃 | 最新稳定版 |
| 1.20.4 | ✅ 活跃 | 最受欢迎 |
| 1.20.1 | ✅ 活跃 | 常用选择 |
| 1.19.4 | ⚠️ 停止维护 | 已停止支持 |
| 1.18.2 | ⚠️ 停止维护 | 遗留版本 |

详细版本兼容性请查看 [references/mc_versions.md](references/mc_versions.md)。

## 已知 Mod 冲突

详细冲突矩阵请查看 [references/mod_compat.md](references/mod_compat.md)。

| Mod A | Mod B | 状态 | 原因 |
|-------|-------|------|------|
| OptiFine | Sodium | ⚠️ 冲突 | 功能重叠 |
| OptiFine | Iris | ⚠️ 冲突 | 着色器不兼容 |
| AE2 | Refined Storage | ❌ 不可兼容 | 两者都是存储系统 |
| REI | EMI | ⚠️ 冲突 | 功能重叠 |

## 使用脚本

### 安装依赖

```bash
pip install requests
```

### 搜索 Mod

```bash
# 搜索帧率优化 Mod
python scripts/search_mods.py --query "fps optimization" --version "1.20.4" --loader "fabric"

# 搜索特定 Mod
python scripts/search_mods.py --query "optifine" --version "1.20.1"

# 组合搜索
python scripts/search_mods.py --query "自动化" --version "1.19.2" --loader "forge"
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--query` | 搜索关键词 | `"帧率优化"` |
| `--version` | Minecraft 版本 | `"1.20.4"` |
| `--loader` | 加载器类型 | `"fabric"` / `"forge"` |
| `--platform` | 搜索平台 | `"modrinth"` / `"curseforge"` / `"all"` |
| `--limit` | 返回结果数量 | `15` |
| `--output` | 输出格式 | `"text"` / `"json"` |

## 贡献指南

欢迎贡献代码！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 开源许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Modrinth](https://modrinth.com/) - 主要 Mod 托管平台
- [CurseForge](https://www.curseforge.com/) - 备用 Mod 托管平台
- [WorkBuddy](https://www.codebuddy.cn/) - AI 助手框架

## 支持

如果这个项目对你有帮助，请给它一个 ⭐！

问题和功能请求请提交 [Issue](https://github.com/MasterHesse/minecraft-mod-search/issues)。你的反馈能给我的更新带来莫大的启发！
