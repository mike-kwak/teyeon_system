import streamlit as st
from db.supabase_client import get_all_members, check_auth_and_log
import os
from core_logic.kdk_engine import generate_kdk_matches_v3
from datetime import datetime, time, timedelta

st.set_page_config(page_title="대진 생성 | TEYEON", page_icon="⚙️", layout="wide")

# ── 권한 체크 및 로그 기록 & 사이드바 ──
check_auth_and_log("02_대진생성.py")

st.markdown("""
<style>
/* 멤버 영역의 테두리 컨테이너만 고정 높이 적용 */
.member-area div[data-testid="stVerticalBlockBordered"] {
    padding: 5px 8px !important;
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    min-height: 110px !important;
    max-height: 110px !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
}
/* 멤버 영역 내 선택창 크기 압축 및 강제 축소 (아이콘 제거 포함) */
.member-area div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 22px !important;
    height: 22px !important;
    font-size: 0.8rem !important; /* 글자 크기 다시 확보 */
    padding: 0px 2px !important; /* 극도로 압축 */
}
/* 화살표 아이콘(SVG) 강제 숨기기 */
.member-area div[data-testid="stSelectbox"] svg {
    display: none !important;
}
/* 우측 여백 제거 */
.member-area div[data-testid="stSelectbox"] [data-baseweb="select"] > div:last-child {
    padding-right: 2px !important;
}
.member-area div[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.65rem !important;
}
.section-card { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 12px; }
.attendee-stat { background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); color: #1a202c; padding: 5px 15px; border-radius: 8px; font-weight: 800; display: inline-block; margin-bottom: 10px; font-size: 0.9rem; }
div.stButton > button:first-child { background-color: #FEE500 !important; color: #000000 !important; font-weight: 800 !important; border: none !important; padding: 0.25rem 0.5rem; }
.stCheckbox { margin-bottom: 0px !important; }
.member-area .stSelectbox { margin-top: -10px !important; }
/* 매칭 컨셉 섹션: selectbox 높이를 number_input과 통일 */
.concept-area div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 38px !important;
    height: 38px !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}
h3 { margin-top: 0px !important; margin-bottom: 10px !important; font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)

CLUB_ID = os.environ.get("CLUB_ID", "")

CLUB_ID = os.environ.get("CLUB_ID", "")

# ── 초기화 ──────────────────────────────────────────────────────────────
if 'selected_members' not in st.session_state: st.session_state.selected_members = []
if 'guests' not in st.session_state: st.session_state.guests = []
if 'player_groups' not in st.session_state: st.session_state.player_groups = {}
if 'player_times' not in st.session_state: st.session_state.player_times = {} # {name: [19:00, 22:00]}
if 'global_start' not in st.session_state: st.session_state.global_start = "19:00"
if 'global_end' not in st.session_state: st.session_state.global_end = "22:00"
if 'fixed_partners' not in st.session_state: st.session_state.fixed_partners = [] # [[p1, p2], ...]
if 'fixed_partner_games' not in st.session_state: st.session_state.fixed_partner_games = 1 # 고정 파트너 유지 게임 수
if 'use_group_division' not in st.session_state: st.session_state.use_group_division = False
if 'reward_1st' not in st.session_state: st.session_state.reward_1st = 10000
if 'fine_25' not in st.session_state: st.session_state.fine_25 = 3000
if 'fine_last_25' not in st.session_state: st.session_state.fine_last_25 = 5000

members = get_all_members(CLUB_ID)
members.sort(key=lambda x: x.get("nickname", ""))

# 시간 옵션 생성 (최상단 정의로 NameError 방지)
time_opts = [(datetime.combine(datetime.today(), time(18, 0)) + timedelta(minutes=30*i)).strftime("%H:%M") for i in range(13)]

st.markdown("## ⚙️ KDK 대진 설정 및 생성")

col_left, col_right = st.columns([3.2, 2])

with col_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🕙 오늘의 운영 시간 (일괄 적용)")
    g_tc1, g_tc2, g_tc3 = st.columns([2, 2, 1.2])
    with g_tc1: 
        new_g_start = st.selectbox("글로벌 시작", time_opts, index=time_opts.index(st.session_state.global_start), key="global_start_sel")
    with g_tc2: 
        new_g_end = st.selectbox("글로벌 종료", time_opts, index=time_opts.index(st.session_state.global_end), key="global_end_sel")
    with g_tc3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("전체 적용", use_container_width=True):
            st.session_state.global_start = new_g_start
            st.session_state.global_end = new_g_end
            # 체크된 모든 멤버와 게스트에게 시간 덮어쓰기
            updated_count = 0
            # 멤버
            for m_id in st.session_state.selected_members:
                name = next((m["nickname"] for m in members if m["id"] == m_id), None)
                if name:
                    st.session_state.player_times[name] = [new_g_start, new_g_end]
                    updated_count += 1
            # 게스트
            for g in st.session_state.guests:
                st.session_state.player_times[g] = [new_g_start, new_g_end]
                updated_count += 1
            st.success(f"✅ {updated_count}명에게 일괄 적용되었습니다!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns([2, 1.5, 1])
    with sc1: st.markdown("### 👥 참석자 체크")
    with sc2: st.session_state.use_group_division = st.checkbox("🔄 조 나누기", value=st.session_state.use_group_division)
    with sc3:
        if st.button("🔄 초기화"):
            # 특정 위젯 키들 삭제
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith(('mem_', 'grp_', 'exc_', 'gst_', 'gst_'))]
            for k in keys_to_clear: del st.session_state[k]
            st.session_state.selected_members = []
            st.session_state.guests = []
            st.session_state.player_times = {}
            st.session_state.player_groups = {}
            st.session_state.fixed_partners = []
            st.rerun()

    search = st.text_input("🔍 이름 검색", placeholder="이름 입력...", label_visibility="collapsed")
    filtered = [m for m in members if search.lower() in m.get("nickname", "").lower()] if search else members
    
    # 📜 참석자 명단 (심플 3열 그리드)
    m_cols = st.columns(3)
    for i, m in enumerate(filtered):
        m_id, m_name = m.get("id"), m.get("nickname", "이름없음")
        with m_cols[i % 3]:
            # 조 정보 표시 추가 (예: 가내현 [B])
            display_name = m_name
            if st.session_state.use_group_division:
                grp = st.session_state.player_groups.get(m_name, "A")
                display_name = f"{m_name} [{grp}]"
            
            is_checked = st.checkbox(display_name, value=m_id in st.session_state.selected_members, key=f"mem_{m_id}")
            if is_checked:
                if m_id not in st.session_state.selected_members:
                    st.session_state.selected_members.append(m_id)
                if m_name not in st.session_state.player_times:
                    st.session_state.player_times[m_name] = [st.session_state.global_start, st.session_state.global_end]
                if m_name not in st.session_state.player_groups:
                    st.session_state.player_groups[m_name] = "A"
            else:
                if m_id in st.session_state.selected_members:
                    st.session_state.selected_members.remove(m_id)
                    if m_name in st.session_state.player_times: del st.session_state.player_times[m_name]
                    if m_name in st.session_state.player_groups: del st.session_state.player_groups[m_name]
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # ── 게스트 섹션 ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 👤 게스트 추가")
    g_col1, g_col2 = st.columns([3, 1])
    with g_col1: new_guest = st.text_input("G_IN", label_visibility="collapsed", placeholder="게스트 이름")
    with g_col2: 
        if st.button("➕"):
            if new_guest and new_guest not in st.session_state.guests:
                st.session_state.guests.append(new_guest)
                st.rerun()
    
    for g in st.session_state.guests:
        p_c1, p_c2 = st.columns([4, 1])
        with p_c1: st.write(f"🟡 {g} (게스트)")
        with p_c2:
            if st.button("🗑️", key=f"del_{g}"):
                st.session_state.guests.remove(g)
                if g in st.session_state.player_times: del st.session_state.player_times[g]
                st.rerun()
        # 기본 시간 자동 적용
        if g not in st.session_state.player_times:
            st.session_state.player_times[g] = [st.session_state.global_start, st.session_state.global_end]
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 고정 파트너 섹션 ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🤝 고정 파트너 설정")
    
    # 함께 뛸 게임 수 설정 추가
    st.session_state.fixed_partner_games = st.number_input("함께 뛸 게임 수", min_value=1, max_value=10, value=st.session_state.fixed_partner_games)
    
    all_selected_names = []
    for m_id in st.session_state.selected_members:
        name = next((m["nickname"] for m in members if m["id"] == m_id), None)
        if name: all_selected_names.append(name)
    all_selected_names.extend(st.session_state.guests)
    
    # 이미 고정된 인원은 선택지에서 가급적 제외 (UX 개선)
    fixed_names = set()
    for p in st.session_state.fixed_partners: fixed_names.update(p)
    
    if len(all_selected_names) >= 2:
        pc1, pc2, pc3 = st.columns([2, 2, 1])
        with pc1: p1 = st.selectbox("선수 1", all_selected_names, key="p1_sel")
        with pc2: p2 = st.selectbox("선수 2", [n for n in all_selected_names if n != p1], key="p2_sel")
        with pc3:
            if st.button("고정"):
                if [p1, p2, st.session_state.fixed_partner_games] not in st.session_state.fixed_partners:
                    st.session_state.fixed_partners.append([p1, p2, st.session_state.fixed_partner_games])
                    st.rerun()
    
    # 고정 파트너 목록 표시 및 삭제
    if st.session_state.fixed_partners:
        st.markdown("---")
        for idx, pair_data in enumerate(st.session_state.fixed_partners):
            # [p1, p2, 게임수] 형태 대응
            p1, p2 = pair_data[0], pair_data[1]
            g_count = pair_data[2] if len(pair_data) > 2 else 1
            
            p_col1, p_col2 = st.columns([4, 1])
            with p_col1: st.write(f"🔗 {p1} ❤️ {p2} **({g_count}게임)**")
            with p_col2:
                if st.button("🗑️", key=f"del_fixed_{idx}"):
                    st.session_state.fixed_partners.pop(idx)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── ⏰ 지각/조퇴 및 🔄 조 나누기 조정 (일괄 관리) ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    
    # 공통 데이터 준비
    current_attendees = []
    for m_id in st.session_state.selected_members:
        name = next((m["nickname"] for m in members if m["id"] == m_id), None)
        if name: current_attendees.append(name)
    current_attendees.extend(st.session_state.guests)

    tab_time, tab_group = st.tabs(["⏰ 시간 조정", "🔄 조 나누기 설정"])
    
    with tab_time:
        if current_attendees:
            exc_names = st.multiselect("시간을 변경할 인원 선택", current_attendees, key="exc_names_time")
            exc_c1, exc_c2, exc_c3 = st.columns([2, 2, 1])
            with exc_c1: exc_start = st.selectbox("변경 시작", time_opts, index=time_opts.index(st.session_state.global_start), key="exc_s")
            with exc_c2: exc_end = st.selectbox("변경 종료", time_opts, index=time_opts.index(st.session_state.global_end), key="exc_e")
            with exc_c3:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("반영", key="apply_exc"):
                    for name in exc_names: st.session_state.player_times[name] = [exc_start, exc_end]
                    st.rerun()
        else: st.write("참석자를 먼저 체크해주세요.")
        
    with tab_group:
        if st.session_state.use_group_division:
            if current_attendees:
                grp_names = st.multiselect("조를 변경할 인원 선택", current_attendees, key="grp_names_change")
                grp_c1, grp_c2 = st.columns([3, 1])
                with grp_c1: target_grp = st.radio("변경할 조 선택", ["A", "B"], horizontal=True, key="target_grp_radio")
                with grp_c2:
                    st.markdown("<div style='height:5px;'></div>", unsafe_allow_html=True)
                    if st.button("조 배정 실행", key="apply_grp"):
                        for name in grp_names: st.session_state.player_groups[name] = target_grp
                        st.success(f"✅ {len(grp_names)}명이 {target_grp}조로 배정되었습니다.")
                        st.rerun()
            else: st.write("참석자를 먼저 체크해주세요.")
        else:
            st.info("💡 위쪽 상단의 '🔄 조 나누기' 체크박스를 먼저 활성화해주세요.")
    
    # 조 배정 현황 요약 (실수 방지용)
    if st.session_state.use_group_division and current_attendees:
        b_list = [n for n in current_attendees if st.session_state.player_groups.get(n, "A") == "B"]
        if b_list: st.caption(f"🔵 현재 B조 인원({len(b_list)}명): {', '.join(b_list)}")
        else: st.caption("⚪ 현재 모든 인원이 A조입니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 🎾 매칭 컨셉 및 최종 설정 (복구) ──
    st.markdown('<div class="section-card concept-area">', unsafe_allow_html=True)
    st.markdown("### 🎾 매칭 컨셉 및 최종 설정")
    row1c1, row1c2 = st.columns(2)
    with row1c1:
        concept = st.selectbox("매칭 컨셉", ["기본(랜덤)", "YB vs OB (나이)", "MBTI (E vs I)", "입상자 vs 비입상자"])
    with row1c2:
        match_dur = st.number_input("경기 소요 시간 (분)", 10, 120, 30)

    row2c1, row2c2 = st.columns(2)
    with row2c1:
        start_t = st.time_input("시작 시간", time(19, 0))
    with row2c2:
        target_matches = st.number_input("1인당 목표 경기 수", 1, 10, 4)

    row3c1, row3c2 = st.columns(2)
    with row3c1:
        a_c = st.number_input("A조 코트 수", 1, 10, 2)
    with row3c2:
        b_c = st.number_input("B조 코트 수", 0, 10, 0)
    
    match_rules = st.text_input("경기 규칙", value="(모든 게임 1:1 시작, 노에드, 5:5 타이 7포인트 선승...)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── 💰 상벌금 설정 ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 💰 상벌금 설정 (1등 / 하위 25% / 최하위 25%)")
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.session_state.reward_1st = st.number_input("1등 상금", value=st.session_state.reward_1st, step=1000)
    with r_col2:
        st.session_state.fine_25 = st.number_input("하위 25% 벌금", value=st.session_state.fine_25, step=1000)
    with r_col3:
        st.session_state.fine_last_25 = st.number_input("최하위 25% 벌금", value=st.session_state.fine_last_25, step=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    final_players = []
    for name in all_selected_names:
        # DB 정보 찾기 (나이, MBTI 등을 위해)
        m_info = next((m for m in members if m["nickname"] == name), {})
        final_players.append({
            "name": name, 
            "group": st.session_state.player_groups.get(name, "A"),
            "times": st.session_state.player_times.get(name, ["19:00", "22:00"]),
            "is_guest": name in st.session_state.guests,
            "birthdate": m_info.get("birthdate"),
            "mbti": m_info.get("mbti"),
            "achievements": m_info.get("achievements")
        })

    if st.button("🚀 KDK 대진 자동 생성", use_container_width=True):
        b_players = [p for p in final_players if p["group"] == "B"]
        
        # 🛡️ 고정 파트너 조 일치 검증
        fixed_group_error = False
        for p1, p2, _ in st.session_state.fixed_partners:
            g1 = st.session_state.player_groups.get(p1, "A")
            g2 = st.session_state.player_groups.get(p2, "A")
            if g1 != g2:
                st.error(f"⚠️ 고정 파트너인 {p1}님과 {p2}님이 서로 다른 조({g1}, {g2})에 배정되었습니다. 같은 조로 맞춰주세요.")
                fixed_group_error = True
                break
        
        if fixed_group_error: pass 
        elif len(final_players) < 4: st.error("최소 4명 이상 선택해주세요.")
        elif st.session_state.use_group_division and len(b_players) > 0 and b_c == 0:
            st.error("⚠️ B조 인원이 선택되었으나 B조 코트 수가 0입니다. 코트 수를 조정해주세요.")
        else:
            court_map = {'A': list(range(1, a_c+1)), 'B': list(range(a_c+1, a_c+b_c+1))}
            matches = generate_kdk_matches_v3(final_players, court_map, target_matches, concept=concept, fixed_partners=st.session_state.fixed_partners, fixed_partner_games=st.session_state.fixed_partner_games)
            
            # --- DB 저장 로직 추가 ---
            from db.supabase_client import create_kdk_session, upsert_kdk_matches
            
            try:
                # 1. 세션 생성
                award_config = {
                    "reward_1st": st.session_state.reward_1st,
                    "fine_25": st.session_state.fine_25,
                    "fine_last_25": st.session_state.fine_last_25
                }
                session_note = f"{concept} | 매칭 컨셉: {concept}"
                user_nickname = st.session_state.get("user", {}).get("nickname", "Admin")
                
                new_session = create_kdk_session(
                    club_id=CLUB_ID,
                    session_date=datetime.now().strftime("%Y-%m-%d"),
                    created_by=user_nickname,
                    note=session_note,
                    award_config=award_config
                )
                session_id = new_session.get("id")
                
                if session_id:
                    # 2. 매치 변환 및 저장
                    db_matches = []
                    for m in matches:
                        db_matches.append({
                            "session_id": session_id,
                            "group": m["group"],
                            "round": m["round"],
                            "court": m["court"],
                            "team1": m["team1"], # JSONB로 저장됨
                            "team2": m["team2"],
                            "score1": 0,
                            "score2": 0,
                            "status": "pending"
                        })
                    
                    saved_matches = upsert_kdk_matches(db_matches)
                    
                    # session_state 동기화 (DB ID 포함)
                    for i, m in enumerate(matches):
                        if i < len(saved_matches):
                            m["id"] = saved_matches[i]["id"]
                            m["session_id"] = session_id
                
                st.session_state.kdk_all_data = {
                    "session_id": session_id if 'session_id' in locals() else None,
                    "players": final_players,
                    "matches": matches,
                    "groups": ["A", "B"] if b_c > 0 else ["A"],
                    "start_time": start_t.strftime("%H:%M"),
                    "duration": match_dur,
                    "match_rules": match_rules,
                    "concept": concept,
                    "award_config": award_config
                }
                st.session_state.match_created_msg = "🚀 대진표가 성공적으로 생성되어 DB에 저장되었습니다!"
                st.rerun()
            except Exception as e:
                st.error(f"❌ DB 저장 중 오류가 발생했습니다: {e}")
                # 오류 발생해도 일단 세션에는 저장 (오프라인 모드 처럼)
                st.session_state.kdk_all_data = {
                    "players": final_players,
                    "matches": matches,
                    "groups": ["A", "B"] if b_c > 0 else ["A"],
                    "start_time": start_t.strftime("%H:%M"),
                    "duration": match_dur,
                    "match_rules": match_rules,
                    "concept": concept
                }
                st.rerun()

# ── 피드백 메시지 표시 ──────────────────────────────────────────────
if st.session_state.get('match_created_msg'):
    st.toast(st.session_state.match_created_msg)
    st.balloons()
    st.success(st.session_state.match_created_msg)
    del st.session_state.match_created_msg

st.markdown('</div>', unsafe_allow_html=True)
