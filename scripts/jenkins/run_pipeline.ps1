# 수동 실행 스크립트 (Windows)
# 사용: .\scripts\jenkins\run_pipeline.ps1
#       .\scripts\jenkins\run_pipeline.ps1 --override KAKAO_API_KEY=xxx

$ErrorActionPreference = "Stop"

$Root   = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Python = "$Root\venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "venv 없음. 먼저 실행하세요:" -ForegroundColor Red
    Write-Host "  python -m venv venv && venv\Scripts\pip install -r requirements.txt"
    exit 1
}

New-Item -ItemType Directory -Force "$Root\data" | Out-Null

& $Python "$Root\scripts\pipeline.py" all --storage redis @args

if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "`n파이프라인 완료" -ForegroundColor Green
