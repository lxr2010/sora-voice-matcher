# PowerShell Script to Convert AT9 to WAV

# --- CONFIGURATION --- 
# Set the root directory for the script
$scriptRoot = $PSScriptRoot

# Automatically determine the path to the at9tool executable
$at9toolPath = Join-Path -Path $scriptRoot -ChildPath "atractool-reloaded\res\psv_at9tool.exe"

# Set the root directory for the voice files based on the script's location
$voiceRoot = Join-Path -Path $PSScriptRoot -ChildPath "FC-Steam\Trails in the Sky FC\voice"
# --- END OF CONFIGURATION ---

# Define source (at9) and destination (wav) directories
$sourceDir = Join-Path -Path $voiceRoot -ChildPath "at9"
$destDir = Join-Path -Path $voiceRoot -ChildPath "wav"

# --- VALIDATION CHECKS ---
# Check if the at9tool executable exists
if (-not (Test-Path -Path $at9toolPath -PathType Leaf)) {
    Write-Error "AT9 tool not found at '$at9toolPath'. Please update the path in the script."
    exit 1
}

# Check if the source directory exists
if (-not (Test-Path -Path $sourceDir -PathType Container)) {
    Write-Error "Source directory not found: '$sourceDir'"
    exit 1
}

# --- SCRIPT EXECUTION ---
# Create the destination directory if it doesn't exist
if (-not (Test-Path -Path $destDir -PathType Container)) {
    Write-Host "Destination directory '$destDir' not found. Creating it..."
    try {
        New-Item -Path $destDir -ItemType Directory -ErrorAction Stop | Out-Null
    }
    catch {
        Write-Error "Failed to create destination directory '$destDir'. Error: $_"
        exit 1
    }
}

# Find all .at9 files recursively
Write-Host "Searching for .at9 files in '$sourceDir'..."
$at9Files = Get-ChildItem -Path $sourceDir -Filter "*.at9" -Recurse

if ($at9Files.Count -eq 0) {
    Write-Warning "No .at9 files found."
    exit 0
}

Write-Host "Found $($at9Files.Count) files to convert."

# Loop through each file and convert it
$successCount = 0
$failCount = 0
foreach ($file in $at9Files) {
    $inputFile = $file.FullName
    $outputFileName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) + ".wav"
    $outputFile = Join-Path -Path $destDir -ChildPath $outputFileName

    Write-Host "Converting '$($file.Name)'..."

    try {
        # Execute the conversion command
        & $at9toolPath -d -repeat 1 $inputFile $outputFile
        if ($LASTEXITCODE -eq 0) {
            $successCount++
        } else {
            throw "at9tool returned a non-zero exit code: $LASTEXITCODE"
        }
    }
    catch {
        Write-Error "Failed to convert '$($file.Name)'. Details: $_"
        $failCount++
    }
}

# --- SUMMARY ---
Write-Host "`nConversion complete."
Write-Host "Successfully converted: $successCount"
Write-Host "Failed to convert:     $failCount"
