#!/usr/bin/env bash
# 가장 단순한 GitOps 테스트.
TIMESTAMP=$(date '+%H:%M:%S')
termux-notification \
    --title "🎉 안녕!" \
    --content "GitOps로 Claude가 보낸 알림. 도착 시각: $TIMESTAMP"
echo "[$(date -Iseconds)] hello 알림 발송"
