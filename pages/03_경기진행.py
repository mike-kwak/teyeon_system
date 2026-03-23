import streamlit as st
import os
from datetime import datetime
import pandas as pd
from db.supabase_client import get_kdk_session, update_kdk_session_status, update_kdk_match_score, check_auth_and_log, get_all_members
from core_logic.kdk_engine import get_rankings_v3, calculate_rewards_v2

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
    background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-bottom: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ffffff;
}
.score-display {
    background: #1a1a2e; color: #CCFF00; font-size: 2.2rem; font-weight: 900;
    text-align: center; border-radius: 12px; padding: 10px 0; line-height: 1;
}
.team-name-badge {
    background: #f1f3f5; color: #495057; font-weight: 800; font-size: 0.95rem;
    padding: 8px 12px; border-radius: 10px; margin-bottom: 8px; text-align: center;
}
.status-draft { background: rgba(255, 244, 230, 0.1); color: #ffa94d; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; border: 1px solid #ffa94d; }
.status-confirmed { background: rgba(231, 245, 255, 0.1); color: #74c0fc; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; border: 1px solid #74c0fc; }
.rules-box {
    background: rgba(204, 255, 0, 0.05); border: 1px dashed #CCFF00;
    padding: 12px; border-radius: 10px; margin-bottom: 20px; font-size: 0.9rem; color: #ffffff;
}
/* KDK 스코어 카드 스타일링 */
div[data-testid="column"]:has(.team-card-wrapper) {
    background: linear-gradient(135deg, rgba(26,37,61,0.9), rgba(10,14,26,0.95)) !important;
    border: 1px solid rgba(204,255,0,0.3) !important;
    border-radius: 24px !important;
    padding: 20px 10px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
}
.kdk-score-name {
    font-size: 1.05rem; font-weight: 800; color: #fff; line-height: 1.4;
    text-align: center; margin-bottom: 15px; min-height: 2.8em;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column;
}
.kdk-score-number {
    font-size: 5.5rem; font-weight: 900; color: #CCFF00; line-height: 1;
    text-align: center; font-family: 'Outfit', sans-serif;
    text-shadow: 0 0 30px rgba(204,255,0,0.6); margin-bottom: 20px;
}
.kdk-score-number-bg {
    background: rgba(0,0,0,0.3); border-radius: 20px; padding: 15px 0;
    margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.05);
}
.kdk-vs-text {
    font-size: 1.8rem; font-weight: 900; color: #aab8d4;
    font-style: italic; opacity: 0.6; text-align: center;
    margin-top: 50%;
}
/* +/- 버튼 약간 크게 */
div[data-testid="column"]:has(.team-card-wrapper) div.stButton > button {
    border-radius: 14px !important;
    font-size: 1.5rem !important;
    padding: 10px 0 !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    transition: all 0.2s;
}
div[data-testid="column"]:has(.team-card-wrapper) div.stButton > button:active {
    background: rgba(204,255,0,0.2) !important;
    border-color: #CCFF00 !important;
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

rules = data.get("match_rules") or "(모든 게임 1:1 시작, 노에드, 5:5 타이 7포인트 선승...)"
st.markdown(f'<div class="rules-box"><b>📏 경기 규칙:</b> {rules}</div>', unsafe_allow_html=True)

if status == "draft" and s_id:
    if st.button("✅ 현재 대진표 최종 확정하기", use_container_width=True, type="primary"):
        update_kdk_session_status(s_id, "in_progress")
        st.toast("🎉 대진표가 최종 확정되었습니다!")
        st.rerun()

# ── 뷰 전환: 점수 입력 모드 vs 리스트 모드 ──
main_tabs = st.tabs(["🎾 현재 대진 및 점수", "🏆 실시간 랭킹"])

with main_tabs[0]:
    if 'editing_match_idx' in st.session_state:
        # 점수 입력 모드
        idx = st.session_state.editing_match_idx
        m = matches[idx]
    
        if st.button("← 대진표 목록으로 돌아가기", use_container_width=True):
            del st.session_state.editing_match_idx
            st.rerun()

        st.markdown(f"### 🔢 경기 결과 입력 (코트 {m['court']} / 라운드 {m['round']})")
    
        if 's1_val' not in st.session_state or st.session_state.get('last_idx') != idx:
            st.session_state.s1_val = m['score1']
            st.session_state.s2_val = m['score2']
            st.session_state.last_idx = idx

        def change_s(side, delta):
            if side == 1: st.session_state.s1_val = max(0, st.session_state.s1_val + delta)
            else: st.session_state.s2_val = max(0, st.session_state.s2_val + delta)

        # ── 가로형 점수 카드 레이아웃 ──
        score_col1, vs_col, score_col2 = st.columns([1, 0.2, 1])
    
        with score_col1:
            st.markdown('<div class="team-card-wrapper"></div>', unsafe_allow_html=True)
            # 프로필 아이콘과 이름
            names_html1 = "<br>".join(m["team1"])
            st.markdown(f'''
            <div class="kdk-score-name">
                <div style="font-size:2rem;margin-bottom:5px;">👤</div>
                {names_html1}
            </div>
            <div class="kdk-score-number-bg">
                <div class="kdk-score-number">{st.session_state.s1_val}</div>
            </div>
            ''', unsafe_allow_html=True)
        
            c_p1, c_m1 = st.columns(2)
            with c_p1: st.button("➕", key="s1p", on_click=change_s, args=(1, 1), use_container_width=True)
            with c_m1: st.button("➖", key="s1m", on_click=change_s, args=(1,-1), use_container_width=True)

        with vs_col:
            st.markdown('<div class="kdk-vs-text">VS</div>', unsafe_allow_html=True)

        with score_col2:
            st.markdown('<div class="team-card-wrapper"></div>', unsafe_allow_html=True)
            names_html2 = "<br>".join(m["team2"])
            st.markdown(f'''
            <div class="kdk-score-name">
                <div style="font-size:2rem;margin-bottom:5px;">🔴</div>
                {names_html2}
            </div>
            <div class="kdk-score-number-bg">
                <div class="kdk-score-number">{st.session_state.s2_val}</div>
            </div>
            ''', unsafe_allow_html=True)
        
            c_p2, c_m2 = st.columns(2)
            with c_p2: st.button("➕", key="s2p", on_click=change_s, args=(2, 1), use_container_width=True)
            with c_m2: st.button("➖", key="s2m", on_click=change_s, args=(2,-1), use_container_width=True)
    
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("💾 점수 저장 및 복귀", type="primary", use_container_width=True):
            m['score1'], m['score2'], m['status'] = st.session_state.s1_val, st.session_state.s2_val, "complete"
            if m.get('id'): update_kdk_match_score(m['id'], m['score1'], m['score2'], "complete")
            st.success("저장 완료!")
            del st.session_state.editing_match_idx
            st.rerun()

    else:
        # ── 대진표 리스트 모드 ──
        for m in matches:
            idx = matches.index(m)
            score_text = f"{m['score1']} : {m['score2']}" if m["status"] == "complete" else "VS"
            st.markdown(f"""
            <div class="match-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="flex:1; text-align:left; font-weight:800; font-size:1.1rem;">{' & '.join(m['team1'])}</div>
                    <div style="flex:0.5; text-align:center; font-weight:900; font-size:1.2rem; color:#CCFF00;">{score_text}</div>
                    <div style="flex:1; text-align:right; font-weight:800; font-size:1.1rem;">{' & '.join(m['team2'])}</div>
                </div>
                <div style="font-size:0.8rem; color:#aab8d4; text-align:center; margin-top:8px;">코트 {m['court']} | 라운드 {m['round']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"점수 입력 (코트 {m['court']} / R{m['round']})", key=f"btn_{idx}", use_container_width=True):
                st.session_state.editing_match_idx = idx
                st.rerun()

with main_tabs[1]:
    st.markdown("### 🏆 실시간 랭킹 (진행 중)")
    CLUB_ID = os.environ.get("CLUB_ID", "")
    try:
        all_members = get_all_members(CLUB_ID)
        member_map = {m["nickname"]: m for m in all_members}
        
        player_names = set()
        for m in matches:
            player_names.update(m["team1"])
            player_names.update(m["team2"])
            
        players_info = []
        for name in player_names:
            m_info = member_map.get(name, {})
            players_info.append({
                "name": name,
                "birthdate": m_info.get("birthdate", "1900-01-01"),
                "is_guest": (m_info.get("kakao_id") or 0) < 0 or name.startswith("Guest") or m_info.get("is_guest") == True
            })
            
        overall_rank, _ = get_rankings_v3(matches, players_info)
        
        if overall_rank:
            # 상벌금 실시간 계산 추가
            award_config = {}
            if s_id and 'curr_s' in locals() and curr_s:
                award_config = curr_s.get("award_config", {})
            
            fines, rewards = calculate_rewards_v2(
                overall_rank,
                reward_1st=award_config.get("reward_1st", 10000),
                fine_25=award_config.get("fine_25", 3000),
                fine_last_25=award_config.get("fine_last_25", 5000)
            )
            
            # HTML 테이블로 가운데 정렬 구현
            html_table = f"""
            <style>
                .ranking-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; color: white; text-align: center; }}
                .ranking-table th {{ background: rgba(204, 255, 0, 0.1); color: #CCFF00; padding: 12px; border-bottom: 2px solid rgba(254, 255, 0, 0.2); font-size: 0.9rem; }}
                .ranking-table td {{ padding: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-size: 0.85rem; }}
                .ranking-table tr:nth-child(even) {{ background: rgba(255, 255, 255, 0.02); }}
                .reward-tag {{ color: #CCFF00; font-weight: bold; }}
                .penalty-tag {{ color: #ff4b4b; font-weight: bold; }}
            </style>
            <table class="ranking-table">
                <thead>
                    <tr>
                        <th>순위</th><th>이름</th><th>승</th><th>패</th><th>득실차</th><th>경기수</th><th>정산액</th><th>비고</th>
                    </tr>
                </thead>
                <tbody>
            """
            for r in res_data:
                note_class = "reward-tag" if "상금" in r["비고"] else "penalty-tag" if "벌금" in r["비고"] else ""
                html_table += f"""
                    <tr>
                        <td>{r['순위']}</td><td>{r['이름']}</td><td>{r['승']}</td><td>{r['패']}</td><td>{r['득실차']}</td><td>{r['경기수']}</td>
                        <td>{r['정산액']}</td><td class="{note_class}">{r['비고']}</td>
                    </tr>
                """
            html_table += "</tbody></table>"
            st.markdown(html_table, unsafe_allow_html=True)
            
            # 진행 상태 표시
            completed_matches = sum(1 for m in matches if m["status"] == "complete")
            st.progress(completed_matches / max(len(matches), 1))
            st.caption(f"진행률: {completed_matches} / {len(matches)} 경기 완료")
        else:
            st.info("아직 랭킹 데이터가 없습니다.")
    except Exception as e:
        st.error(f"랭킹 계산 중 오류 발생: {e}")

