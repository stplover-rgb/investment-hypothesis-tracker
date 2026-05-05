"""Minimal OpenDart REST client.

OpenDart 공식 문서: https://opendart.fss.or.kr/guide/main.do
이 모듈은 cron 환경에서 가볍게 돌아가도록 requests만 사용한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import requests

BASE_URL = "https://opendart.fss.or.kr/api"


@dataclass(frozen=True)
class Disclosure:
    rcept_no: str
    corp_code: str
    corp_name: str
    report_nm: str
    rcept_dt: str

    @property
    def url(self) -> str:
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={self.rcept_no}"


class OpenDartClient:
    def __init__(self, api_key: str, *, timeout: float = 10.0):
        self.api_key = api_key
        self.timeout = timeout

    def search_disclosures(
        self,
        corp_code: str,
        bgn_de: date,
        end_de: date,
        *,
        page_count: int = 100,
    ) -> list[Disclosure]:
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": bgn_de.strftime("%Y%m%d"),
            "end_de": end_de.strftime("%Y%m%d"),
            "page_count": page_count,
        }
        resp = requests.get(f"{BASE_URL}/list.json", params=params, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        status = payload.get("status")
        # "013" = no data — treat as empty rather than error
        if status == "013":
            return []
        if status != "000":
            raise RuntimeError(f"OpenDart error {status}: {payload.get('message')}")
        return [
            Disclosure(
                rcept_no=item["rcept_no"],
                corp_code=item["corp_code"],
                corp_name=item["corp_name"],
                report_nm=item["report_nm"],
                rcept_dt=item["rcept_dt"],
            )
            for item in payload.get("list", [])
        ]
