# 텔레그램 봇 셋업

이 봇은 채팅창으로 투자 트래커를 조작하게 해줍니다 (5분 대기 없이 즉시).

## 셋업 5단계 (총 약 5분)

### 1. BotFather에서 봇 생성

폰의 텔레그램에서 [@BotFather](https://t.me/BotFather) 검색 → 채팅 시작.

```
/newbot
```

질문 답하기:
- **봇 이름**: 아무거나 (예: `내 투자 트래커`)
- **봇 username**: `_bot` 으로 끝나야 함 (예: `mytrader_2026_bot`)

봇이 토큰을 줍니다 (`123456789:ABCdef...` 형식). **복사**.

### 2. .env에 토큰 추가

폰의 Termux에서:

```bash
echo 'TELEGRAM_BOT_TOKEN=받은_토큰_붙여넣기' >> ~/projects/investment-hypothesis-tracker/.env
```

### 3. crontab 재적용 (워치독 등록)

```bash
cd ~/projects/investment-hypothesis-tracker
git pull
crontab pixel/crontab.example
```

워치독 cron이 5분 안에 봇을 띄웁니다. 또는 즉시 시작:

```bash
nohup python -m jobs.tg_bot >> logs/tg_bot.log 2>&1 &
```

### 4. chat_id 확인

텔레그램에서 본인 봇 검색 → 채팅 시작 → 메시지:

```
/start
```

봇이 답장에 본인 `chat_id`를 알려줍니다 (예: `123456789`).

### 5. 본인만 받게 잠그기

```bash
echo 'ALLOWED_CHAT_IDS=받은_chat_id' >> ~/projects/investment-hypothesis-tracker/.env
pkill -f jobs.tg_bot   # 봇 재시작 (워치독이 5분 내 재기동)
```

이제 본인 외 사용자에게는 권한 없음 메시지가 갑니다.

## 사용 가능한 명령

| 명령 | 동작 |
|---|---|
| `/help` 또는 `/도움` | 명령 목록 |
| `/whoami` | 내 chat_id, user_id |
| `/가설` | 활성 가설 목록 |
| `/공시 회사명` | 최근 14일 공시 (예: `/공시 삼성전자`) |
| `/브리핑` | 즉시 모닝 브리핑 실행 + 결과 회신 |
| `/상태` | cron, git, 최근 sync 상태 |
| `/log 30` | 태스크 로그 최근 30줄 |

## 동작 확인

```bash
tail -f ~/projects/investment-hypothesis-tracker/logs/tg_bot.log
```

`[start] bot polling (allowed=...)` 로그가 보이면 성공.

## 재시작 / 정지

```bash
# 정지
pkill -f jobs.tg_bot

# 즉시 재시작 (워치독을 안 기다리고)
cd ~/projects/investment-hypothesis-tracker
nohup python -m jobs.tg_bot >> logs/tg_bot.log 2>&1 &
```

워치독을 완전히 끄고 봇도 같이 끄려면:

```bash
crontab -l | grep -v 'jobs.tg_bot' | crontab -
pkill -f jobs.tg_bot
```

## 트러블슈팅

| 증상 | 원인 |
|---|---|
| 봇이 답이 없음 | `pgrep -f jobs.tg_bot` 로 살아있는지 확인. 없으면 `tail logs/tg_bot.log` |
| "권한 없음" 메시지 | `ALLOWED_CHAT_IDS` 에 본인 chat_id 있는지 확인 |
| `/공시` 가 빈 결과 | 가설에 등록된 회사만 인식 — 먼저 `hypotheses.yaml` 에 추가 |
| `/브리핑` 실패 | OpenRouter/Anthropic 키 + `LLM_BACKEND` 설정 확인 |

## 보안 한 마디

- BotFather 토큰은 채팅에 절대 붙여넣지 말 것 (노출되면 즉시 BotFather에서 `/revoke` + 재발급)
- `ALLOWED_CHAT_IDS` 비워두면 누구든 봇 사용 가능 — 항상 본인 ID로 잠그세요.
- `/log` 같은 명령이 노출하는 정보를 검토하세요. 민감한 데이터가 포함될 수 있음.
