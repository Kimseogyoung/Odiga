#!/bin/bash
# 수동 실행 스크립트 (Linux/Mac)
# 사용: bash scripts/jenkins/run_pipeline.sh
#       bash scripts/jenkins/run_pipeline.sh --override KAKAO_API_KEY=xxx
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="$ROOT/venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "venv 없음. 먼저 실행하세요:"
    echo "  python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

mkdir -p "$ROOT/data"

"$PYTHON" "$ROOT/scripts/pipeline.py" all --storage redis "$@"
