# Sora Voice Extractor & Matcher

## 项目简介

本项目旨在将《空之轨迹FC Evo》版的语音包与重置版《空之轨迹1st》进行匹配和替换，让玩家可以在新版游戏中体验到Evo版的完全语音。

项目通过提取两个版本的游戏脚本，利用文本相似度匹配算法，自动将Evo版的语音文件与重制版相应的对话文本进行关联，最终生成可用于新版游戏的语音文件。

注意：项目施工中，打包功能没有经过完整测试。请有需要的朋友使用匹配结果手动打包。
```
--- 匹配完成 ---
总计 (输入文件): 17274
处理 (符合条件): 13686
成功: 13513 (其中向量搜索: 628)
失败: 173
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

1.  **安装 uv**：

    如果您尚未安装 `uv`，请根据您的操作系统执行相应命令：
    ```shell
    # Windows (Powershell)
    irm https://astral.sh/uv/install.ps1 | iex

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **同步环境**：

    在项目根目录下运行以下命令，`uv` 会自动读取 `pyproject.toml` 文件，创建虚拟环境并安装所有必需的依赖项。
    ```shell
    uv sync
    ```

### 方法二：使用 pip

如果您不想使用 `uv`，也可以使用 `pip` 手动安装依赖。

1.  **创建并激活虚拟环境 (可选但推荐)**：
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
-   `old_script_id`: 匹配到的Evo版语音的脚本ID。
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

运行 `package_assets.ps1` 脚本。默认情况下，该脚本会处理 `table_sc`（语音表）。您可以选择性地包含语音文件的打包。

**打包选项:**

-   **仅打包语音表 (默认)**:
    ```powershell
    ./package_assets.ps1
    ```
    此命令仅会生成 `table_sc.pac`。

-   **打包语音表和语音文件**:
    ```powershell
    ./package_assets.ps1 -IncludeVoice
    ```
    此命令会同时生成 `table_sc.pac` 和 `voice.pac`。

**脚本会自动执行以下操作：**
1.  将 `output/t_voice.json` 转换为 `t_voice.tbl`。
2.  准备一个临时打包环境，并复制原始游戏资源。
3.  使用新的 `t_voice.tbl` 替换旧表。
4.  如果使用 `-IncludeVoice`，则合并所有新的 `.wav` 语音文件。
5.  重新打包生成 `table_sc.pac` (默认) 和 `voice.pac` (可选)。
6.  将最终的 `.pac` 文件存放到 `output` 目录下。

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

本项目的实现离不开以下优秀的开源工具和社区的支持，在此向他们表示诚挚的感谢：

- **[kuro_mdl_tool](https://github.com/eArmada8/kuro_mdl_tool)**: 提供了拆包和打包Falcom `.pac` 文件的核心功能。特别感谢其文档中提到的以下贡献者：
    - **Julian Uy (uyjulian)**: 在MDL格式的逆向工程方面做出了基础性贡献。
    - **TwnKey** 及 **KuroTools 团队 (nnguyen259)**: 提供了用于解密/解压资源和MDL转换器的代码。
    - **weskeryiu** 和 **Kyuuhachi**: 为理解MDL格式和碰撞网格结构提供了深刻见解。
    - **DarkStarSword**: 开发了功能强大的3DMigoto-Blender插件。
- **[SoraVoiceScripts](https://github.com/ZhenjianYang/SoraVoiceScripts)**: 由 **ZhenjianYang** 提供，该仓库包含了从原始游戏中提取的关键脚本文件，是文本提取的基础。
- **[atractool-reloaded](https://github.com/kou-yeung/atractool-reloaded)**: 提供了将 `.at9` 音频文件转换为 `.wav` 格式的工具。
- **Kiseki modding discord 社区**: 营造了知识共享与协作的环境。
- **[轨迹Cafe](https://wiki.biligame.com/kiseki/)**: 一个内容详尽的粉丝运营维基和社区，是轨迹系列宝贵的资源库。

## 许可协议

本项目中的脚本代码采用 **GNU General Public License v3.0** 进行许可。您可以在项目的根目录下找到 [LICENSE](LICENSE) 文件的完整内容。

### 子模块许可

本项目包含的子模块使用其各自的许可协议：
- **[kuro_mdl_tool](https://github.com/eArmada8/kuro_mdl_tool)**
- **[SoraVoiceScripts](https://github.com/ZhenjianYang/SoraVoiceScripts)**

### 数据权利声明

本项目所使用的所有游戏数据，包括但不限于语音、文本、图像及其他资源，其所有权和知识产权均归属于 **Nihon Falcom Corporation**。本项目的作者不对这些数据主张任何权利。

本项目仅为技术研究和个人娱乐目的而创建，旨在增强玩家的游戏体验。严禁将本工具及其产出用于任何商业用途。

---
# Sora Voice Extractor & Matcher (English)

## Project Introduction

This project aims to match and replace the voice pack from *The Legend of Heroes: Trails in the Sky FC Evolution* with the remastered version, allowing players to experience the full voice acting of the Evo version in the new game.

The project works by extracting game scripts from both versions and using text similarity matching algorithms to automatically associate the Evo voice files with the corresponding dialogue text in the remastered version. Finally, it generates the necessary files to be used in the new game.

**Note**: This project is under construction, and the packaging functionality has not been fully tested. Please use the matching results to package the files manually if needed.

```
--- Matching Complete ---
Total (Input Files): 17274
Processed (Eligible): 13686
Success: 13594 (Vector Search: 405)
Failed: 92
```

## Directory Structure
- `atractool-reloaded`: Tool for converting the old `AT9` audio format to the new `wav` format.
- `FC-Steam`: Directory for the old game files. Place the Evo voice pack under `FC-Steam\Trails in the Sky FC\` as described in Step 1.
- `kuro_mdl_tool`: Tool for unpacking and repacking Falcom engine PAC files, used for the remastered game.
- `KuroTools v1.3`: Falcom engine editing tools, used for editing the remastered game's TBL files.
- `SoraVoiceScripts`: Voice scripts from the original game, used to extract dialogue text.
- `voice`: Directory for the old game's voice files, used to store the `WAV` audio for packaging.
- `output/`: Output directory. Contains all final generated files, including the updated `t_voice.json`, `t_voice.tbl`, and the final `.pac` files.

## Environment Setup

This project requires Python 3.10 or higher.

It is recommended to use `uv` to manage the virtual environment and dependencies for faster resolution and installation.

### Method 1: Using uv (Recommended)

1.  **Install uv**:

    If you don't have `uv` installed, run the appropriate command for your OS:
    ```shell
    # Windows (Powershell)
    irm https://astral.sh/uv/install.ps1 | iex

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Sync Environment**:

    Run the following command in the project root. `uv` will automatically read `pyproject.toml`, create a virtual environment, and install all required dependencies.
    ```shell
    uv sync
    ```

### Method 2: Using pip

If you prefer not to use `uv`, you can install dependencies manually with `pip`.

1.  **Create and Activate a Virtual Environment (Optional but Recommended)**:
    ```shell
    # Create virtual environment
    python -m venv .venv

    # Activate virtual environment
    # Windows
    .venv\Scripts\activate
    # macOS / Linux
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```shell
    pip install blowfish>=0.6.1 numpy>=2.3.2 pyquaternion>=0.9.9 "sentence-transformers>=5.1.0" torch>=2.8.0 xxhash>=3.5.0 zstandard>=0.24.0
    ```

3. Some PowerShell scripts use `uv` by default. Please modify the scripts as needed, for example, by replacing `uv run` with `python3`.

## Workflow

### Step 1: Prepare Voice Files

If your Evo voice pack is in `.at9` format, you need to convert it to `.wav` first.

1.  **Place Source Files**: Extract the Evo voice pack and place the `voice` directory (containing all `.at9` files) into the `FC-Steam\Trails in the Sky FC\` directory. The structure should look like this:
    ```
     FC-Steam
     └── Trails in the Sky FC
         └── voice
             └── 000
                 └── ch0010000001.at9
    ```

2.  **Run Conversion Script**: Execute `convert_voice.ps1`. This script will automatically download the necessary tools and output the converted `.wav` files to the `voice\wav` folder in the project root.
    ```powershell
    ./convert_voice.ps1
    ```

### Step 2: Extract Text from the Original Game

Run `extract_voice_data.py` to process the original game script files located in `SoraVoiceScripts/cn.fc/out.msg/`. This script extracts all voiced dialogue and generates `voice_data.json`.

```bash
git submodule update SoraVoiceScripts --init
uv run ./extract_voice_data.py
```

This script generates `voice_data.json`, which contains all voice data extracted from the original game. It is a JSON array where each element represents a voice line with the following fields:

-   `character_id`: The character's ID.
-   `voice_id`: The unique identifier for the voice file.
-   `text`: The cleaned dialogue text.
-   `source_file`: The original script file from which the data was sourced.

### Step 3: Prepare Remastered Game Assets

This step extracts the necessary assets from the remastered game, primarily the `t_voice.json` file.

**Preparation:**

This script will automatically download `KuroTools`. Just ensure the `kuro_mdl_tool` submodule is initialized:

```bash
git submodule update --init kuro_mdl_tool
```

**Execution:**

Run the `prepare_game_assets.ps1` script, providing the game installation path.

```powershell
# Replace "Your\Game\Path" with the actual game installation path
.\prepare_game_assets.ps1 -GamePath "Your\Game\Path"
```

**Output:**

-   The contents of `voice.pac` and `table_sc.pac` will be unpacked into the `kuro_mdl_tool\misc\` directory.
-   The most important output, `t_voice.json`, will be generated in the `KuroTools v1.3\scripts&tables\` directory, which is required for the next matching step.

### Step 4: Run the Core Matching Script

This is the most critical step. Run `match_voices.py` to load the new game's voice table (`KuroTools v1.3/scripts&tables/t_voice.json`) and the `voice_data.json` generated previously, then perform the text matching.

```bash
# Run basic matching (only main story voices by default)
uv run match_voices.py

# (Optional) Match voices for specific characters
uv run match_voices.py --character-ids 001 002

# (Optional) Match main, battle, and active voices
uv run match_voices.py --match-battle --match-active
```

This script generates three main files:
*   `merged_voice_data.json`: Successfully matched voice data, for analysis.
*   `unmatched_voice_data.json`: Unmatched voice data, for analysis.
*   `output/t_voice.json`: **The core output file**. This is an updated voice table where matched entries now point to the Evo voice filenames. This file is the basis for the next packaging step.

#### Match Data Format (`merged_voice_data.json`)

Successfully matched data is saved in `merged_voice_data.json`. Each entry contains:

-   `new_voice_id`: The ID of the remastered voice.
-   `new_filename`: The filename of the remastered voice (without extension).
-   `new_text`: The corresponding text of the remastered voice.
-   `old_voice_id`: The ID of the matched Evo voice file.
-   `old_text`: The corresponding text of the matched Evo voice.
-   `character_id`: The character ID.
-   `source_file`: The source script file of the Evo voice.
-   `match_type`: The matching method used (`exact`, `normalized`, `vector_search (score)`).
-   `classification`: Classification info for the remastered voice file (`type`, `character_id`, `category`, `number`).

#### Script Arguments Explained

`match_voices.py` provides flexible command-line arguments:

-   **Basic Usage**: `uv run match_voices.py` - Matches only main story voices.
-   **Filter by Character ID**: `--character-ids <ID1> <ID2>` - Processes only specified character IDs.
-   **Match Active Voices**: `--match-active` - Includes active voices (`av` category).
-   **Match Battle Voices**: `--match-battle` - Includes battle voices (`b` and `bv` categories).
-   **Match Other Voices**: `--match-other` - Includes voices classified as `unknown`.
-   **Match Sound Effects**: `--match-sfx` - Includes sound effect files (`v_se_*`).
-   **Verbose Logging**: `-v` or `--verbose` - Outputs detailed logs for debugging.
-   **Disable Vector Search**: `--no-similarity-search` - Disables vector-based similarity search for stricter matching.
-   **Custom Similarity Threshold**: `--similarity-threshold 0.9` - Sets the similarity score threshold (default: `0.85`).
-   **Map Failed to Empty**: Enabled by default. Unmatched voices point to a silent `EMPTY.wav` to prevent in-game errors. Disable with `--no-map-failed-to-empty`.

Arguments can be combined. For example, to match main, battle, and active voices for Estelle (ID 001) and Joshua (ID 002):
`uv run match_voices.py --character-ids 001 002 --match-battle --match-active`

### Step 5: Package the Final Assets

This final step integrates all matching results and voice files to generate game-ready `.pac` files.

Run the `package_assets.ps1` script. By default, this script processes the `table_sc` (voice table). You can optionally include voice file packaging.

**Packaging Options:**

-   **Package Only the Voice Table (Default)**:
    ```powershell
    ./package_assets.ps1
    ```
    This command will only generate `table_sc.pac`.

-   **Package Both Voice Table and Voice Files**:
    ```powershell
    ./package_assets.ps1 -IncludeVoice
    ```
    This command will generate both `table_sc.pac` and `voice.pac`.

**The script automates the following:**
1.  Converting `output/t_voice.json` to `t_voice.tbl`.
2.  Preparing a temporary packaging environment.
3.  Replacing the old `t_voice.tbl`.
4.  If `-IncludeVoice` is used, it merges all new `.wav` voice files.
5.  Repackaging `table_sc.pac` (by default) and `voice.pac` (optional).
6.  Placing the final `.pac` files in the `output` directory.

### Step 6: Apply or Restore the Patch

After packaging, use `update_game_files.ps1` to automatically apply the generated `.pac` files to your game directory or restore the original files from a backup.

**Apply Patch:**

This command copies `table_sc.pac` and `voice.pac` to the game's data directory, automatically backing up the original files on the first run.

```powershell
# Replace "Your\Game\Path" with the actual game installation path
.\update_game_files.ps1 -GamePath "Your\Game\Path"
```

**Restore Originals:**

To remove the patch and restore the original game files, use the `-Restore` parameter.

```powershell
# Replace "Your\Game\Path" with the actual game installation path
.\update_game_files.ps1 -GamePath "Your\Game\Path" -Restore
```

### Step 7: Analysis and Debugging (Optional)

To analyze why some voices failed to match, you can run:

*   **`analyze_voice_files.py`**: Checks for consistency between `t_voice.json` and the files in the `wav/` directory.
*   **`analyze_context.py`**: Examines `unmatched_voice_data.json` to find unmatched lines surrounded by matched ones, providing clues for manual fixing.

## Main Scripts and Files Explained

*   `extract_voice_data.py`: Extracts voice and text data from the **original** game scripts, generating `voice_data.json`.
*   `match_voices.py`: **Core matching script**. Matches new text with old text using various algorithms.
*   `analyze_voice_files.py`: **Utility script**. Verifies consistency between `t_voice.json` and on-disk `.wav` files.
*   `analyze_context.py`: **Debugging tool**. Analyzes unmatched voices using context.
*   `converter.py`: **Utility script**. Converts text files from Shift-JIS to UTF-8.
*   `convert_voice.ps1`: **Utility script**. Converts `.at9` audio files to `.wav` using `atractool-reloaded`.
*   `merged_voice_data.json`: **Output file**. Contains all successfully matched voice entries.
*   `unmatched_voice_data.json`: **Output file**. Contains all unmatched voice entries.
*   `package_assets.ps1`: **Packaging script**. Automates the final step of packaging all assets into `voice.pac` and `table_sc.pac`.
*   `update_game_files.ps1`: **Deployment script**. Copies the final `.pac` files to the game directory and supports restoring from backups.

## License

The script code in this project is licensed under the **GNU General Public License v3.0**. You can find the full text of the license in the [LICENSE](LICENSE) file at the root of the project.

### Submodule Licensing

The submodules included in this project are subject to their own licenses:
- **[kuro_mdl_tool](https://github.com/eArmada8/kuro_mdl_tool)**
- **[SoraVoiceScripts](https://github.com/ZhenjianYang/SoraVoiceScripts)**

### Data Rights Disclaimer

All game data used by this project, including but not limited to voice, text, images, and other assets, are the property and intellectual property of **Nihon Falcom Corporation**. The author of this project claims no rights over this data.

This project is created for technical research and personal entertainment purposes only, aiming to enhance the player's gaming experience. Any commercial use of this tool and its output is strictly prohibited.

## Acknowledgements

This project was made possible by the support of the following excellent open-source tools and communities. A sincere thank you to them:

- **[kuro_mdl_tool](https://github.com/eArmada8/kuro_mdl_tool)**: For providing the core functionality of unpacking and repacking Falcom's `.pac` files. Special thanks to the following individuals mentioned in its credits:
    - **Julian Uy (uyjulian)**: For the foundational reverse engineering work on the MDL format.
    - **TwnKey** and the **KuroTools team (nnguyen259)**: For the code to decrypt/decompress assets and the MDL converter.
    - **weskeryiu** and **Kyuuhachi**: For providing deep insights into the MDL format and collision mesh structures.
    - **DarkStarSword**: For the invaluable 3DMigoto-Blender plugin.
- **[SoraVoiceScripts](https://github.com/ZhenjianYang/SoraVoiceScripts)**: Provided by **ZhenjianYang**, this repository contains the essential script files from the original game, which are crucial for text extraction.
- **[atractool-reloaded](https://github.com/kou-yeung/atractool-reloaded)**: For the tool that converts `.at9` audio files to the `.wav` format.
- The **Kiseki modding discord community**: For fostering an environment of knowledge sharing and collaboration.
- **[轨迹Cafe](https://wiki.biligame.com/kiseki/)**: A comprehensive fan-run wiki and community that serves as an invaluable resource for the Trails series.
