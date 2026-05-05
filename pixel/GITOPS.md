# GitOps 모드 — Claude가 폰에 코드를 "푸시"하는 방식

기본 자율성 L2(스케줄)에 더해, **원격에서 코드를 push 하면 5분 내 폰에서
자동으로 적용/실행되는** 패턴.

## 동작

```
[Claude/데스크탑]            [GitHub]            [픽셀7 Termux cron]
   git push      ───────►   브랜치 갱신   ◄───── */5분 git pull
                                                    │
                                                    ▼
                                        tasks/pending/*.sh 실행
                                                    │
                                                    ▼
                                        crontab 자동 재등록
```

## 활성화 (한 번만)

```bash
cd ~/projects/investment-hypothesis-tracker
git pull
crontab pixel/crontab.example
crontab -l    # */5 * * * * bash $PROJ/scripts/auto_sync.sh 보이는지 확인
```

이후 폰에서는 손댈 게 없다.

## 사용 시나리오

### 새 코드 자동 반영
Claude가 `lib/notify.py` 수정 → push → 5분 내 폰에서 다음 cron부터 새 코드 사용.

### 일회성 명령 실행
Claude가 다음 파일을 push:
```
tasks/pending/20260505-01-recompute.sh
```
내용:
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")/../.."
python -m jobs.daily_disclosure_check
```
→ 5분 내 자동 실행 → `tasks/done/<ts>-20260505-01-recompute.sh` 로 이동
→ 출력은 `logs/tasks.log` 에 기록.

### 스케줄 변경
Claude가 `pixel/crontab.example` 에 새 cron 줄 추가 → push → auto_sync가 pull
후 `crontab pixel/crontab.example` 자동 호출 → 새 스케줄 즉시 발효.

## 확인 방법

```bash
# 동기화 로그
tail -f ~/projects/investment-hypothesis-tracker/logs/sync.log

# 태스크 실행 로그
tail -f ~/projects/investment-hypothesis-tracker/logs/tasks.log

# 처리된 태스크 목록
ls -lt ~/projects/investment-hypothesis-tracker/tasks/done/
```

## ⚠️ 보안 — 꼭 읽으세요

이 모드를 켜면 **리포에 push 권한이 있는 모든 주체가 폰에서 임의 코드 실행
가능**합니다. 신뢰 모델이 바뀌니 다음을 검토:

1. **리포는 private 인가?** public이면 활성화 금지 (PR로 들어오는 코드도 실행됨)
2. **GitHub 계정 2FA 켜져 있나?**
3. **branch protection** 설정 — `claude/...` 브랜치만 자동 동기화하고, main은 수동
4. 의심스러우면 임시 정지:
   ```bash
   crontab -l | grep -v auto_sync.sh | crontab -
   ```

처음에는 며칠간 `tail -f logs/sync.log`로 동작을 모니터링하는 걸 권장.

## 비활성화

```bash
crontab -l | grep -v auto_sync.sh | crontab -
```

또는 전체 cron 정지:
```bash
pkill crond
```
