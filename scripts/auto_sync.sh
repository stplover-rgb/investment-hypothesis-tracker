#!/usr/bin/env bash
# 5분마다 cron이 호출. 원격 변경 사항을 가져오고 큐에 쌓인 태스크를 실행한다.
#
# 트레이드오프 / 보안: 이 스크립트가 cron에 등록되면, 리포에 push 권한이 있는
# 사람은 누구든 폰에서 코드를 실행할 수 있다. tasks/pending 의 .sh는 검증 없이
# 실행되니, 신뢰하지 않는 코드를 push하지 말 것.

set -uo pipefail  # -e 미사용: 일시적 네트워크 실패에 cron이 죽지 않게.

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ_DIR"
mkdir -p logs tasks/pending tasks/done

LOG="$PROJ_DIR/logs/sync.log"
TASKLOG="$PROJ_DIR/logs/tasks.log"

ts() { date -Iseconds; }

if ! git fetch origin --quiet 2>>"$LOG"; then
    echo "[$(ts)] fetch failed (network?)" >> "$LOG"
    exit 0
fi

LOCAL=$(git rev-parse HEAD 2>/dev/null) || exit 0
REMOTE=$(git rev-parse '@{u}' 2>/dev/null) || exit 0

if [ "$LOCAL" != "$REMOTE" ]; then
    if git pull --quiet --ff-only 2>>"$LOG"; then
        echo "[$(ts)] synced ${LOCAL:0:7} -> ${REMOTE:0:7}" >> "$LOG"
        # 일정이 바뀌었을 수 있으니 crontab 재적용
        crontab pixel/crontab.example >/dev/null 2>&1 || true
    else
        echo "[$(ts)] pull failed (non fast-forward?)" >> "$LOG"
        exit 0
    fi
fi

# Task queue: tasks/pending/*.sh 를 한 번씩 실행하고 done 으로 옮김
shopt -s nullglob
for task in tasks/pending/*.sh; do
    name=$(basename "$task")
    echo "[$(ts)] >>> $name" >> "$TASKLOG"
    if bash "$task" >> "$TASKLOG" 2>&1; then
        echo "[$(ts)] <<< $name OK" >> "$TASKLOG"
    else
        echo "[$(ts)] <<< $name FAILED (exit $?)" >> "$TASKLOG"
    fi
    mv "$task" "tasks/done/$(date +%s)-$name"
done
