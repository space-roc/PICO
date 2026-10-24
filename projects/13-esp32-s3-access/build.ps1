param(
    [string]$Port,
    [switch]$Upload
)

$ErrorActionPreference = "Stop"
$sourceRevision = "fda89ff2ff32eb1bce561901225c6a36fa684237"
$vendorFiles = @(
    "Display_SPD2010.cpp",
    "Display_SPD2010.h",
    "I2C_Driver.cpp",
    "I2C_Driver.h",
    "TCA9554PWR.cpp",
    "TCA9554PWR.h",
    "Touch_SPD2010.cpp",
    "Touch_SPD2010.h",
    "esp_lcd_spd2010.c",
    "esp_lcd_spd2010.h"
)
$fqbn = "esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc,PartitionScheme=app3M_fat9M_16MB"

$cli = Get-Command arduino-cli -ErrorAction SilentlyContinue
if ($cli) {
    $arduinoCli = $cli.Source
}
else {
    $arduinoCli = Join-Path $env:LOCALAPPDATA "Programs\ArduinoCLI\arduino-cli.exe"
}
if (-not (Test-Path -LiteralPath $arduinoCli)) {
    throw "Arduino CLI not found. Install Arduino CLI, then install esp32:esp32@3.1.1."
}

$tempRoot = Join-Path $env:TEMP ("esp32-s3-clock-" + [guid]::NewGuid().ToString("N"))
$sketchDir = Join-Path $tempRoot "ClockDemo"
$buildDir = Join-Path $tempRoot "build"
New-Item -ItemType Directory -Path $sketchDir -Force | Out-Null

try {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "ClockDemo.ino") -Destination $sketchDir

    $credentials = Join-Path $PSScriptRoot "wifi_secrets.h"
    if (Test-Path -LiteralPath $credentials) {
        Copy-Item -LiteralPath $credentials -Destination $sketchDir
    }
    else {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot "wifi_secrets.example.h") `
            -Destination (Join-Path $sketchDir "wifi_secrets.h")
        Write-Warning "Wi-Fi is not configured. The clock will use the build time until you add wifi_secrets.h and upload again."
    }

    $vendorBase = "https://raw.githubusercontent.com/waveshareteam/ESP32-S3-Touch-LCD-1.46/$sourceRevision/example/Arduino-3.1.1/examples/LVGL_Arduino"
    foreach ($file in $vendorFiles) {
        $destination = Join-Path $sketchDir $file
        & curl.exe -fL --retry 2 --silent --show-error --output $destination "$vendorBase/$file"
        if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $destination).Length -eq 0) {
            throw "Failed to download the Waveshare display driver file: $file"
        }
    }

    & $arduinoCli compile --fqbn $fqbn --build-path $buildDir $sketchDir
    if ($LASTEXITCODE -ne 0) {
        throw "Arduino compilation failed with exit code $LASTEXITCODE."
    }

    if ($Upload) {
        if ([string]::IsNullOrWhiteSpace($Port) -or $Port -notmatch '^COM\d+$') {
            throw "Specify the ESP32 serial port, for example -Port COM5."
        }
        & python -m esptool --chip esp32s3 --port $Port chip-id
        if ($LASTEXITCODE -ne 0) {
            throw "The device on $Port did not identify as an ESP32-S3; nothing was uploaded."
        }
        & $arduinoCli upload --fqbn $fqbn --port $Port --input-dir $buildDir $sketchDir
        if ($LASTEXITCODE -ne 0) {
            throw "Upload to $Port failed with exit code $LASTEXITCODE."
        }
        Write-Host "Clock uploaded to $Port."
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
