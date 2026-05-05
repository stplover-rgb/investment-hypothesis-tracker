#!/usr/bin/env bash
# Gemini (Google AI Studio) 백엔드 원샷 셋업.
# 사용:
#   bash scripts/setup_gemini.sh

set -euo pipefail

PROJ="${PROJ:-$HOME/projects/investment-hypothesis-tracker}"
ENV_FILE="$PROJ/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE 없음. 먼저 부트스트랩부터." >&2
    exit 1
fi

cd "$PROJ"

echo "==> 최신 코드 동기화"
git pull --quiet --ff-only || echo "(pull 스킵)"

echo "==> 기존 백엔드 라인 정리"
sed -i -e '/^OPENROUTER_/d' \
       -e '/^ANTHROPIC_/d' \
       -e '/^NVIDIA_/d' \
       -e '/^GEMINI_/d' \
       -e '/^LLM_BACKEND=/d' \
       "$ENV_FILE"

echo "==> Gemini 설정 추가"
{
    echo 'LLM_BACKEND=gemini'
    echo 'GEMINI_MODEL=gemini-2.0-flash-exp'
} >> "$ENV_FILE"

echo ""
echo "==> Gemini API 키 입력 (AIzaSy... 로 시작)"
echo "    aistudio.google.com → Get API Key"
echo ""
read -r -s -p "Gemini 키 (입력 안 보임): " GEMINI_KEY
echo ""

if [ -z "$GEMINI_KEY" ]; then
    echo "ERROR: 키가 비어있음. 중단." >&2
    exit 1
fi
if [[ "$GEMINI_KEY" != AIzaSy* ]]; then
    echo "WARN: 키가 'AIzaSy' 로 시작하지 않음. 그래도 저장."
fi
echo "GEMINI_API_KEY=$GEMINI_KEY" >> "$ENV_FILE"

echo "==> 봇 재시작"
pkill -9 -f 'jobs.tg_bot' 2>/dev/null || true
sleep 3
nohup python -m jobs.tg_bot >> logs/tg_bot.log 2>&1 &
disown 2>/dev/null || true
sleep 3

echo ""
echo "==> 봇 상태"
if pgrep -f 'jobs.tg_bot' >/dev/null; then
    echo "  살아있음: $(pgrep -fa 'jobs.tg_bot' | head -1)"
else
    echo "  WARN: 봇 안 보임. logs/tg_bot.log 확인"
fi

echo ""
echo "==> 최종 .env (마스킹)"
sed 's/=.*/=***/' "$ENV_FILE"

echo ""
echo "============================================"
echo " 완료. 텔레그램에서 /브리핑 보내보세요."
echo "============================================"
