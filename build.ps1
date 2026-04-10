# Default option is to run build, like a Makefile
param(
    [string]$Task = "build",
    [string]$additional_args = "--standalone"
)

$buildProject = {
    Write-Host "Fixing nodriver network.py encoding..."
    $NODRIVER_LOC = Invoke-Expression "python -c `"import site; print(site.getsitepackages()[-1] + '/nodriver/cdp/network.py')`""
    Get-Content "$NODRIVER_LOC" | Set-Content -Encoding utf8 ".\network-fix.py"
    Copy-Item -Path ".\network-fix.py" -Destination "$NODRIVER_LOC" -Force
    Remove-Item -Path ".\network-fix.py"
    
    Write-Host "Building Just Eat Linker..."
    pyside6-project build pyproject.toml

    $argsArray = $additional_args -split " "


    python -m nuitka --show-progress --assume-yes-for-downloads @argsArray JustEatLinker.py
}

$cleanBuild = {
    Write-Host "Cleaning..."
    Remove-Item -Recurse -Force JustEatLinker.exe, ./JustEatLinker.build/, ./JustEatLinker.dist/, ./JustEatLinker.onefile-build/
}

switch ($Task.ToLower()) {
    "build" {
        & $buildProject
        break
    }
    "clean" {
        & $cleanBuild
        break
    }
    default {
        Write-Host "Unknown task: $Task" -ForegroundColor Red
        Write-Host "Available tasks: build, clean"
        break
    }
}