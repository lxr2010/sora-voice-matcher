<#
.SYNOPSIS
    Automates the process of packaging game assets after voice matching.

.DESCRIPTION
    This script performs the following steps:
    1. Converts the matched `t_voice.json` to `t_voice.tbl` using KuroTools.
    2. Prepares a temporary directory with original game assets (`table_sc` and `voice`).
    3. Updates the temporary directory with the new `t_voice.tbl` and merges the new `.wav` voice files.
    4. Repackages the `table_sc` and `voice` directories into `.pac` archives using kuro_mdl_tool.
    5. Moves the final `.pac` files to the `output` directory and cleans up temporary files.

.EXAMPLE
    .\package_assets.ps1
#>

param(
    [Parameter(Mandatory=$false, HelpMessage="Additionally process the voice assets.")]
    [switch]$IncludeVoice
)

# --- Configuration ---
$ErrorActionPreference = 'Stop'
$scriptRoot = $PSScriptRoot

# Paths to tools and assets
$json2TblScript = Join-Path -Path $scriptRoot -ChildPath "KuroTools v1.3\scripts&tables\json2tbl.py"
$createPacScript = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\create_pac.py"

# Source paths
$sourceJson = Join-Path -Path $scriptRoot -ChildPath "output\t_voice.json"
$newVoicesDir = Join-Path -Path $scriptRoot -ChildPath "voice" # Converted Evo voices

# Output and temporary paths
$outputDir = Join-Path -Path $scriptRoot -ChildPath "output"
$tempJson = Join-Path -Path $scriptRoot -ChildPath "KuroTools v1.3\scripts&tables\t_voice_new.json"
$tmpTbl = Join-Path -Path $scriptRoot -ChildPath "KuroTools v1.3\scripts&tables\t_voice_new.tbl"
$outputTableScDir = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\table_sc"
$outputVoiceDir = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\voice"
$outputTableScPac = Join-Path -Path $scriptRoot -ChildPath "output\table_sc.pac"
$outputVoicePac = Join-Path -Path $scriptRoot -ChildPath "output\voice.pac"

# --- Main Script ---
$originalLocation = Get-Location

Write-Host "--- Processing table_sc assets (Default) ---"

# Step 1: Copy $sourceJson to $tempJson
Write-Host "Step 1: Copying t_voice.json for processing..."
if (-not (Test-Path -Path $sourceJson)) {
    Write-Error "Source JSON file not found: $sourceJson"
    exit 1
}
Copy-Item -Path $sourceJson -Destination $tempJson -Force
Write-Host "Successfully copied t_voice.json."

# Step 2: Convert $tempJson to $tmpTbl
Write-Host "Step 2: Converting JSON to TBL..."
if (-not (Test-Path -Path $json2TblScript)) {
    Write-Error "json2tbl.py script not found: $json2TblScript"
    exit 1
}
Set-Location -Path (Split-Path -Path $json2TblScript -Parent)
uv run python (Split-Path -Path $json2TblScript -Leaf) (Split-Path -Path $tempJson -Leaf)
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to convert JSON to TBL."
    Set-Location -Path $originalLocation
    exit 1
}
Set-Location -Path $originalLocation
Write-Host "Successfully converted JSON to TBL."

# Step 3: Copy $tmpTbl to $outputDir
Write-Host "Step 3: Copying TBL to output directory..."
Copy-Item -Path $tmpTbl -Destination (Join-Path -Path $outputDir -ChildPath "t_voice.tbl") -Force
Write-Host "Successfully copied TBL file."

# Step 4: Copy $tmpTbl to $outputTableScDir, replacing the old t_voice.tbl
Write-Host "Step 4: Updating table_sc with new TBL file..."
Copy-Item -Path $tmpTbl -Destination (Join-Path -Path $outputTableScDir -ChildPath "t_voice.tbl") -Force
Write-Host "Successfully updated table_sc."

# Step 5 & 6: Create and move table_sc.pac
Write-Host "Step 5 & 6: Packaging table_sc directory..."
Set-Location -Path (Split-Path -Path $createPacScript -Parent)
uv run python (Split-Path -Path $createPacScript -Leaf) "table_sc" -o
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to package table_sc directory."
    Set-Location -Path $originalLocation
    exit 1
}
Move-Item -Path (Join-Path -Path (Split-Path -Path $createPacScript -Parent) -ChildPath "table_sc.pac") -Destination $outputTableScPac -Force
Set-Location -Path $originalLocation
Write-Host "Successfully packaged and moved table_sc.pac."

if ($IncludeVoice.IsPresent) {
    Write-Host "--- Processing voice assets (Optional) ---"

    # Optional Step a.1: Copy new voices
    Write-Host "Optional Step a.1: Merging new voice files..."
    $newVoicesWavDir = Join-Path -Path $newVoicesDir -ChildPath "wav"
    $outputVoiceWavDir = Join-Path -Path $outputVoiceDir -ChildPath "wav"
    if (Test-Path -Path $newVoicesWavDir) {
        Copy-Item -Path "$newVoicesWavDir\*" -Destination $outputVoiceWavDir -Recurse -Force
        Write-Host "New voice files merged."
    } else {
        Write-Host "No new voice files found to merge."
    }

    # Optional Step a.2: Create and move voice.pac
    Write-Host "Optional Step a.2: Packaging voice directory..."
    Set-Location -Path (Split-Path -Path $createPacScript -Parent)
    uv run python (Split-Path -Path $createPacScript -Leaf) "voice" -o
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to package voice directory."
        Set-Location -Path $originalLocation
        exit 1
    }
    Move-Item -Path (Join-Path -Path (Split-Path -Path $createPacScript -Parent) -ChildPath "voice.pac") -Destination $outputVoicePac -Force
    Set-Location -Path $originalLocation
    Write-Host "Successfully packaged and moved voice.pac."
}

# Cleanup
Write-Host "Cleaning up temporary files..."
Remove-Item -Path $tempJson -Force
Remove-Item -Path $tmpTbl -Force

Write-Host "Asset packaging process completed successfully!"
