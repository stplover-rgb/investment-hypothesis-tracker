#!/usr/bin/env bash
# GitOps 활성화 검증용 첫 태스크.
# 5분 후 자동 실행되며, 모닝 브리핑이 한 번 돌고 알림이 온다면 전체 파이프라인 OK.

set -uo pipefail
cd "$(dirname "$0")/../.."

echo "==================================================="
echo " GitOps 검증 태스크 시작: $(date -Iseconds)"
echo "==================================================="

echo ""
echo "[1/3] 환경 확인"
echo "  PWD: $(pwd)"
echo "  PYTHON: $(command -v python)"
echo "  GIT HEAD: $(git rev-parse --short HEAD)"
echo "  BRANCH: $(git rev-parse --abbrev-ref HEAD)"

echo ""
echo "[2/3] Termux 알림 발송 (있다면)"
if command -v termux-notification >/dev/null 2>&1; then
    termux-notification --title "✅ GitOps 활성화 성공" \
        --content "Claude가 push한 태스크가 폰에서 자동 실행됨. 5분 내 모닝 브리핑도 도착 예정." \
        && echo "  알림 OK"
else
    echo "  termux-notification 미설치 (스킵)"
fi

echo ""
echo "[3/3] 모닝 브리핑 1회 실행"
python -m jobs.morning_brief

echo ""
echo "==================================================="
echo " 검증 완료: $(date -Iseconds)"
echo "==================================================="
