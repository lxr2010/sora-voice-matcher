# Sora Voice Extractor & Matcher

## 项目简介

本项目旨在将《空之轨迹FC Evo》版的语音包与PC重制版（例如Steam版）进行匹配和替换，让玩家可以在新版游戏中体验到Evo版的完全语音。

项目通过提取两个版本的游戏脚本，利用文本相似度匹配算法，自动将Evo版的语音文件与重制版相应的对话文本进行关联，最终生成可用于新版游戏的语音文件。

## 正确的工作流程

**重要提示：** `main.py` 脚本当前只是一个占位符，并**不能**自动运行整个流程。您必须按照以下顺序手动执行脚本。

### 步骤 1: 准备语音文件 (可选)

如果您的语音文件是 `.at9` 格式，请使用 `convert_voice.ps1` 将其转换为 `.wav` 格式。

```powershell
# 运行此脚本将 at9 转换为 wav
./convert_voice.ps1
```

### 步骤 2: 提取旧版游戏文本

运行 `extract_voice_data.py` 来处理位于 `SoraVoiceScripts/cn.fc/out.msg/` 的旧版（中文FC）脚本文件。此脚本会提取所有带语音的对话，并生成 `voice_data.json`。

```bash
python extract_voice_data.py
```

### 步骤 3: 运行核心匹配脚本

这是最关键的一步。运行 `match_voices.py`，它会加载新版游戏的语音表 (`KuroTools v1.3/scripts&tables/t_voice.json`) 和上一步生成的 `voice_data.json`，然后进行文本匹配。

```bash
# 运行基础匹配
python match_voices.py

# (可选) 只匹配特定角色的语音
python match_voices.py --character-ids 001 002

# (可选) 包含战斗语音
python match_voices.py --match-battle
```

此脚本会生成两个主要文件：
*   `merged_voice_data.json`: 成功匹配的语音数据。
*   `unmatched_voice_data.json`: 未能匹配的语音数据。

### 步骤 4: 分析与调试 (可选)

如果您想分析为何某些语音未能匹配，可以运行以下脚本：

*   **`analyze_voice_files.py`**: 检查 `t_voice.json` 和 `wav/` 目录中的文件是否一致，确保没有文件丢失或多余。
*   **`analyze_context.py`**: 检查 `unmatched_voice_data.json`，寻找那些被成功匹配的对话包围的未匹配项，为手动修复提供线索。

## 主要脚本和文件说明

*   `main.py`: **占位符脚本**，当前无实际功能。
*   `extract_voice_data.py`: 从**旧版**游戏脚本 (`SoraVoiceScripts/cn.fc/out.msg/`) 中提取语音和文本数据，生成 `voice_data.json`。
*   `match_voices.py`: **核心匹配脚本**。使用多种算法（精确、标准化、向量搜索）将新版文本与旧版文本进行匹配。
*   `analyze_voice_files.py`: **工具脚本**。用于验证 `t_voice.json` 中的文件列表与磁盘上的 `.wav` 文件是否一致。
*   `analyze_context.py`: **调试工具**。分析未匹配的语音，通过上下文帮助定位问题。
*   `converter.py`: **工具脚本**。用于将文本文件从 Shift-JIS 编码转换为 UTF-8。
*   `convert_voice.ps1`: **工具脚本**。使用 `atractool-reloaded` 将 `.at9` 音频文件转换为 `.wav`。
*   `merged_voice_data.json`: **输出文件**。包含所有成功匹配的语音条目。
*   `unmatched_voice_data.json`: **输出文件**。包含所有未能匹配的语音条目。