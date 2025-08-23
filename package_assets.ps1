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

# --- Configuration ---
$ErrorActionPreference = 'Stop'
$scriptRoot = $PSScriptRoot

# Paths to tools and assets
$json2TblScript = Join-Path -Path $scriptRoot -ChildPath "KuroTools v1.3\scripts&tables\json2tbl.py"
$createPacScript = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\create_pac.py"

# Source paths
$sourceJson = Join-Path -Path $scriptRoot -ChildPath "output\t_voice.json"
$sourceTableScDir = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\table_sc"
$sourceVoiceDir = Join-Path -Path $scriptRoot -ChildPath "kuro_mdl_tool\misc\voice"
$newVoicesDir = Join-Path -Path $scriptRoot -ChildPath "voice" # Converted Evo voices

# Output and temporary paths
$outputDir = Join-Path -Path $scriptRoot -ChildPath "output"
$tempPackagingDir = Join-Path -Path $outputDir -ChildPath "packaging_temp"
$tempTableScDir = Join-Path -Path $tempPackagingDir -ChildPath "table_sc"
$tempVoiceDir = Join-Path -Path $tempPackagingDir -ChildPath "voice"

# --- Main Script ---

# 1. Convert t_voice.json to t_voice.tbl
Write-Host "Step 1: Converting t_voice.json to t_voice.tbl..."
if (-not (Test-Path $sourceJson)) {
    Write-Error "Source file not found: $sourceJson. Please run the matching script first."
    exit 1
}
try {
    $toolDir = Split-Path -Path $json2TblScript -Parent
    Push-Location -Path $toolDir

    # Use absolute path for source json as we are in a different directory
    uv run python (Split-Path -Path $json2TblScript -Leaf) "$sourceJson"
    
    $generatedTblInToolDir = Join-Path -Path $toolDir -ChildPath "t_voice.tbl"
    $generatedTblInOutputDir = Join-Path -Path $outputDir -ChildPath "t_voice.tbl"

    if (-not (Test-Path $generatedTblInToolDir)) {
        Write-Error "Failed to generate t_voice.tbl. Check for errors from json2tbl.py."
        Pop-Location
        exit 1
    }
    
    Move-Item -Path $generatedTblInToolDir -Destination $generatedTblInOutputDir -Force
    Pop-Location
    Write-Host "t_voice.tbl generated successfully." -ForegroundColor Green
} catch {
    Write-Error "An error occurred while running json2tbl.py. Please check your Python environment and script paths."
    Pop-Location
    exit 1
}

# 2. Prepare temporary packaging directory
Write-Host "`nStep 2: Preparing temporary packaging directory..."
if (Test-Path $tempPackagingDir) {
    Write-Host "Cleaning up old temporary directory..."
    Remove-Item -Path $tempPackagingDir -Recurse -Force
}
New-Item -Path $tempPackagingDir -ItemType Directory | Out-Null

Write-Host "Copying original 'table_sc' and 'voice' assets..."
# Create the target directories first
New-Item -Path $tempTableScDir -ItemType Directory -Force | Out-Null
New-Item -Path $tempVoiceDir -ItemType Directory -Force | Out-Null

# Copy the contents of source directories to the temporary directories
Copy-Item -Path "$sourceTableScDir\*" -Destination $tempTableScDir -Recurse
Copy-Item -Path "$sourceVoiceDir\*" -Destination $tempVoiceDir -Recurse

# 3. Update assets in temporary directory
Write-Host "`nStep 3: Updating assets with new voice data..."
# Replace t_voice.tbl
Write-Host "Replacing t_voice.tbl..."
Move-Item -Path $generatedTblInOutputDir -Destination (Join-Path -Path $tempTableScDir -ChildPath "t_voice.tbl") -Force

# Merge new voice files
Write-Host "Merging new .wav files..."
if (Test-Path $newVoicesDir) {
    Copy-Item -Path "$newVoicesDir\*" -Destination $tempVoiceDir -Recurse -Force
    Write-Host "New voices merged."
} else {
    Write-Warning "Directory with new voices not found: $newVoicesDir. Continuing without merging new voices."
}

# 4. Repackage .pac files
Write-Host "`nStep 4: Repackaging .pac files..."

$toolDir = Split-Path -Path $createPacScript -Parent
Push-Location -Path $toolDir

try {
    # Repackage table_sc.pac
    Write-Host "Creating table_sc.pac..."
    uv run python (Split-Path -Path $createPacScript -Leaf) "$tempTableScDir" -o
    $generatedTablePacInToolDir = Join-Path -Path $toolDir -ChildPath "table_sc.pac"
    Move-Item -Path $generatedTablePacInToolDir -Destination $outputDir -Force
    Write-Host "table_sc.pac created successfully." -ForegroundColor Green

    # Repackage voice.pac
    Write-Host "Creating voice.pac..."
    uv run python (Split-Path -Path $createPacScript -Leaf) "$tempVoiceDir" -o -a "voice_new.pac"
    $generatedVoicePacInToolDir = Join-Path -Path $toolDir -ChildPath "voice_new.pac"
    
    # Check if voice.pac file exists and print file information
    if (Test-Path -Path $generatedVoicePacInToolDir) {
        $fileInfo = Get-Item -Path $generatedVoicePacInToolDir
        $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        
        Write-Host "Voice.pac file generated:" -ForegroundColor Cyan
        Write-Host "  - Path: $($fileInfo.FullName)" -ForegroundColor Cyan
        Write-Host "  - Size: ${fileSizeMB} MB" -ForegroundColor Cyan
        Write-Host "  - Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
        
        # Move the file to output directory
        Copy-Item -Path $generatedVoicePacInToolDir -Destination "$outputDir/voice.pac" -Force
        Write-Host "voice.pac created successfully." -ForegroundColor Green
    } else {
        Write-Warning "Warning: voice.pac file was not generated!"
    }
} catch {
    Write-Error "An error occurred during .pac file creation: $_"
} finally {
    Pop-Location
}

# 5. Clean up
Write-Host "`nStep 5: Cleaning up temporary files..."
Remove-Item -Path $tempPackagingDir -Recurse -Force
Write-Host "Cleanup complete."

Write-Host "`n--- Packaging Complete! ---" -ForegroundColor Cyan
Write-Host "The final files 'table_sc.pac' and 'voice.pac' are in the '$outputDir' directory."
