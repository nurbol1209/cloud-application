$python = "python"
$venvPython = Join-Path $PSScriptRoot "..\..\..\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
}

Write-Host "1. Ruff lint"
& $python -m ruff check app scripts
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff lint failed"
    exit $LASTEXITCODE
}

Write-Host "2. Ruff format check"
& $python -m ruff format --check app scripts
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff format check failed"
    exit $LASTEXITCODE
}

Write-Host "QUALITY CHECK PASSED"
