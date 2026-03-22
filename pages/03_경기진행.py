import streamlit as st
from datetime import datetime, timedelta
from core_logic.kdk_engine import get_rankings_v3, calculate_rewards_v2
import pandas as pd

from db.supabase_client import check_auth_and_log

st.set_page_config(page_title="경기 진행 | TEYEON", page_icon="🎾", layout="wide")

# ── 권한 체크 및 로그 기록 ────────────────────────────────────────────────────────
check_auth_and_log("03_경기진행.py")

# ── 세션 상태 초기화 ───────────────────────────────────────────────────────────
if "active_view" not in st.session_state:
    st.session_state.active_view = "대진표"
if "editing_match_idx" not in st.session_state:
    st.session_state.editing_match_idx = None

# ── CSS 스타일 ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── UI/UX Pro Max 디자인 ── */
.match-card {
    background: #ffffff;
    color: #1a1a2e;
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    border-left: 8px solid #CCFF00;
    transition: transform 0.2s ease;
}
.match-card:active { transform: scale(0.98); }

.match-card-header {
    display: flex; justify-content: space-between;
    font-size: 0.75rem; color: #777; font-weight: 600; margin-bottom: 10px;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.match-card-body {
    display: flex; align-items: center; justify-content: space-between;
}
.match-teams { font-weight: 800; font-size: 1.1rem; flex: 1; }
.match-score-area { display: flex; align-items: center; gap: 15px; }
.match-score { font-size: 1.6rem; font-weight: 900; color: #0A0E1A; }
.match-time { color: #ff4b4b; font-weight: 700; font-size: 0.9rem; min-width: 45px; text-align: right; }

/* Stepper UI - Horizontal Layout */
.stepper-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    background: rgba(255, 255, 255, 0.05);
    padding: 15px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.score-display { 
    font-size: 3.5rem; font-weight: 900; line-height: 1; margin: 0; 
    color: #CCFF00;
    text-shadow: 0 0 15px rgba(204, 255, 0, 0.3);
    min-width: 80px;
    text-align: center;
}
.team-name-badge { 
    background: rgba(204, 255, 0, 0.1); padding: 10px 20px; border-radius: 12px;
    font-size: 1.1rem; color: #fff; text-align: center; font-weight: 800;
    margin-bottom: 15px;
    border: 1px solid rgba(204, 255, 0, 0.2);
}
</style>
""", unsafe_allow_html=True)

if "kdk_all_data" not in st.session_state:
    st.warning("먼저 '대진 생성' 페이지에서 대진표를 생성해주세요.")
    st.stop()

d = st.session_state.kdk_all_data
matches = d["matches"]
players = d["players"]
groups = d["groups"]
start_time_str = d.get("start_time", "19:30")
duration = d.get("duration", 30)

def get_time_slot(rd):
    st_dt = datetime.strptime(start_time_str, "%H:%M")
    s = st_dt + timedelta(minutes=(rd-1)*duration)
    return s.strftime('%H:%M')

# ── 상단 네비게이션 ────────────────────────────────────────────────────────────
nav_cols = st.columns([1, 1, 1])
if nav_cols[0].button("🎾 정밀 대진표", use_container_width=True, type="primary" if st.session_state.active_view == "대진표" else "secondary"):
    st.session_state.active_view = "대진표"
    st.rerun()
if nav_cols[1].button("🏆 실시간 순위", use_container_width=True, type="primary" if st.session_state.active_view == "순위" else "secondary"):
    st.session_state.active_view = "순위"
    st.rerun()
if st.session_state.editing_match_idx is not None:
    if nav_cols[2].button("✏️ 점수 입력", use_container_width=True, type="primary" if st.session_state.active_view == "입력" else "secondary"):
        st.session_state.active_view = "입력"
        st.rerun()

st.divider()

# ── VIEW: 대진표 (Card UI) ──────────────────────────────────────────────────
if st.session_state.active_view == "대진표":
    # A조, B조를 가로로 배치 (A는 왼쪽, B는 오른쪽 고정)
    col_a, col_b = st.columns(2)
    
    # 조별 맵핑
    group_cols = {"A": col_a, "B": col_b}
    
    # 만약 A, B 외의 다른 조가 있다면? (확장성 대비)
    for g in groups:
        target_col = group_cols.get(g, st.container())
        with target_col:
            # 헤더: 중앙 정렬 & 가로 한 줄 최적화
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 25px; line-height: 1.2;">
                <div style="font-size: 1.5rem; font-weight: 900; color: white;">🎾 {g}조 경기 현황</div>
                <div style="font-size: 0.7rem; color: #aab8d4; font-weight: 500; letter-spacing: -0.2px;">
                    (모든 게임 1:1 시작, 노에드, 5:5 타이 7포인트 선승...)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            g_ms = [m for m in matches if m["group"] == g]
            g_ms.sort(key=lambda x: (x["round"], x["court"]))
            
            for m in g_ms:
                idx = matches.index(m)
                p_round = f"/ {m['pair_round']}" if m.get('pair_round') else ""
                # 가독성을 위해 흰색 카드에서는 진한 네이비 사용, 점수 사이 여백(띄어쓰기) 강조
                res_display = f"{m['score1']} &nbsp; : &nbsp; {m['score2']}" if m["status"] == "complete" else "VS"
                score_color = "#0A0E1A" if m["status"] == "complete" else "#adb5bd"
                
                # 한줄로 길게 가로 레이아웃 (3칼럼: 팀1 | 점수 | 팀2)
                st.markdown(f"""
                <div class="match-card">
                    <div class="match-card-header" style="font-size: 0.7rem; margin-bottom: 8px; color: #888;">
                        <div>코트 {m['court']} | {m['round']} {p_round}</div>
                    </div>
                    <div class="match-card-body" style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                        <div style="flex: 1.4; font-weight: 800; font-size: 1.05rem; line-height: 1.1; text-align: left; overflow-wrap: break-word; color: #1a1a2e; padding-right: 5px;">
                            {' & '.join(m['team1'])}
                        </div>
                        <div style="flex: 0.6; text-align: center; font-weight: 900; font-size: 1.5rem; color: {score_color}; letter-spacing: -1.5px; min-width: 75px; white-space: nowrap;">
                            {res_display}
                        </div>
                        <div style="flex: 1.4; font-weight: 800; font-size: 1.05rem; line-height: 1.1; text-align: right; overflow-wrap: break-word; color: #1a1a2e; padding-left: 5px;">
                            {' & '.join(m['team2'])}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 투명 버튼을 카드 뒤에 배치하여 클릭 가능하게 함
                if st.button(f"점수 입력 / 수정 (코트 {m['court']} - {idx})", key=f"edit_card_{idx}", use_container_width=True):
                    st.session_state.editing_match_idx = idx
                    st.session_state.active_view = "입력"
                    st.rerun()
                st.write("") # 간격
            st.divider()

    # ── 카톡 공유 ──────────────────
    st.markdown("### 💬 카톡 공유용 텍스트")
    share_text = f"🎾 테연 대진표 ({datetime.now().strftime('%m/%d')})\n"
    for r in sorted(list(set(m["round"] for m in matches))):
        share_text += f"\n[{get_time_slot(r)}]\n"
        for m in [m for m in matches if m["round"] == r]:
            status = f" ({m['score1']}:{m['score2']})" if m["status"]=="complete" else ""
            share_text += f"{m['court']}코트: [{' & '.join(m['team1'])}] vs [{' & '.join(m['team2'])}]{status}\n"
    st.info("결과 화면을 캡처하거나 아래 텍스트를 복사하세요.")
    st.code(share_text)

# ── VIEW: 점수 입력 (Horizontal Stepper) ───────────────────────────────────────────────
elif st.session_state.active_view == "입력" and st.session_state.editing_match_idx is not None:
    idx = st.session_state.editing_match_idx
    m = matches[idx]
    
    st.markdown(f"<h2 style='text-align:center;'>✏️ 경기 결과 입력</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; color:#adb5bd; margin-bottom:20px;'>{m['round']} {m['court']}코트</div>", unsafe_allow_html=True)
    
    if "s1_val" not in st.session_state or st.session_state.get("last_idx") != idx:
        st.session_state.s1_val = m["score1"] if m["status"] == "complete" else 0
        st.session_state.s2_val = m["score2"] if m["status"] == "complete" else 0
        st.session_state.last_idx = idx

    def change_score(side, delta):
        if side == 1: 
            st.session_state.s1_val = max(0, min(10, st.session_state.s1_val + delta))
        else:
            st.session_state.s2_val = max(0, min(10, st.session_state.s2_val + delta))

    # 팀 1 가로 한 줄 Stepper: [-] Score [+]
    st.markdown(f'<div class="team-name-badge">{" & ".join(m["team1"])}</div>', unsafe_allow_html=True)
    c1, s1, c3 = st.columns([1, 1.5, 1])
    with c1: st.button("➖", key="s1_m", on_click=change_score, args=(1, -1), use_container_width=True)
    with s1: st.markdown(f'<div class="score-display">{st.session_state.s1_val}</div>', unsafe_allow_html=True)
    with c3: st.button("➕", key="s1_p", on_click=change_score, args=(1, 1), use_container_width=True)

    st.markdown('<div style="text-align:center; margin: 30px 0; color:#555; font-weight:900; font-size:1.5rem; letter-spacing:5px;">V S</div>', unsafe_allow_html=True)

    # 팀 2 가로 한 줄 Stepper: [-] Score [+]
    st.markdown(f'<div class="team-name-badge">{" & ".join(m["team2"])}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: st.button("➖ ", key="s2_minus", on_click=change_score, args=(2, -1), use_container_width=True)
    with c2: st.markdown(f'<div class="score-display">{st.session_state.s2_val}</div>', unsafe_allow_html=True)
    with c3: st.button("➕ ", key="s2_plus", on_click=change_score, args=(2, 1), use_container_width=True)

    st.write("")
    if st.button("✅ 결과 저장 및 복귀", type="primary", use_container_width=True):
        m["score1"] = st.session_state.s1_val
        m["score2"] = st.session_state.s2_val
        m["status"] = "complete"
        
        # --- DB 업데이트 로직 추가 ---
        match_id = m.get("id") # DB의 UUID
        if match_id:
            from db.supabase_client import update_kdk_match_score
            try:
                update_kdk_match_score(match_id, m["score1"], m["score2"], "complete")
                st.toast("💾 DB에 점수가 저장되었습니다!")
            except Exception as e:
                st.error(f"❌ DB 저장 오류: {e}")
        
        st.session_state.editing_match_idx = None
        st.session_state.active_view = "대진표"
        st.success("점수가 성공적으로 저장되었습니다!")
        st.rerun()
    
    if st.button("❌ 취소", use_container_width=True):
        st.session_state.editing_match_idx = None
        st.session_state.active_view = "대진표"
        st.rerun()

# ── VIEW: 순위 ──────────────────────────────────────────────────────────────
elif st.session_state.active_view == "순위":
    overall_rank, group_rank_dict = get_rankings_v3(matches, players)
    fines, rewards = calculate_rewards_v2(overall_rank)
    
    st.markdown("### 🌍 전체 통합 순위 및 정산")
    combined_df_data = []
    for r in overall_rank:
        name = r["이름"]
        amt = rewards.get(name, 0) - fines.get(name, 0)
        note = ""
        if name in rewards: note = f"👑 1등 상금 (+{rewards[name]:,})"
        elif name in fines: note = f"❗ 벌금 대상 (-{fines[name]:,})"
        combined_df_data.append({
            "순위": r["순위"], "이름": name, "승": r["승"], "패": r["패"], 
            "득실차": r["득실차"], "경기수": r["경기수"], "정산액": f"{amt:,}원", "비고": note
        })
    st.dataframe(pd.DataFrame(combined_df_data), use_container_width=True, hide_index=True)

    for g in groups:
        st.markdown(f"### 📍 {g}조 실시간 순위")
        if g in group_rank_dict:
            results_g = group_rank_dict[g]
            st.dataframe(pd.DataFrame(results_g)[["순위", "이름", "승", "패", "득실차", "경기수"]], use_container_width=True, hide_index=True)
            
    total_penalty = sum(fines.values())
    st.markdown(f"""<div style="background: rgba(255, 75, 75, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; text-align: center; margin-top: 10px;">
        <span style="font-size: 1.2rem; font-weight: bold; color: #ff4b4b;">오늘 총 예상 벌금 합계:</span>
        <span style="font-size: 1.8rem; font-weight: 900; color: #ff4b4b; margin-left: 10px;">{total_penalty:,}원</span>
    </div>""", unsafe_allow_html=True)
