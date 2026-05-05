#!/usr/bin/env bash
# Termux용 원샷 부트스트랩.
# Termux에서 다음 한 줄로 실행:
#   curl -fsSL https://raw.githubusercontent.com/stplover-rgb/investment-hypothesis-tracker/claude/claude-pixel-automation-KFk4C/scripts/bootstrap.sh | bash
#
# 또는 이미 클론한 상태라면:
#   bash scripts/bootstrap.sh

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/stplover-rgb/investment-hypothesis-tracker.git}"
BRANCH="${BRANCH:-claude/claude-pixel-automation-KFk4C}"
PROJ_DIR="${PROJ_DIR:-$HOME/projects/investment-hypothesis-tracker}"

echo "==> Termux 패키지 설치"
pkg update -y
pkg install -y python python-pip git termux-api cronie nano

# 주의: Termux에서는 `pip install --upgrade pip` 가 의도적으로 차단됨
# (python-pip 패키지로 관리되기 때문). 그래서 pip 업그레이드는 생략한다.

if [ ! -d "$PROJ_DIR" ]; then
    echo "==> 저장소 클론: $REPO_URL"
    mkdir -p "$(dirname "$PROJ_DIR")"
    git clone -b "$BRANCH" "$REPO_URL" "$PROJ_DIR"
else
    echo "==> 이미 존재 — 최신화"
    git -C "$PROJ_DIR" fetch origin "$BRANCH"
    git -C "$PROJ_DIR" checkout "$BRANCH"
    git -C "$PROJ_DIR" pull --ff-only origin "$BRANCH"
fi

echo "==> Python 패키지 설치"
cd "$PROJ_DIR"
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "==> .env 생성됨 (아직 키 미입력 상태)"
fi

echo "==> Smoke test 실행"
python -m jobs.smoke_test || true

cat <<'TXT'

============================================================
  부트스트랩 완료.

  다음 단계:
  1) OpenDart API 키 발급
       → https://opendart.fss.or.kr → 가입 → 인증키 신청
  2) .env에 키 입력
       → nano .env
       → OPENDART_API_KEY=발급받은키
  3) 실제 실행
       → python -m jobs.daily_disclosure_check
  4) cron 등록 (자동 반복)
       → pixel/QUICKSTART.md 8단계 참조
============================================================
TXT
