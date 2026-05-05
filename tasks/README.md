# Task Queue

`scripts/auto_sync.sh`(cron이 5분마다 실행)가 이 디렉터리를 비운다.

## 사용 방법

`tasks/pending/` 에 셸 스크립트를 두고 commit + push 하면, 폰의 다음
auto_sync 사이클(최대 5분 후)에 한 번 실행되고 `tasks/done/` 로 옮겨진다.

## 파일 명명 규칙

`YYYYMMDD-NN-짧은설명.sh` 권장. 충돌 방지 + done 폴더에서 추적 용이.

예: `20260505-01-recompute-hypotheses.sh`

## 동작 방식

1. `git pull` 로 새 commit 가져오기
2. `tasks/pending/*.sh` 를 알파벳 순으로 하나씩 실행
3. 성공/실패 상관없이 `tasks/done/<unix_ts>-<name>` 로 이동
4. 출력은 `logs/tasks.log` 에 기록

## 예시 태스크

```bash
#!/usr/bin/env bash
# 모닝 브리핑 즉시 1회 실행
cd "$(dirname "$0")/../.."
python -m jobs.morning_brief
```

## ⚠️ 보안 모델

이 큐는 **검증 없이 실행되는 원격 명령 채널**이다.
- 리포에 push 권한 있는 모두가 폰에서 코드 실행 가능
- 공개/공유 리포에서는 활성화하지 말 것
- 개인용이라도 처음에는 `crontab -l` 로 auto_sync 등록 여부를 확인하고,
  의심스러운 commit은 pull 전에 검토

## 비활성화

```bash
crontab -l | grep -v auto_sync.sh | crontab -
```
