import streamlit as st
import os
from datetime import datetime
import pandas as pd
from db.supabase_client import get_kdk_session, update_kdk_session_status, update_kdk_match_score, check_auth_and_log

st.set_page_config(page_title="경기 진행 | TEYEON", page_icon="🎾", layout="wide")

# 권한 체크
check_auth_and_log("03_경기진행.py")

# CSS: 가로형 스텝퍼 강제 및 UI 개선
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]:has(.score-stepper-row) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 10px !important;
}
div[data-testid="stHorizontalBlock"]:has(.score-stepper-row) > div[data-testid="column"] {
    width: auto !important;
    flex: 1 !important;
}
.match-card {
    background: white; border-radius: 15px; padding: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 15px;
    border: 1px solid #eee;
}
.score-display {
    background: #1a1a2e; color: #CCFF00; font-size: 2.2rem; font-weight: 900;
    text-align: center; border-radius: 12px; padding: 10px 0; line-height: 1;
}
.team-name-badge {
    background: #f1f3f5; color: #495057; font-weight: 800; font-size: 0.95rem;
    padding: 8px 12px; border-radius: 10px; margin-bottom: 8px; text-align: center;
}
.status-draft { background: #fff4e6; color: #d9480f; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; }
.status-confirmed { background: #e7f5ff; color: #1971c2; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; }
.rules-box {
    background: rgba(204, 255, 0, 0.05); border: 1px dashed #CCFF00;
    padding: 12px; border-radius: 10px; margin-bottom: 20px; font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

if 'active_view' not in st.session_state: st.session_state.active_view = "대진표"
if 'kdk_all_data' not in st.session_state:
    st.info("먼저 '대진 생성' 페이지에서 대진표를 생성해주세요.")
    st.stop()

data = st.session_state.kdk_all_data
s_id = data.get("session_id")
matches = data.get("matches", [])

# ── 상단 정보 ──
if s_id:
    curr_s = get_kdk_session(s_id)
    status = curr_s.get("status", "draft") if curr_s else "draft"
    title = curr_s.get("title") or data.get("title") or "현재 대진표"
else:
    status = "draft"
    title = data.get("title") or "현재 대진표 (미저장)"

status_tag = '<span class="status-draft">임시 저장</span>' if status == "draft" else '<span class="status-confirmed">확정</span>'
st.markdown(f"## 📝 {title} {status_tag}", unsafe_allow_html=True)

rules = data.get("match_rules", "설정된 규칙이 없습니다.")
st.markdown(f'<div class="rules-box"><b>📏 경기 규칙:</b> {rules}</div>', unsafe_allow_html=True)

if status == "draft" and s_id:
    if st.button("✅ 현재 대진표 최종 확정하기", use_container_width=True, type="primary"):
        update_kdk_session_status(s_id, "confirmed")
        st.success("🎉 대진표가 최종 확정되었습니다!"); st.rerun()

# ── 뷰 전환 ──
view_tabs = st.tabs(["📊 대진표", "🔢 점수 입력", "🏆 순위"])

# 1. 대진표 뷰
with view_tabs[0]:
    for m in matches:
        idx = matches.index(m)
        score_text = f"{m['score1']} : {m['score2']}" if m["status"] == "complete" else "VS"
        st.markdown(f"""
        <div class="match-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1; text-align:left; font-weight:800;">{' & '.join(m['team1'])}</div>
                <div style="flex:0.5; text-align:center; font-weight:900; font-size:1.2rem;">{score_text}</div>
                <div style="flex:1; text-align:right; font-weight:800;">{' & '.join(m['team2'])}</div>
            </div>
            <div style="font-size:0.7rem; color:#888; text-align:center; margin-top:5px;">코트 {m['court']} | 라운드 {m['round']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"점수 입력 (코트 {m['court']}/R{m['round']})", key=f"btn_{idx}", use_container_width=True):
            st.session_state.editing_match_idx = idx
            st.rerun()

# 2. 점수 입력 뷰
with view_tabs[1]:
    if 'editing_match_idx' not in st.session_state:
        st.info("대진표에서 '점수 입력' 버튼을 눌러주세요.")
    else:
        idx = st.session_state.editing_match_idx
        m = matches[idx]
        st.markdown(f"### 🔢 경기 결과 입력 (코트 {m['court']})")
        
        if 's1_val' not in st.session_state or st.session_state.get('last_idx') != idx:
            st.session_state.s1_val = m['score1']
            st.session_state.s2_val = m['score2']
            st.session_state.last_idx = idx

        def change_s(side, delta):
            if side == 1: st.session_state.s1_val = max(0, st.session_state.s1_val + delta)
            else: st.session_state.s2_val = max(0, st.session_state.s2_val + delta)

        # 팀 1 스텝퍼
        st.markdown(f'<div class="team-name-badge">{" & ".join(m["team1"])}</div>', unsafe_allow_html=True)
        st.markdown('<div class="score-stepper-row">', unsafe_allow_html=True)
        c1, s1, c3 = st.columns([1, 1.5, 1])
        with c1: st.button("➖", key="s1m", on_click=change_s, args=(1,-1), use_container_width=True)
        with s1: st.markdown(f'<div class="score-display">{st.session_state.s1_val}</div>', unsafe_allow_html=True)
        with c3: st.button("➕", key="s1p", on_click=change_s, args=(1, 1), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="text-align:center; margin:20px 0; font-weight:900;">VS</div>', unsafe_allow_html=True)

        # 팀 2 스텝퍼
        st.markdown(f'<div class="team-name-badge">{" & ".join(m["team2"])}</div>', unsafe_allow_html=True)
        st.markdown('<div class="score-stepper-row">', unsafe_allow_html=True)
        c1, s1, c3 = st.columns([1, 1.5, 1])
        with c1: st.button("➖", key="s2m", on_click=change_s, args=(2,-1), use_container_width=True)
        with s1: st.markdown(f'<div class="score-display">{st.session_state.s2_val}</div>', unsafe_allow_html=True)
        with c3: st.button("➕", key="s2p", on_click=change_s, args=(2, 1), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("💾 점수 저장 및 복귀", type="primary", use_container_width=True):
            m['score1'], m['score2'], m['status'] = st.session_state.s1_val, st.session_state.s2_val, "complete"
            if m.get('id'): update_kdk_match_score(m['id'], m['score1'], m['score2'], "complete")
            st.success("저장 완료!"); del st.session_state.editing_match_idx; st.rerun()

# 3. 순위 (간소화)
with view_tabs[2]:
    st.write("순위 계산 로직은 03_경기결과.py 에서 확인 가능합니다.")
