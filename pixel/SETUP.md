# 픽셀7 Termux + cron 셋업 가이드

이 가이드는 픽셀7을 24/7 자율 에이전트로 만들기 위한 최소 셋업입니다.
자율성 레벨 **L2 (스케줄 자율 실행)** 까지 다룹니다.

## 0. 사전 준비

- 픽셀7 (Android 13 이상)
- 약 30~60분 작업 시간
- OpenDart API 키 (https://opendart.fss.or.kr 무료 가입)
- Google Play의 Termux는 **사용하지 마세요** (구버전 + 업데이트 중단됨).

## 1. Termux 설치 (F-Droid 경로)

1. F-Droid 앱 설치: https://f-droid.org/
2. F-Droid에서 다음 두 개 설치:
   - **Termux**
   - **Termux:API** (알림/센서 접근용)

설치 후 한 번씩 실행해 권한 부여.

## 2. Termux 기본 패키지

```bash
pkg update && pkg upgrade -y
pkg install -y python git openssh termux-api cronie nano
pip install --upgrade pip
```

알림 권한 확인:

```bash
termux-notification --title "test" --content "hello"
```

폰에 알림이 뜨면 OK.

## 3. 저장소 접근 (선택)

```bash
termux-setup-storage
```

내부 저장소를 `~/storage/`에서 접근 가능. 카메라 파이프라인 등 확장 시 필요.

## 4. 리포지토리 클론

```bash
mkdir -p ~/projects
cd ~/projects
git clone <리포 URL> investment-hypothesis-tracker
cd investment-hypothesis-tracker
```

## 5. Python 의존성

Termux는 venv 대신 `pip install --user` 권장 (venv가 깨질 때가 있음).

```bash
pip install -r requirements.txt
```

## 6. 환경변수 설정

```bash
cp .env.example .env
nano .env
```

`OPENDART_API_KEY=...` 입력 후 저장.

## 7. 수동 실행으로 검증

```bash
python -m jobs.daily_disclosure_check
```

`logs/YYYY-MM-DD.log`에 결과가 쌓이고, 매칭이 있으면 알림이 떠야 합니다.

## 8. cron 데몬 시작

Termux에서는 cronie를 직접 띄워야 합니다:

```bash
crond
```

부팅마다 자동 실행하려면 `~/.bashrc`에 다음 추가:

```bash
pgrep -x crond > /dev/null || crond
```

## 9. cron 등록

```bash
crontab -e
```

[`crontab.example`](crontab.example) 내용을 참고하여 작성.

## 10. 배터리 최적화 회피 (중요)

Android는 백그라운드 앱을 죽입니다. Termux를 살려두는 방법:

1. **Wake Lock 활성화**: Termux 알림에서 "Acquire Wakelock" 탭
2. **배터리 최적화 제외**: 설정 → 앱 → Termux → 배터리 → "제한 없음"
3. **Termux:Boot 설치 (선택)**: F-Droid에서 설치하면 부팅 시 cron 자동 시작
4. **충전기 연결 권장**: cron 작업이 빈번하면 발열·소모 ↑

## 11. 동작 확인

다음날 새벽 작업이 돌고 나면:

```bash
ls -la logs/
tail -n 50 logs/$(date +%F).log
```

새 알림이 있으면 푸시도 와 있어야 합니다.

## 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| `crond: command not found` | `pkg install cronie` |
| 알림 안 뜸 | Termux:API 미설치 또는 알림 권한 미부여 |
| cron 실행 안 됨 | `pgrep -x crond`로 데몬 확인. 없으면 `crond` 실행 |
| 새벽에만 안 돌아감 | Doze 모드. wake lock + 배터리 최적화 해제 필요 |
| API 401/403 | `.env`의 키 확인 또는 OpenDart 일일 한도 초과 |

## 다음 단계 (L3 진입 시)

- Tasker 설치 → 위치/이벤트 트리거 시 cron job 즉시 호출
- `lib/notify.py`에 카카오 메모챗 / Slack 채널 추가
- `jobs/`에 morning_brief.py 등 추가하여 시간대별 분기
