<#
.SYNOPSIS
    Updates game asset files (.pac) from the output directory to a specified game installation directory.

.DESCRIPTION
    This script automates the process of updating game files for Trails in the Sky SC.
    It backs up the original 'table_sc.pac' and 'voice.pac' files by renaming them with a .bak extension,
    and then copies the newly generated files from the local 'output' directory to the game's 'data' directory.

.PARAMETER GamePath
    The full path to the root directory of the game installation.
    Example: 'C:\Program Files (x86)\Steam\steamapps\common\Trails in the Sky SC'

.EXAMPLE
    .\update_game_files.ps1 -GamePath 'D:\SteamLibrary\steamapps\common\Trails in the Sky SC'
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, HelpMessage = "Path to the game's root directory.")]
    [string]$GamePath,

    [Parameter(HelpMessage = "Restore original files from backup.")]
    [switch]$Restore
)

# --- Configuration ---
$SourceDir = Join-Path -Path $PSScriptRoot -ChildPath "output"
$DestDataDir = Join-Path -Path $GamePath -ChildPath "pac/steam"
$FilesToUpdate = @("table_sc.pac", "voice.pac")

# --- Main Script ---
try {
    # Validate paths
    if (-not (Test-Path -Path $GamePath -PathType Container)) {
        throw "Game directory not found: $GamePath"
    }
    if (-not (Test-Path -Path $DestDataDir -PathType Container)) {
        throw "Game data directory not found: $DestDataDir. Please ensure the game path is correct."
    }

    if ($Restore) {
        # --- Restore Logic ---
        Write-Host "Starting file restoration process for: $GamePath" -ForegroundColor Yellow

        foreach ($file in $FilesToUpdate) {
            $destFile = Join-Path -Path $DestDataDir -ChildPath $file
            $backupFile = "$destFile.bak"

            Write-Host "`nProcessing: $file" -ForegroundColor Cyan

            if (Test-Path -Path $backupFile) {
                Write-Host "  - Restoring '$file' from backup..."
                Rename-Item -Path $backupFile -NewName $file -Force
                Write-Host "  - Restoration successful."
            } else {
                Write-Warning "  - Backup file not found, skipping: $backupFile"
            }
        }
        Write-Host "`nRestoration process completed successfully!" -ForegroundColor Green

    } else {
        # --- Update Logic ---
        if (-not (Test-Path -Path $SourceDir -PathType Container)) {
            throw "Source directory not found: $SourceDir"
        }

        Write-Host "Starting file update process for: $GamePath" -ForegroundColor Green

        foreach ($file in $FilesToUpdate) {
            $sourceFile = Join-Path -Path $SourceDir -ChildPath $file
            $destFile = Join-Path -Path $DestDataDir -ChildPath $file
            $backupFile = "$destFile.bak"

            if (-not (Test-Path -Path $sourceFile)) {
                Write-Warning "Source file not found, skipping: $sourceFile"
                continue
            }

            Write-Host "`nProcessing: $file" -ForegroundColor Cyan

            if ((Test-Path -Path $destFile) -and (-not (Test-Path -Path $backupFile))) {
                Write-Host "  - Backing up original file to: $backupFile"
                Rename-Item -Path $destFile -NewName "$($file).bak" -Force
            } elseif (Test-Path -Path $backupFile) {
                Write-Host "  - Backup file already exists. Skipping backup."
            } else {
                Write-Host "  - No original file found to back up."
            }

            Write-Host "  - Copying new file to: $destFile"
            Copy-Item -Path $sourceFile -Destination $destFile -Force

            Write-Host "  - '$file' updated successfully."
        }

        Write-Host "`nUpdate process completed successfully!" -ForegroundColor Green
    }

} catch {
    Write-Error "An error occurred: $_"
    exit 1
}
