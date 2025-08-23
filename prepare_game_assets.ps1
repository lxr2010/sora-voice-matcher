<#
.SYNOPSIS
    Automates the extraction of game assets required for voice matching.

.DESCRIPTION
    This script performs the following actions:
    1. Takes the path to the game's installation directory as input.
    2. Unpacks 'voice.pac' and 'table_sc.pac' using 'extract_pac.py'.
    3. Converts the extracted 't_voice.tbl' to 't_voice.json' using 'tbl2json.py'.

.PARAMETER GamePath
    The full path to the game's installation directory (e.g., "D:\SteamLibrary\steamapps\common\Sora No Kiseki the 1st Demo").

.EXAMPLE
    .\prepare_game_assets.ps1 -GamePath "D:\SteamLibrary\steamapps\common\Sora No Kiseki the 1st Demo"
#>
param(
    [Parameter(Mandatory=$true, HelpMessage="The full path to the game's installation directory.")]
    [string]$GamePath
)

# --- SCRIPT SETUP ---
$scriptRoot = $PSScriptRoot

# --- AUTO-DOWNLOAD KUROTOOLS ---
$kuroToolsDir = Join-Path -Path $scriptRoot -ChildPath "KuroTools v1.3"
$kuroToolsUrl = "https://github.com/nnguyen259/KuroTools/releases/download/v1.3/KuroTools.v1.3.zip"
$kuroToolsZipPath = Join-Path -Path $scriptRoot -ChildPath "KuroTools.v1.3.zip"

if ((-not (Test-Path -Path $kuroToolsDir -PathType Container)) -or (-not (Get-ChildItem -Path $kuroToolsDir))) {
    Write-Host "KuroTools not found or directory is empty. Downloading and extracting..."
    try {
        Invoke-WebRequest -Uri $kuroToolsUrl -OutFile $kuroToolsZipPath
        if (-not (Test-Path -Path $kuroToolsDir -PathType Container)) {
            New-Item -Path $kuroToolsDir -ItemType Directory | Out-Null
        }
        Expand-Archive -Path $kuroToolsZipPath -DestinationPath $kuroToolsDir -Force
        Remove-Item -Path $kuroToolsZipPath
        Write-Host "KuroTools downloaded and extracted successfully."
    } catch {
        Write-Error "Failed to download or extract KuroTools. Please do it manually from $kuroToolsUrl"
        exit 1
    }
}
# --- END OF AUTO-DOWNLOAD ---

# Define paths to the required tools and files
$extractPacScript = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\extract_pac.py"
$tbl2JsonScript = Join-Path -Path $scriptRoot -ChildPath "KuroTools v1.3\scripts&tables\tbl2json.py"

$voicePac = Join-Path -Path $GamePath -ChildPath "pac\steam\voice.pac"
$tableScPac = Join-Path -Path $GamePath -ChildPath "pac\steam\table_sc.pac"

$voiceTbl = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\table_sc\t_voice.tbl"

# --- VALIDATION CHECKS ---
Write-Host "Validating paths..."

if (-not (Test-Path -Path $GamePath -PathType Container)) {
    Write-Error "Game directory not found: '$GamePath'"
    exit 1
}

if (-not (Test-Path -Path $extractPacScript -PathType Leaf)) {
    Write-Error "extract_pac.py not found: '$extractPacScript'"
    exit 1
}

if (-not (Test-Path -Path $tbl2JsonScript -PathType Leaf)) {
    Write-Error "tbl2json.py not found: '$tbl2JsonScript'"
    exit 1
}

if (-not (Test-Path -Path $voicePac -PathType Leaf)) {
    Write-Error "voice.pac not found: '$voicePac'"
    exit 1
}

if (-not (Test-Path -Path $tableScPac -PathType Leaf)) {
    Write-Error "table_sc.pac not found: '$tableScPac'"
    exit 1
}

Write-Host "All paths validated successfully."

# --- SCRIPT EXECUTION ---

# 1. Extract voice.pac
Write-Host "Extracting voice.pac..."
try {
    Push-Location (Split-Path -Path $extractPacScript -Parent)
    uv run python .\extract_pac.py $voicePac
    Pop-Location
    Write-Host "'voice.pac' extracted successfully."
} catch {
    Write-Error "Failed to extract 'voice.pac'."
    Pop-Location
    exit 1
}

# 2. Extract table_sc.pac
Write-Host "Extracting table_sc.pac..."
try {
    Push-Location (Split-Path -Path $extractPacScript -Parent)
    uv run python .\extract_pac.py $tableScPac
    Pop-Location
    Write-Host "'table_sc.pac' extracted successfully."
} catch {
    Write-Error "Failed to extract 'table_sc.pac'."
    Pop-Location
    exit 1
}

# 3. Convert t_voice.tbl to JSON
Write-Host "Converting t_voice.tbl to JSON..."
if (-not (Test-Path -Path $voiceTbl -PathType Leaf)) {
    Write-Error "t_voice.tbl not found after extraction: '$voiceTbl'"
    exit 1
}

try {
    Push-Location (Split-Path -Path $tbl2JsonScript -Parent)
    uv run python .\tbl2json.py $voiceTbl
    Pop-Location
    Write-Host "'t_voice.tbl' converted to JSON successfully."
} catch {
    Write-Error "Failed to convert 't_voice.tbl' to JSON."
    Pop-Location
    exit 1
}

Write-Host "Asset preparation complete!"
