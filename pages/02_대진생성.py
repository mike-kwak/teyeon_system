import streamlit as st
from db.supabase_client import get_all_members, check_auth_and_log, get_kdk_sessions, delete_kdk_session
import os
from core_logic.kdk_engine import generate_kdk_matches_v3
from datetime import datetime, time, timedelta

st.set_page_config(page_title="대진 생성 | TEYEON", page_icon="⚙️", layout="wide")

# ── 권한 체크 및 로그 기록 & 사이드바 ──
check_auth_and_log("02_대진생성.py")

st.markdown('''
<style>
/* 모바일 환경에서 st.columns가 1열로 챌기는 것 절대 방어 */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 32% !important;
        flex: 1 1 32% !important;
        min-width: 32% !important;
        padding: 0 2px !important;
    }
}

/* 체크박스를 네온그린 3열 버튼으로 위장 */
div[data-testid="stCheckbox"] input[type="checkbox"] { display: none !important; }
div[data-testid="stCheckbox"] div[data-baseweb="checkbox"] > div { display: none !important; }
div[data-testid="stCheckbox"] label {
    background-color: #1E1E2E !important;
    border: 1px solid #4a4a6a !important;
    border-radius: 8px !important;
    padding: 10px 0px !important;
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    cursor: pointer !important;
    min-height: 42px !important;
    align-items: center !important;
}
div[data-testid="stCheckbox"] label p { color: white !important; font-size: 14px !important; margin: 0 !important; }
div[data-testid="stCheckbox"] label[data-checked="true"] {
    background-color: #39FF14 !important;
    border-color: #39FF14 !important;
}
div[data-testid="stCheckbox"] label[data-checked="true"] p { color: black !important; font-weight: bold !important; }
div[data-testid="stCheckbox"] label:has(input:checked) { background-color: #39FF14 !important; border-color: #39FF14 !important; }
div[data-testid="stCheckbox"] label:has(input:checked) p { color: black !important; font-weight: bold !important; }
.section-card { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px; }
</style>
''', unsafe_allow_html=True)
div[data-testid="stCheckbox"] input[type="checkbox"] { display: none !important; }
div[data-testid="stCheckbox"] div[data-baseweb="checkbox"] > div { display: none !important; }
div[data-testid="stCheckbox"] label {
    background-color: #1E1E2E !important;
    border: 1px solid #4a4a6a !important;
    border-radius: 8px !important;
    padding: 10px 0px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    cursor: pointer !important;
    min-height: 42px !important;
}
div[data-testid="stCheckbox"] label p { color: white !important; font-size: 13px !important; margin: 0 !important; font-weight: 700 !important; }
div[data-testid="stCheckbox"] label[data-checked="true"] {
    background-color: #39FF14 !important;
    border-color: #39FF14 !important;
    box-shadow: 0 0 8px rgba(57,255,20,0.4) !important;
}
div[data-testid="stCheckbox"] label[data-checked="true"] p { color: black !important; font-weight: 900 !important; }
div[data-testid="stCheckbox"] label:has(input:checked) { background-color: #39FF14 !important; border-color: #39FF14 !important; }
div[data-testid="stCheckbox"] label:has(input:checked) p { color: black !important; font-weight: 900 !important; }
.section-card { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px; }
</style>
''', unsafe_allow_html=True)

CLUB_ID = os.environ.get("CLUB_ID", "")

# ── 초기화 ──
if 'selected_members' not in st.session_state: st.session_state.selected_members = []
if 'guests' not in st.session_state: st.session_state.guests = []
if 'player_groups' not in st.session_state: st.session_state.player_groups = {}
if 'player_times' not in st.session_state: st.session_state.player_times = {}
if 'global_start' not in st.session_state: st.session_state.global_start = "19:00"
if 'global_end' not in st.session_state: st.session_state.global_end = "22:00"
if 'fixed_partners' not in st.session_state: st.session_state.fixed_partners = []
if 'fixed_partner_games' not in st.session_state: st.session_state.fixed_partner_games = 1
if 'use_group_division' not in st.session_state: st.session_state.use_group_division = False
if 'reward_1st' not in st.session_state: st.session_state.reward_1st = 10000
if 'fine_25' not in st.session_state: st.session_state.fine_25 = 3000
if 'fine_last_25' not in st.session_state: st.session_state.fine_last_25 = 5000
if 'default_score' not in st.session_state: st.session_state.default_score = 1
if 'account_number' not in st.session_state: st.session_state.account_number = "카카오뱅크 곽민섭 3333-01-5235337"

members = get_all_members(CLUB_ID)
members.sort(key=lambda x: x.get("nickname", ""))
time_opts = [(datetime.combine(datetime.today(), time(18, 0)) + timedelta(minutes=30*i)).strftime("%H:%M") for i in range(13)]

st.markdown("## ⚙️ KDK 대진 설정 및 생성")

col_left, col_right = st.columns([3.2, 2])

with col_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🕙 오늘의 운영 시간 (일괄 적용)")
    g_tc1, g_tc2, g_tc3 = st.columns([2, 2, 1.2])
    with g_tc1: new_g_start = st.selectbox("글로벌 시작", time_opts, index=time_opts.index(st.session_state.global_start), key="global_start_sel")
    with g_tc2: new_g_end = st.selectbox("글로벌 종료", time_opts, index=time_opts.index(st.session_state.global_end), key="global_end_sel")
    with g_tc3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("전체 적용", use_container_width=True):
            st.session_state.global_start, st.session_state.global_end = new_g_start, new_g_end
            for m_id in st.session_state.selected_members:
                name = next((m.get("nickname") for m in members if m.get("id") == m_id), None)
                if name: st.session_state.player_times[name] = [new_g_start, new_g_end]
            for g in st.session_state.guests: st.session_state.player_times[g] = [new_g_start, new_g_end]
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    search = st.text_input("🔍 이름 검색", placeholder="이름 입력...", label_visibility="collapsed")
    filtered = [m for m in members if search.lower() in m.get("nickname", "").lower()] if search else members

    # v23.0: st.columns(3) + 모바일 Flex 방어막으로 완벽 3열
    cols = st.columns(3)
    for i, m in enumerate(filtered):
        m_id = m.get("id")
        m_name = m.get("nickname", "이름없음")
        is_pre_selected = m_id in st.session_state.selected_members
        with cols[i % 3]:
            st.checkbox(m_name, key=f"att_{m_id}", value=is_pre_selected, label_visibility="visible")

    # 선택된 인원 집계
    current_selected = []
    for m in members:
        m_id = m.get("id")
        if st.session_state.get(f"att_{m_id}"):
            current_selected.append(m_id)
            m_name = m.get("nickname", "이름없음")
            if m_name not in st.session_state.player_times:
                st.session_state.player_times[m_name] = [st.session_state.get('global_start','19:00'), st.session_state.get('global_end','22:00')]
            if m_name not in st.session_state.player_groups:
                st.session_state.player_groups[m_name] = "A"
    st.session_state.selected_members = current_selected

    if st.button("🔄 전체 초기화", use_container_width=True, key="reset_btn_v23"):
        for m in members: st.session_state[f"att_{m.get('id')}"] = False
        st.session_state.selected_members = []
        st.session_state.player_times = {}
        st.session_state.player_groups = {}
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True) # section-card 닫기

with col_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 👤 게스트 추가")
    g_col1, g_col2 = st.columns([3, 1])
    with g_col1: new_guest = st.text_input("G_IN", label_visibility="collapsed", placeholder="게스트 이름")
    with g_col2: 
        if st.button("➕"):
            if new_guest and new_guest not in st.session_state.guests:
                st.session_state.guests.append(new_guest); st.rerun()
    for g in st.session_state.guests:
        p_c1, p_c2 = st.columns([4, 1])
        with p_c1: st.write(f"🟡 {g} (게스트)")
        with p_c2:
            if st.button("🗑️", key=f"del_{g}"):
                st.session_state.guests.remove(g); st.session_state.player_times.pop(g, None); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🤝 고정 파트너 설정")
    st.session_state.fixed_partner_games = st.number_input("함께 뛸 게임 수", min_value=1, max_value=10, value=st.session_state.fixed_partner_games)
    all_selected_names = [next((m["nickname"] for m in members if m["id"] == i), "") for i in st.session_state.selected_members] + st.session_state.guests
    if len(all_selected_names) >= 2:
        pc1, pc2, pc3 = st.columns([2, 2, 1])
        with pc1: p1 = st.selectbox("선수 1", all_selected_names, key="p1_sel")
        with pc2: p2 = st.selectbox("선수 2", [n for n in all_selected_names if n != p1], key="p2_sel")
        with pc3:
            if st.button("고정"):
                if [p1, p2, st.session_state.fixed_partner_games] not in st.session_state.fixed_partners:
                    st.session_state.fixed_partners.append([p1, p2, st.session_state.fixed_partner_games]); st.rerun()
    for idx, pair in enumerate(st.session_state.fixed_partners):
        p_col1, p_col2 = st.columns([4, 1])
        with p_col1: st.write(f"🔗 {pair[0]} ❤️ {pair[1]} ({pair[2]}게임)")
        with p_col2:
            if st.button("🗑️", key=f"del_fixed_{idx}"): st.session_state.fixed_partners.pop(idx); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    tab_time, tab_group = st.tabs(["⏰ 시간 조정", "🔄 조 나누기"])
    with tab_time:
        exc_names = st.multiselect("대상 선택", all_selected_names)
        exc_c1, exc_c2, exc_c3 = st.columns([2, 2, 1])
        with exc_c1: e_s = st.selectbox("시작", time_opts, index=time_opts.index(st.session_state.global_start), key="e_s")
        with exc_c2: e_e = st.selectbox("종료", time_opts, index=time_opts.index(st.session_state.global_end), key="e_e")
        with exc_c3:
            if st.button("반영"):
                for n in exc_names: st.session_state.player_times[n] = [e_s, e_e]
                st.rerun()
    with tab_group:
        if st.session_state.use_group_division:
            target_n = st.multiselect("대상 선택", all_selected_names, key="grp_n")
            target_g = st.radio("조 선택", ["A", "B"], horizontal=True)
            if st.button("확정"):
                for n in target_n: st.session_state.player_groups[n] = target_g
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card concept-area">', unsafe_allow_html=True)
    st.markdown("### 🎾 최종 설정")
    c1, c2 = st.columns(2)
    with c1: concept = st.selectbox("컨셉", ["기본(랜덤)", "YB vs OB", "MBTI", "입상자 vs 비입상자"])
    with c2: match_dur = st.number_input("경기 시간(분)", 10, 120, 30)
    c3, c4 = st.columns(2)
    with c3: start_t = st.time_input("시작 시간", time(19, 0))
    with c4: target_matches = st.number_input("목표 경기 수", 1, 10, 4)
    c5, c6 = st.columns(2)
    with c5: a_c = st.number_input("A조 코트", 1, 10, 2)
    with c6: b_c = st.number_input("B조 코트", 0, 10, 0)
    st.markdown("---")
    session_title = st.text_input("📝 대진표 제목", value=f"대진표_{datetime.now().strftime('%m%d_%H%M')}")
    match_rules = st.text_input("📜 경기 규칙", value="(모든 게임 1:1 시작, 노에드, 5:5 타이 7포인트 선승...)")
    
    st.session_state.default_score = st.number_input("기본 시작 점수", min_value=0, max_value=5, value=st.session_state.default_score)

    st.markdown("### 💰 상벌금")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: st.session_state.reward_1st = st.number_input("1등", value=st.session_state.reward_1st, step=1000)
    with sc2: st.session_state.fine_25 = st.number_input("하위 25%", value=st.session_state.fine_25, step=1000)
    with sc3: st.session_state.fine_last_25 = st.number_input("최하위 25%", value=st.session_state.fine_last_25, step=1000)
    
    st.session_state.account_number = st.text_input("벌금 입금 계좌", value=st.session_state.account_number)
    
    if st.button("🚀 KDK 대진 자동 생성", use_container_width=True):
        if len(all_selected_names) < 4: st.error("최소 4명 이상 선택해주세요.")
        else:
            from db.supabase_client import create_kdk_session, upsert_kdk_matches
            court_map = {'A': list(range(1, a_c+1)), 'B': list(range(a_c+1, a_c+b_c+1))}
            players = []
            for n in all_selected_names:
                m_info = next((m for m in members if m["nickname"] == n), {})
                players.append({"name": n, "group": st.session_state.player_groups.get(n, "A"), "times": st.session_state.player_times.get(n, [st.session_state.global_start, st.session_state.global_end]), "is_guest": n in st.session_state.guests})
            matches = generate_kdk_matches_v3(players, court_map, target_matches, concept=concept, fixed_partners=st.session_state.fixed_partners, fixed_partner_games=st.session_state.fixed_partner_games)
            
            # 기본 점수 일괄 적용
            for m in matches:
                m['score1'] = st.session_state.default_score
                m['score2'] = st.session_state.default_score
                
            award_config = {"reward_1st": st.session_state.reward_1st, "fine_25": st.session_state.fine_25, "fine_last_25": st.session_state.fine_last_25, "account_number": st.session_state.account_number}
            c_id = CLUB_ID if CLUB_ID else None
            creator_id = st.session_state.get("user", {}).get("id")
            new_session = create_kdk_session(c_id, datetime.now().strftime("%Y-%m-%d"), creator_id, note=f"{concept} | {session_title}", award_config=award_config, title=session_title)
            if new_session:
                db_matches = [{"session_id": new_session["id"], "group": m["group"], "round": m["round"], "court": m["court"], "team1": m["team1"], "team2": m["team2"], "score1": m["score1"], "score2": m["score2"], "status": "pending"} for m in matches]
                upsert_kdk_matches(db_matches)
                st.session_state.kdk_all_data = {"session_id": new_session["id"], "players": players, "matches": matches, "match_rules": match_rules, "title": session_title}
                st.session_state.match_created_msg = "🚀 대진표 생성 및 저장 완료!"
                st.rerun()

if st.session_state.get('match_created_msg'):
    st.success(st.session_state.match_created_msg); st.toast(st.session_state.match_created_msg); st.balloons(); del st.session_state.match_created_msg

st.markdown("### 📦 과거 대진표 아카이브")
try:
    recent = get_kdk_sessions(CLUB_ID, limit=10)
    for s in recent:
        s_title = s.get("title") or f"대진표 ({s.get('session_date')})"
        arc_c1, arc_c2, arc_c3 = st.columns([4, 1, 1])
        with arc_c1: st.write(f"📅 {s_title} [{s.get('status','draft')}]")
        with arc_c2:
            if st.button("불러오기", key=f"l_{s['id']}"):
                from db.supabase_client import get_kdk_session
                full_s = get_kdk_session(s["id"])
                if full_s:
                    st.session_state.kdk_all_data = {"session_id": full_s["id"], "matches": full_s.get("kdk_matches", []), "match_rules": full_s.get("match_rules", ""), "title": s_title}
                    st.success(f"✅ {s_title} 로드 완료!"); st.rerun()
        with arc_c3:
            if st.button("삭제", key=f"d_{s['id']}"):
                delete_kdk_session(s["id"]); st.toast("삭제 완료!"); st.rerun()
except Exception as e: st.error(f"아카이브 로드 실패: {e}")
st.markdown('</div>', unsafe_allow_html=True)
