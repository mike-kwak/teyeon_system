"""
pages/05_랭킹.py
─────────────────
기간별 KDK 랭킹 대시보드 + (운영진) 수동 포인트 부여.
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone
from db.supabase_client import get_ranking, add_ranking_points, get_all_members

st.set_page_config(page_title="랭킹 | TEYEON", page_icon="🏆", layout="wide")

if not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.stop()

CLUB_ID  = os.environ.get("CLUB_ID", "")
is_admin = st.session_state.get("is_admin", False)
today    = datetime.now(timezone.utc)

st.markdown("## 🏆 랭킹")

# ── 기간 선택 ─────────────────────────────────────────────────────────────
period = st.radio("기간 선택", ["이번 주", "이번 달", "올해", "전체"], horizontal=True)

def _period_dates(period: str):
    if period == "이번 주":
        start = today - __import__("datetime").timedelta(days=today.weekday())
        return start.strftime("%Y-%m-%d"), None
    elif period == "이번 달":
        return today.replace(day=1).strftime("%Y-%m-%d"), None
    elif period == "올해":
        return today.replace(month=1, day=1).strftime("%Y-%m-%d"), None
    return None, None

start_date, end_date = _period_dates(period)

# ── 랭킹 테이블 ───────────────────────────────────────────────────────────
try:
    ranking = get_ranking(CLUB_ID, start_date=start_date, end_date=end_date)
    if ranking:
        medals = ["🥇", "🥈", "🥉"]
        rows   = []
        for i, r in enumerate(ranking, 1):
            medal = medals[i-1] if i <= 3 else str(i)
            rows.append({"순위": medal, "닉네임": r["nickname"], "포인트": r["total_points"]})
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("해당 기간의 랭킹 데이터가 없습니다.")
except Exception as e:
    st.error(f"랭킹 조회 오류: {e}")

st.divider()

# ── 수동 포인트 부여 (운영진) ─────────────────────────────────────────────
if is_admin:
    st.markdown("### ✏️ 수동 포인트 부여")
    with st.form("point_form"):
        members = get_all_members(CLUB_ID)
        member_map = {m["id"]: m["nickname"] for m in members}
        target_id = st.selectbox("회원 선택", options=list(member_map.keys()),
                                  format_func=lambda x: member_map[x])
        pts    = st.number_input("포인트 (음수 가능)", value=0, step=10)
        reason = st.text_input("사유")
        if st.form_submit_button("부여", type="primary"):
            if not reason:
                st.warning("사유를 입력해주세요.")
            else:
                try:
                    add_ranking_points(CLUB_ID, target_id, int(pts), reason="manual")
                    st.success(f"포인트 부여 완료: {member_map[target_id]} +{pts}pt")
                    st.rerun()
                except Exception as e:
                    st.error(f"부여 실패: {e}")
