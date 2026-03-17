"""
core_logic/ranking.py
──────────────────────
기간별 랭킹 집계 헬퍼. 
db/supabase_client.get_ranking()을 감싸는 고수준 래퍼.

TODO (Phase 3):
  - 세션별 포인트 로직 (승: +3, 무: +1, 패: 0 등)을 설정값으로 분리
"""

from db.supabase_client import get_ranking
from datetime import datetime, timedelta, timezone


def get_weekly_ranking(club_id: str) -> list[dict]:
    today = datetime.now(timezone.utc)
    start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    return get_ranking(club_id, start_date=start)


def get_monthly_ranking(club_id: str) -> list[dict]:
    today = datetime.now(timezone.utc)
    start = today.replace(day=1).strftime("%Y-%m-%d")
    return get_ranking(club_id, start_date=start)


def get_yearly_ranking(club_id: str) -> list[dict]:
    today = datetime.now(timezone.utc)
    start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    return get_ranking(club_id, start_date=start)


def get_all_time_ranking(club_id: str) -> list[dict]:
    return get_ranking(club_id)
