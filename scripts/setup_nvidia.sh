#!/usr/bin/env bash
# NVIDIA NIM 백엔드 원샷 셋업.
# 사용:
#   bash scripts/setup_nvidia.sh
# 또는:
#   curl -fsSL https://raw.githubusercontent.com/stplover-rgb/investment-hypothesis-tracker/claude/claude-pixel-automation-KFk4C/scripts/setup_nvidia.sh | bash

set -euo pipefail

PROJ="${PROJ:-$HOME/projects/investment-hypothesis-tracker}"
ENV_FILE="$PROJ/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE 없음. 먼저 부트스트랩부터 진행하세요." >&2
    exit 1
fi

cd "$PROJ"

echo "==> 최신 코드 동기화"
git pull --quiet --ff-only || echo "(pull 실패 — 이미 최신이거나 충돌)"

echo "==> 기존 OpenRouter / Anthropic / LLM_BACKEND 줄 정리"
sed -i -e '/^OPENROUTER_/d' \
       -e '/^ANTHROPIC_/d' \
       -e '/^LLM_BACKEND=/d' \
       -e '/^NVIDIA_/d' \
       "$ENV_FILE"

echo "==> 기본 설정 추가"
{
    echo 'LLM_BACKEND=nvidia'
    echo 'NVIDIA_MODEL=meta/llama-3.3-70b-instruct'
} >> "$ENV_FILE"

echo ""
echo "==> NVIDIA API 키 입력 (nvapi-... 로 시작)"
echo "    프롬프트가 뜨면 길게 눌러 붙여넣기 + 엔터"
echo ""
read -r -p "NVIDIA 키: " NVIDIA_KEY
if [ -z "$NVIDIA_KEY" ]; then
    echo "ERROR: 키가 비어있음. 중단." >&2
    exit 1
fi
if [[ "$NVIDIA_KEY" != nvapi-* ]]; then
    echo "WARN: 키가 'nvapi-' 로 시작하지 않습니다. 그래도 저장할게요."
fi
echo "NVIDIA_API_KEY=$NVIDIA_KEY" >> "$ENV_FILE"

echo ""
echo "==> 봇 재시작 (env 다시 읽도록)"
pkill -f 'jobs.tg_bot' 2>/dev/null || true
sleep 2
nohup python -m jobs.tg_bot >> logs/tg_bot.log 2>&1 &
disown 2>/dev/null || true

sleep 2

echo ""
echo "==> 봇 상태 확인"
if pgrep -f 'jobs.tg_bot' >/dev/null; then
    echo "  봇 살아있음. PID: $(pgrep -f 'jobs.tg_bot' | head -1)"
else
    echo "  WARN: 봇이 안 보임. logs/tg_bot.log 확인 필요"
fi

echo ""
echo "==> 최종 .env (값 마스킹)"
sed 's/=.*/=***/' "$ENV_FILE"

echo ""
echo "============================================"
echo " 완료. 이제 텔레그램에서 /브리핑 보내보세요."
echo " 약 5~10초 후 한국어 brief가 채팅으로 도착합니다."
echo "============================================"
