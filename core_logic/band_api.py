"""
core_logic/band_api.py
───────────────────────
카카오 밴드 API 연동 — 참석자 목록 및 게스트 구분.

TODO (Phase 3):
  - get_attendees()     : 특정 밴드 포스트의 참석 댓글 수집
  - parse_guest_flag()  : 댓글 내 '(게스트)' 패턴 파싱
  - get_partner_pairs() : 댓글에서 '@파트너지정' 패턴 파싱
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BAND_ACCESS_TOKEN = os.environ.get("BAND_ACCESS_TOKEN", "")
BAND_KEY          = os.environ.get("BAND_KEY", "")

_BAND_API_BASE = "https://openapi.band.us"


def get_post_comments(band_key: str, post_key: str) -> list[dict]:
    """
    밴드 포스트 댓글 목록 조회.
    Returns: [{author_name, body, created_at}, ...]
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")


def parse_attendees(comments: list[dict]) -> list[dict]:
    """
    댓글 목록에서 참석자와 게스트 여부를 파싱.
    '(게스트)' 키워드가 포함된 댓글 → is_guest=True
    Returns: [{name, is_guest, partner_request: str|None}, ...]
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")
