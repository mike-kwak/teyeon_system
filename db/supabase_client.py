"""
db/supabase_client.py
─────────────────────
Supabase 연결 싱글턴 + 공통 쿼리 헬퍼.
모든 페이지에서 `from db.supabase_client import get_client` 로 임포트.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

from supabase import create_client, Client

load_dotenv()


# ── 싱글턴 클라이언트 ────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_client() -> Client:
    """Supabase 클라이언트를 최초 1회만 생성하여 재사용."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL과 SUPABASE_ANON_KEY를 .env 파일에 설정해주세요."
        )
    return create_client(url, key)


# ── 회원(members) 헬퍼 ───────────────────────────────────────────────────
def upsert_member(kakao_id: int, nickname: str, profile_image: str = None, email: str = None) -> dict:
    """카카오 로그인 성공 시 회원 정보를 upsert(있으면 update, 없으면 insert)."""
    client = get_client()
    data = {
        "kakao_id": kakao_id,
        "nickname": nickname,
        "profile_image": profile_image,
        "email": email,
    }
    res = (
        client.table("members")
        .upsert(data, on_conflict="kakao_id")
        .execute()
    )
    return res.data[0] if res.data else {}


def get_member_by_kakao_id(kakao_id: int) -> dict | None:
    """kakao_id로 회원 조회. 없으면 None 반환."""
    client = get_client()
    res = (
        client.table("members")
        .select("*")
        .eq("kakao_id", kakao_id)
        .single()
        .execute()
    )
    return res.data


def get_all_members(club_id: str = None) -> list[dict]:
    """전체(또는 특정 클럽) 회원 목록 조회."""
    client = get_client()
    query = client.table("members").select("*")
    if club_id:
        query = query.eq("club_id", club_id)
    return query.execute().data or []


# ── KDK 세션 헬퍼 ────────────────────────────────────────────────────────
def create_kdk_session(club_id: str, session_date: str, created_by: str, note: str = "") -> dict:
    """새 KDK 세션을 생성하고 반환."""
    client = get_client()
    res = (
        client.table("kdk_sessions")
        .insert({
            "club_id": club_id,
            "session_date": session_date,
            "created_by": created_by,
            "note": note,
            "status": "draft",
        })
        .execute()
    )
    return res.data[0] if res.data else {}


def get_kdk_sessions(club_id: str, limit: int = 20) -> list[dict]:
    """최근 KDK 세션 목록 조회."""
    client = get_client()
    return (
        client.table("kdk_sessions")
        .select("*")
        .eq("club_id", club_id)
        .order("session_date", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )


def get_kdk_session(session_id: str) -> dict | None:
    """단일 KDK 세션 조회."""
    client = get_client()
    res = (
        client.table("kdk_sessions")
        .select("*, kdk_results(*), kdk_matches(*)")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return res.data


def update_kdk_session_status(session_id: str, status: str) -> dict:
    """KDK 세션 상태 업데이트 (draft → in_progress → completed)."""
    client = get_client()
    res = (
        client.table("kdk_sessions")
        .update({"status": status})
        .eq("id", session_id)
        .execute()
    )
    return res.data[0] if res.data else {}


# ── KDK 결과 헬퍼 ────────────────────────────────────────────────────────
def upsert_kdk_results(results: list[dict]) -> list[dict]:
    """경기 결과 배치 upsert. results = [{session_id, member_id, wins, ...}, ...]"""
    client = get_client()
    res = (
        client.table("kdk_results")
        .upsert(results, on_conflict="session_id,member_id")
        .execute()
    )
    return res.data or []


# ── 재무 헬퍼 ────────────────────────────────────────────────────────────
def insert_finance_record(
    club_id: str,
    type_: str,
    amount: int,
    description: str,
    created_by: str,
    session_id: str = None,
    member_id: str = None,
) -> dict:
    """재무 레코드 단건 삽입."""
    client = get_client()
    res = (
        client.table("finance_records")
        .insert({
            "club_id": club_id,
            "session_id": session_id,
            "member_id": member_id,
            "type": type_,
            "amount": amount,
            "description": description,
            "created_by": created_by,
        })
        .execute()
    )
    return res.data[0] if res.data else {}


def get_finance_records(club_id: str, limit: int = 50) -> list[dict]:
    """재무 기록 조회 (최신순)."""
    client = get_client()
    return (
        client.table("finance_records")
        .select("*, members(nickname)")
        .eq("club_id", club_id)
        .order("recorded_at", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )


# ── 랭킹 포인트 헬퍼 ─────────────────────────────────────────────────────
def add_ranking_points(
    club_id: str,
    member_id: str,
    points: int,
    reason: str,
    session_id: str = None,
) -> dict:
    """포인트 적립 (KDK 완료 시 자동 혹은 수동 부여 모두 사용)."""
    client = get_client()
    res = (
        client.table("ranking_points")
        .insert({
            "club_id": club_id,
            "member_id": member_id,
            "session_id": session_id,
            "points": points,
            "reason": reason,
        })
        .execute()
    )
    return res.data[0] if res.data else {}


def get_ranking(club_id: str, start_date: str = None, end_date: str = None) -> list[dict]:
    """
    기간별 랭킹 집계.
    반환: [{member_id, nickname, total_points}, ...] 포인트 내림차순
    """
    client = get_client()
    query = (
        client.table("ranking_points")
        .select("member_id, points, members(nickname)")
        .eq("club_id", club_id)
    )
    if start_date:
        query = query.gte("awarded_at", start_date)
    if end_date:
        query = query.lte("awarded_at", end_date)

    rows = query.execute().data or []

    # Python 쪽에서 집계 (Supabase Free tier에서 GROUP BY RPC 없이 처리)
    aggregated: dict[str, dict] = {}
    for row in rows:
        mid = row["member_id"]
        if mid not in aggregated:
            aggregated[mid] = {
                "member_id": mid,
                "nickname": row.get("members", {}).get("nickname", "알 수 없음"),
                "total_points": 0,
            }
        aggregated[mid]["total_points"] += row["points"]

    return sorted(aggregated.values(), key=lambda x: x["total_points"], reverse=True)
