# Sora Voice Extractor & Matcher

## 项目简介

本项目旨在将《空之轨迹FC Evo》版的语音包与重置版《空之轨迹1st》进行匹配和替换，让玩家可以在新版游戏中体验到Evo版的完全语音。

项目通过提取两个版本的游戏脚本，利用文本相似度匹配算法，自动将Evo版的语音文件与重制版相应的对话文本进行关联，最终生成可用于新版游戏的语音文件。

注意：项目施工中，打包功能没有经过完整测试。请有需要的朋友使用匹配结果手动打包。
```
--- 匹配完成 ---
总计 (输入文件): 17274
处理 (符合条件): 17230
成功: 16109 (其中向量搜索: 2329)
失败: 1121
```

## 目录介绍
- `atractool-reloaded`：旧版音频`AT9`格式到新版音频`wav`格式转换工具
- `FC-Steam`：旧版游戏文件，下设`Trails in the Sky FC`目录，需要将Evo语音包文件放置在这个目录下，具体参考流程步骤1
- `kuro_mdl_tool`：Falcom引擎PAC文件解包工具，用于解包和重新打包重置版游戏的PAC文件
- `KuroTools v1.3`：Falcom引擎编辑工具，用于编辑重置版游戏的TBL文件
- `SoraVoiceScripts`：旧版游戏的语音脚本，用于提取旧版游戏的对话文本
- `voice`：旧版游戏的语音文件，用于存放打包使用的`WAV`音频
- `output/`: 输出目录。存放所有最终生成的文件，包括更新后的 `t_voice.json`、`t_voice.tbl` 以及最终的 `.pac` 文件。

## 环境准备

本项目需要 Python 3.10 或更高版本。

推荐使用 `uv` 来管理虚拟环境和依赖，它能提供更快的解析和安装速度。

### 方法一：使用 uv (推荐)

1.  **安装 uv**:

    如果您尚未安装 `uv`，请根据您的操作系统执行相应命令：
    ```shell
    # Windows (Powershell)
    irm https://astral.sh/uv/install.ps1 | iex

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **同步环境**:

    在项目根目录下运行以下命令，`uv` 会自动读取 `pyproject.toml` 文件，创建虚拟环境并安装所有必需的依赖项。
    ```shell
    uv sync
    ```

### 方法二：使用 pip

如果您不想使用 `uv`，也可以使用 `pip` 手动安装依赖。

1.  **创建并激活虚拟环境 (可选但推荐)**:
    ```shell
    # 创建虚拟环境
    python -m venv .venv

    # 激活虚拟环境
    # Windows
    .venv\Scripts\activate
    # macOS / Linux
    source .venv/bin/activate
    ```

2.  **安装依赖**: 
    ```shell
    pip install blowfish>=0.6.1 numpy>=2.3.2 pyquaternion>=0.9.9 "sentence-transformers>=5.1.0" torch>=2.8.0 xxhash>=3.5.0 zstandard>=0.24.0
    ```

3. 部分Powershell脚本默认使用了uv，请您根据实际情况修改脚本内容，如使用`python3`替换`uv run`。

## 工作流程

### 步骤 1: 准备语音文件

如果您的Evo语音包是 `.at9` 格式，需要先将其转换为 `.wav` 格式。

1.  **放置源文件**: 解压Evo语音包，并将其中的 `voice` 目录（包含所有 `.at9` 文件）放置到 `FC-Steam\Trails in the Sky FC\` 目录下。目录结构应如下：
    ```
     FC-Steam
     └── Trails in the Sky FC
         └── voice
             └── 000
                 └── ch0010000001.at9
    ```

2.  **运行转换脚本**: 执行 `convert_voice.ps1`。该脚本会自动下载所需工具，并将转换后的 `.wav` 文件输出到项目根目录下的 `voice\wav` 文件夹中。
    ```powershell
    ./convert_voice.ps1
    ```

### 步骤 2: 提取旧版游戏文本

运行 `extract_voice_data.py` 来处理位于 `SoraVoiceScripts/cn.fc/out.msg/` 的旧版（中文FC）脚本文件。此脚本会提取所有带语音的对话，并生成 `voice_data.json`。

```bash
git submodule update SoraVoiceScripts --init
uv run ./extract_voice_data.py
```

此脚本会生成 `voice_data.json` 文件，其中包含了从旧版游戏中提取的所有语音数据。该文件是一个JSON数组，每个元素代表一条语音对话，包含以下字段：

-   `character_id`: 角色的ID。
-   `voice_id`: 语音文件的唯一标识符。
-   `text`: 清理后的对话文本。
-   `source_file`: 数据来源的原始脚本文件名。

### 步骤 3: 准备新版游戏资源

此步骤将从重置版游戏中提取匹配所需的资源，主要是 `t_voice.json` 文件。

**准备工作:**

此脚本会自动下载 `KuroTools`，您只需确保 `kuro_mdl_tool` 子模块已初始化：

```bash
git submodule update --init kuro_mdl_tool
```

**执行脚本:**

运行 `prepare_game_assets.ps1` 脚本，并提供游戏安装路径。

```powershell
# 将 "Your\Game\Path" 替换为实际的游戏安装路径
.\prepare_game_assets.ps1 -GamePath "Your\Game\Path"
```

**脚本输出:**

-   `voice.pac` 和 `table_sc.pac` 的内容会被解包到 `kuro_mdl_tool\misc\` 目录下。
-   最重要的输出文件 `t_voice.json` 会在 `KuroTools v1.3\scripts&tables\` 目录下生成，这是下一步匹配脚本所必需的。

### 步骤 4: 运行核心匹配脚本

这是最关键的一步。运行 `match_voices.py`，它会加载新版游戏的语音表 (`KuroTools v1.3/scripts&tables/t_voice.json`) 和上一步生成的 `voice_data.json`，然后进行文本匹配。

```bash
# 运行基础匹配（默认只匹配主线剧情语音）
uv run match_voices.py

# (可选) 只匹配特定角色的语音
uv run match_voices.py --character-ids 001 002

# (可选) 同时匹配主线、战斗和主动语音
uv run match_voices.py --match-battle --match-active
```

此脚本会生成三个主要文件：
*   `merged_voice_data.json`: 成功匹配的语音数据，用于分析。
*   `unmatched_voice_data.json`: 未能匹配的语音数据，用于分析。
*   `output/t_voice.json`: **核心输出文件**。这是一个更新后的语音表，其中成功匹配的条目已指向Evo版的语音文件名。此文件是下一步打包的基础。

#### 匹配数据格式 (`merged_voice_data.json`)

成功匹配的数据会保存在 `merged_voice_data.json` 文件中，其每个条目包含以下字段：

-   `new_voice_id`: 重制版语音的ID。
-   `new_filename`: 重制版语音的文件名（不含扩展名）。
-   `new_text`: 重制版语音的对应文本。
-   `old_voice_id`: 匹配到的Evo版语音文件的ID。
-   `old_text`: 匹配到的Evo版语音的对应文本。
-   `character_id`: 角色ID。
-   `source_file`: Evo版语音来源的脚本文件名。
-   `match_type`: 匹配方式，可能的值包括：
    -   `exact`: 文本完全相同。
    -   `normalized`: 移除标点和空格后文本相同。
    -   `vector_search (score)`: 基于文本向量相似度匹配，并附带相似度分数。
-   `classification`: 对重制版语音文件的分类信息，包含 `type`, `character_id`, `category`, `number` 等。

#### 脚本调用方式详解

`match_voices.py` 脚本提供了灵活的命令行参数，以控制匹配范围：

-   **基础用法** (默认行为)
    -   **命令**: `uv run match_voices.py`
    -   **作用**: 仅匹配主线剧情相关的语音 (`00` category)。这是最基础的模式，不包含任何战斗、主动或未知语音。

-   **按角色ID过滤**
    -   **命令**: `uv run match_voices.py --character-ids <ID1> <ID2> ...`
    -   **示例**: `uv run match_voices.py --character-ids 001 002`
    -   **作用**: 只处理指定角色ID的语音。此过滤器可与其它选项组合使用。

-   **匹配主动语音**
    -   **命令**: `uv run match_voices.py --match-active`
    -   **作用**: 在默认匹配的基础上，额外包含主动语音 (`av` category)。

-   **匹配战斗语音**
    -   **命令**: `uv run match_voices.py --match-battle`
    -   **作用**: 在默认匹配的基础上，额外包含所有角色的战斗语音 (`b` 和 `bv` category)。

-   **匹配其他未知语音**
    -   **命令**: `uv run match_voices.py --match-other`
    -   **作用**: 匹配所有分类为 `unknown` 的语音。

-   **匹配音效**
    -   **命令**: `uv run match_voices.py --match-sfx`
    -   **作用**: 匹配所有音效文件 (`v_se_*`)。

-   **详细日志**
    -   **命令**: `uv run match_voices.py -v` 或 `uv run match_voices.py --verbose`
    -   **作用**: 输出详细的日志信息，包括每个被跳过处理的语音条目及其原因，便于调试。

-   **禁用向量搜索**
    -   **命令**: `uv run match_voices.py --no-similarity-search`
    -   **作用**: 完全禁用基于向量的相似度搜索，只依赖精确匹配和标准化文本匹配。当您希望匹配结果更严格时可以使用此选项。

-   **自定义相似度阈值**
    -   **命令**: `uv run match_voices.py --similarity-threshold 0.9`
    -   **作用**: 设置向量相似度搜索的阈值（默认为 `0.85`）。只有当相似度分数高于此阈值时，才会被视为成功匹配。您可以根据需要调整此值以平衡准确性和召回率。

-   **将匹配失败的语音指向空文件**
    -   **默认行为**: 脚本会自动将所有未能成功匹配的语音条目指向一个无声的 `EMPTY.wav` 文件。这可以防止游戏在播放这些语音时因找不到文件而出错。
    -   **禁用命令**: `uv run match_voices.py --no-map-failed-to-empty`
    -   **作用**: 禁用上述功能。未匹配的语音条目将保留其原始文件名。

这些参数可以组合使用。例如，要匹配艾丝蒂尔（ID 001）和约修亚（ID 002）的主线、战斗和主动语音，可以使用以下命令：
`uv run match_voices.py --character-ids 001 002 --match-battle --match-active`


### 步骤 5: 打包最终资源

这是最后一步，此脚本将整合所有匹配结果和语音文件，生成可直接用于游戏的 `.pac` 文件。

运行 `package_assets.ps1` 脚本：

```powershell
./package_assets.ps1
```

此脚本会自动执行以下操作：
1.  将 `output/t_voice.json` 转换为 `t_voice.tbl`。
2.  准备一个临时打包环境，并复制原始游戏资源。
3.  使用新的 `t_voice.tbl` 替换旧表，并合并所有新的 `.wav` 语音文件。
4.  重新打包生成 `voice.pac` 和 `table_sc.pac`。
5.  将最终的 `.pac` 文件存放到 `output` 目录下。

### 步骤 6: 应用或恢复补丁

打包完成后，您可以使用 `update_game_files.ps1` 脚本来自动将生成的 `.pac` 文件应用到游戏目录，或从备份中恢复原始文件。

**应用补丁:**

运行以下命令，将 `output` 目录下的 `table_sc.pac` 和 `voice.pac` 复制到游戏的数据目录。脚本会自动备份原始文件（仅首次运行时）。

```powershell
# 将 "Your\Game\Path" 替换为实际的游戏安装路径
.\update_game_files.ps1 -GamePath "Your\Game\Path"
```

**恢复原始文件:**

如果您想移除补丁并恢复游戏的原始文件，请使用 `-Restore` 参数。

```powershell
# 将 "Your\Game\Path" 替换为实际的游戏安装路径
.\update_game_files.ps1 -GamePath "Your\Game\Path" -Restore
```

### 步骤 7: 分析与调试 (可选)

如果您想分析为何某些语音未能匹配，可以运行以下脚本：

*   **`analyze_voice_files.py`**: 检查 `t_voice.json` 和 `wav/` 目录中的文件是否一致，确保没有文件丢失或多余。
*   **`analyze_context.py`**: 检查 `unmatched_voice_data.json`，寻找那些被成功匹配的对话包围的未匹配项，为手动修复提供线索。

## 主要脚本和文件说明

*   `extract_voice_data.py`: 从**旧版**游戏脚本 (`SoraVoiceScripts/cn.fc/out.msg/`) 中提取语音和文本数据，生成 `voice_data.json`。
*   `match_voices.py`: **核心匹配脚本**。使用多种算法（精确、标准化、向量搜索）将新版文本与旧版文本进行匹配。
*   `analyze_voice_files.py`: **工具脚本**。用于验证 `t_voice.json` 中的文件列表与磁盘上的 `.wav` 文件是否一致。
*   `analyze_context.py`: **调试工具**。分析未匹配的语音，通过上下文帮助定位问题。
*   `converter.py`: **工具脚本**。用于将文本文件从 Shift-JIS 编码转换为 UTF-8。
*   `convert_voice.ps1`: **工具脚本**。使用 `atractool-reloaded` 将 `.at9` 音频文件转换为 `.wav`。
*   `merged_voice_data.json`: **输出文件**。包含所有成功匹配的语音条目。
*   `unmatched_voice_data.json`: **输出文件**。包含所有未能匹配的语音条目。
*   `package_assets.ps1`: **打包脚本**。自动化最后一步，将所有资源打包成最终的 `voice.pac` 和 `table_sc.pac` 文件。
*   `update_game_files.ps1`: **部署脚本**。用于将最终生成的 `.pac` 文件自动复制到游戏目录，并支持从备份中恢复原始文件。

## 致谢

本项目的完成离不开以下优秀开源工具和社区的支持，在此向他们表示诚挚的感谢：

-   **[kuro_mdl_tool](https://github.com/eArmada8/kuro_mdl_tool)** by eArmada8
    -   **作用**: 提供了处理 Falcom 游戏资源（`.mdl` 文件）的核心功能，是本工具集打包 `.pac` 文件的关键。

-   **[ATRACTool-Reloaded](https://github.com/XyLe-GBP/ATRACTool-Reloaded)** by XyLe-GBP
    -   **作用**: 用于将索尼的 `.at9` 音频文件高效地转换为通用的 `.wav` 格式，是语音提取流程中不可或缺的一环。

-   **[SoraVoiceScripts](https://github.com/ZhenjianYang/SoraVoiceScripts)** by ZhenjianYang
    -   **作用**: 提供了原始的《空之轨迹FC Evolution》语音脚本，是进行语音匹配的数据基础。

-   **[Kuro Tools](https://github.com/nnguyen259/KuroTools)** by nnguyen259
    -   **作用**: 为理解和处理 Falcom 的游戏文件格式提供了宝贵的工具和参考。

-   **[轨迹系列-Cafe](https://trails-game.com/)**
    -   **作用**: 作为优秀的轨迹系列粉丝社区和资料站，为项目提供了丰富的背景知识和数据参考。
