"""
pages/01_대시보드.py
────────────────────
홈 대시보드: 최근 KDK 세션 요약 + 이번 달 상위 랭킹 미리보기.
"""

import streamlit as st
from datetime import datetime, timezone
from db.supabase_client import get_client, get_kdk_sessions, get_ranking, check_auth_and_log
import os

st.set_page_config(page_title="대시보드 | TEYEON", page_icon="🏠", layout="wide")

# ── 권한 체크 및 로그 기록 ────────────────────────────────────────────────────────
check_auth_and_log("01_대시보드.py")

CLUB_ID = os.environ.get("CLUB_ID", "")

# ── 헤더 ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display: flex; align-items: center; gap: 18px; margin-bottom: 30px;">
    <div style="filter: drop-shadow(0 0 10px rgba(204, 255, 0, 0.6));">
        <svg viewBox="0 0 100 100" width="55" height="55">
            <circle cx="50" cy="50" r="48" fill="#CCFF00" />
            <path d="M25,20 Q50,50 25,80" fill="none" stroke="#0A0E1A" stroke-width="3" />
            <path d="M75,20 Q50,50 75,80" fill="none" stroke="#0A0E1A" stroke-width="3" />
        </svg>
    </div>
    <div style="display: flex; flex-direction: column; align-items: flex-start;">
        <div style="font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 2.8rem; letter-spacing: -3px; color: white; line-height: 0.85;">테연</div>
        <div style="font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 1rem; color: #CCFF00; font-style: italic; letter-spacing: 4px; transform: skewX(-10deg); line-height: 1;">테니스</div>
    </div>
    <div style="margin-left: auto; background: rgba(204, 255, 0, 0.1); color: #CCFF00; padding: 5px 15px; border-radius: 30px; font-size: 0.8rem; font-weight: 900; border: 1px solid rgba(204, 255, 0, 0.3); box-shadow: 0 4px 10px rgba(204, 255, 0, 0.1);">
        SINCE 2025
    </div>
</div>
""", unsafe_allow_html=True)

today = datetime.now(timezone.utc)
st.caption(f"📅 {today.strftime('%Y. %m. %d')} — {st.session_state.get('user', {}).get('nickname', '회원')}님 안녕하세요!")

# ── 🏆 2026 TEYEON Hall of Fame ──────────────────────────────────────────
from db.supabase_client import get_tournament_results
results = get_tournament_results()

if results:
    st.markdown("#### 🏆 2026 명예의 전당")
    # 네온 그린 & 네이비 조합의 프리미엄 카드
    cols = st.columns(min(len(results), 3))
    for i, res in enumerate(results[:3]):
        with cols[i]:
            st.markdown(f"""
            <div style="background: rgba(204, 255, 0, 0.05); 
                        padding: 20px; border-radius: 20px; border: 1px solid rgba(204, 255, 0, 0.15);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-bottom: 25px; transition: 0.3s;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #CCFF00; opacity: 0.8; letter-spacing: 1px;">{res['tournament_date']}</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: white; margin: 8px 0;">{res['tournament_name']}</div>
                <div style="font-size: 1.4rem; font-weight: 900; color: #CCFF00;">{res['rank']}</div>
                <div style="font-size: 0.9rem; color: #aab8d4; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                     {res['winners']}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── 📱 모바일 앱 스타일 그리드 네비게이션 ──────────────────────────────────────────
st.markdown("#### 🚀 퀵 메뉴")
grid_css = """
<style>
.nav-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 22px;
    padding: 20px;
    transition: all 0.3s ease;
    text-align: center;
    cursor: pointer;
}
.nav-card:hover {
    background: rgba(204, 255, 0, 0.05);
    border-color: #CCFF00;
    transform: translateY(-5px);
}
</style>
"""
st.markdown(grid_css, unsafe_allow_html=True)

nav_items = [
    {"icon": "🎾", "label": "대진 생성", "path": "02_대진생성.py"},
    {"icon": "🏃", "label": "경기 진행", "path": "03_경기진행.py"},
    {"icon": "📊", "label": "최근 결과", "path": "03_경기결과.py"},
    {"icon": "🏆", "label": "클럽 랭킹", "path": "05_랭킹.py"},
    {"icon": "💰", "label": "재무 기록", "path": "04_재무.py"},
    {"icon": "👥", "label": "멤버 정보", "path": "07_멤버정보.py"},
]

# 3열 구성
rows = [nav_items[i:i+3] for i in range(0, len(nav_items), 3)]
for row in rows:
    cols = st.columns(3)
    for i, item in enumerate(row):
        with cols[i]:
            st.page_link(f"pages/{item['path']}", label=f"{item['icon']} {item['label']}", use_container_width=True)

st.divider()

# ── 실시간 요약 (KPI) ──────────────────────────────────────────────────────
st.markdown("#### 📈 클럽 현황")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("이번 달 세션", "—")
with col2: st.metric("총 회원 수", "—")
with col3: st.metric("내 이달 포인트", "—")
with col4: st.metric("클럽 잔액", "—원")
