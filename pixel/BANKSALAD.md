# 뱅크샐러드/금융 알림 → 자산 대시보드 자동화

폰의 금융 앱 알림을 자동으로 LLM 파싱해서 대시보드까지 가는 파이프라인.

## 동작 흐름

```
[뱅크샐러드/카드/은행 알림]
   ↓
[MacroDroid 매크로]   ← 본인이 한 번 셋업
   ↓ (Telegram 봇으로 /거래 명령 전송)
[봇이 받음]
   ↓
[Claude Haiku가 알림 텍스트 파싱]
   ↓ (kind, amount, category, ... 추출)
[data/transactions/transactions.jsonl 추가]
   ↓
[/자산, /오늘 명령으로 대시보드 조회]
```

## 1단계 — 수동 입력으로 먼저 검증 (5분)

봇한테 직접 알림 본문을 보내보세요:

```
/거래 신한카드 12,300원 사용 / 스타벅스 강남점
```

봇이 LLM으로 자동 파싱:
```
✅ 저장됨
• 종류: expense
• 금액: 12,300원
• 카테고리: 식음료
• 상대: 스타벅스
• 계좌: 신한카드
```

다양한 포맷 다 가능:
```
/거래 KB증권 삼성전자 100주 매수 7,000,000원 체결
/거래 국민은행 입금 3,500,000원 / 급여
/거산 11월 카드 자동결제 89,500원 SK텔레콤
```

확인:
```
/자산
/오늘
```

## 2단계 — MacroDroid로 자동화 (10분)

알림이 도착하면 자동으로 봇한테 보내게 함.

### 매크로 셋업

폰의 **MacroDroid 앱** 열기 → **+ 매크로 추가**:

#### 트리거
- **알림** → **알림 수신**
- 앱 선택: **뱅크샐러드** (또는 모니터링하고 싶은 금융 앱들)
- 프리셋 옵션: "본문 포함" 같은 거 비워두기 (모든 알림 통과)

#### 액션
- **HTTP 요청**
- URL: `https://api.telegram.org/bot{본인_봇_토큰}/sendMessage`
- 메서드: `POST`
- Content type: `application/json`
- Body:
  ```json
  {
    "chat_id": 50196097,
    "text": "/거래 [notification_title] [notification_text]"
  }
  ```
  - `[notification_title]`, `[notification_text]` 는 MacroDroid의 magic text
  - 본인 chat_id로 교체

#### 조건 (선택)
- "거래", "사용", "결제", "입금" 등 키워드 포함 알림만 통과시키기
  → 광고/공지 알림 필터링

### 활성화

- 매크로 저장
- 매크로 목록에서 토글 ON

이제 뱅크샐러드 알림이 올 때마다:
1. MacroDroid가 캡처
2. 봇으로 `/거래 알림본문` POST
3. 봇이 LLM 파싱 후 저장

## 3단계 — 활용

### 봇 명령
```
/자산        — 오늘/7일/전체 대시보드
/오늘        — 오늘 거래 목록
/거래 [본문]  — 수동 입력 (자동화 안 잡힌 거)
```

### 데이터 직접 분석
```bash
cat ~/projects/investment-hypothesis-tracker/data/transactions/transactions.jsonl | jq .
```

### 카테고리별/월별 집계
나중에 추가할 명령 후보:
- `/월간` — 이번 달 카테고리별 지출
- `/추세` — 최근 30일 일자별 그래프
- `/예산` — 카테고리별 예산 vs 실제
- `/CSV` — 거래 내역 CSV 다운로드

원하시면 채팅에서 부탁하세요.

## 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| `/거래` 가 "파싱 실패" | 알림 본문이 너무 모호하거나 LLM 응답이 JSON 아님. 본문 직접 보고 수동 정정 |
| MacroDroid가 알림 못 잡음 | 설정 → 알림 액세스 → MacroDroid 권한 ON |
| 봇한테 메시지 안 옴 | MacroDroid HTTP 요청 결과 확인. 토큰/chat_id 오타? |
| 같은 알림 두 번 처리 | MacroDroid 중복 알림 필터 활성화 |

## 보안

- `data/transactions/` 는 `.gitignore` 처리됨 — 깃에 안 올라감
- 봇 토큰만 알면 누구나 메시지 보낼 수 있으니 `ALLOWED_CHAT_IDS` 잠금 필수
- MacroDroid가 봇 토큰을 알게 되니 매크로 export 시 토큰 빠짐 주의
