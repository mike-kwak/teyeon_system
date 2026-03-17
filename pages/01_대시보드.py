"""
pages/01_대시보드.py
────────────────────
홈 대시보드: 최근 KDK 세션 요약 + 이번 달 상위 랭킹 미리보기.
"""

import streamlit as st
from datetime import datetime, timezone
from db.supabase_client import get_client, get_kdk_sessions, get_ranking
import os

st.set_page_config(page_title="대시보드 | TEYEON", page_icon="🏠", layout="wide")

# ── 로그인 가드 ───────────────────────────────────────────────────────────
if not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.stop()

CLUB_ID = os.environ.get("CLUB_ID", "")

# ── 헤더 ─────────────────────────────────────────────────────────────────
st.markdown("## 🏠 대시보드")
today = datetime.now(timezone.utc)
st.caption(f"오늘: {today.strftime('%Y년 %m월 %d일')}")

# ── KPI 카드 ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

# TODO: 실제 집계 쿼리로 대체
with col1:
    st.metric("이번 달 세션", "—", help="이번 달 진행된 KDK 횟수")
with col2:
    st.metric("총 회원 수", "—", help="등록 회원 수")
with col3:
    st.metric("내 이달 포인트", "—", help="이번 달 내 포인트")
with col4:
    st.metric("클럽 잔액", "—원", help="누적 상벌금 잔액")

st.divider()

# ── 최근 세션 목록 ────────────────────────────────────────────────────────
st.markdown("### 📅 최근 KDK 세션")
try:
    sessions = get_kdk_sessions(CLUB_ID, limit=5)
    if sessions:
        for s in sessions:
            status_emoji = {"draft": "✏️", "in_progress": "▶️", "completed": "✅"}.get(s.get("status", ""), "❓")
            st.markdown(f"{status_emoji} **{s['session_date']}** — {s.get('note', '비고 없음')} `{s['status']}`")
    else:
        st.info("아직 진행된 세션이 없습니다.")
except Exception as e:
    st.error(f"세션 조회 오류: {e}")

st.divider()

# ── 이번 달 랭킹 미리보기 ─────────────────────────────────────────────────
st.markdown("### 🏆 이번 달 Top 5")
month_start = today.replace(day=1).strftime("%Y-%m-%d")
try:
    ranking = get_ranking(CLUB_ID, start_date=month_start)[:5]
    if ranking:
        for i, r in enumerate(ranking, 1):
            medal = ["🥇","🥈","🥉"].get(i-1, f"{i}위") if i <= 3 else f"{i}위"
            st.markdown(f"{medal} **{r['nickname']}** — {r['total_points']}pt")
    else:
        st.info("이번 달 랭킹 데이터가 없습니다.")
except Exception as e:
    st.error(f"랭킹 조회 오류: {e}")
