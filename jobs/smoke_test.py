"""셋업이 제대로 됐는지 확인하는 smoke test.

OpenDart API 키 없이도 실행 가능. 다음을 검증:
- Python 모듈 임포트
- hypotheses.yaml 로드
- 키워드 매칭 로직
- 파일 로그 쓰기
- Termux 알림 (있으면)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.hypotheses import active, load_hypotheses  # noqa: E402
from lib.notify import log_to_file, termux_notify  # noqa: E402


def main() -> int:
    print("=== Investment Hypothesis Tracker — Smoke Test ===\n")

    yaml_path = ROOT / "hypotheses.yaml"
    print(f"[1/4] hypotheses.yaml 로드 중... ({yaml_path})")
    hypotheses = load_hypotheses(yaml_path)
    actives = active(hypotheses)
    print(f"      OK — 전체 {len(hypotheses)}개, 활성 {len(actives)}개")
    for h in actives:
        print(f"        - [{h.id}] {h.corp_name}: {h.title}")

    print("\n[2/4] 키워드 매칭 로직 테스트...")
    if actives:
        sample = "주요사항보고서(자기주식취득결정)"
        matched = actives[0].matches(sample)
        print(f"      샘플 공시명: {sample}")
        print(f"      매칭 키워드: {matched if matched else '(없음)'}")
        print("      OK")
    else:
        print("      활성 가설이 없어 스킵")

    log_dir = ROOT / "logs"
    print(f"\n[3/4] 파일 로그 쓰기 테스트... ({log_dir})")
    log_to_file("smoke test entry", log_dir)
    print("      OK — logs/ 폴더 확인")

    print("\n[4/4] Termux 알림 테스트...")
    sent = termux_notify("Smoke Test", "셋업 완료! L2 자동화 준비됨.")
    if sent:
        print("      OK — 폰 알림 확인하세요")
    else:
        print("      SKIP — termux-notification 미설치 (Termux:API 패키지 필요).")
        print("              데스크탑 환경이면 정상입니다.")

    print("\n✅ 모든 검증 통과. 다음 단계: OpenDart API 키 발급 후 .env 입력.")
    print("   가이드: pixel/QUICKSTART.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
