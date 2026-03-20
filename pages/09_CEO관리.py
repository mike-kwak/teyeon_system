import streamlit as st
import pandas as pd
from db.supabase_client import (
    log_access, get_ceo_dashboard_stats, get_menu_permissions, update_menu_permissions,
    get_tournament_results, add_tournament_result, delete_tournament_result,
    get_menu_settings, update_menu_setting
)
import os

st.set_page_config(page_title="CEO 관리 | TEYEON", page_icon="👑", layout="wide")

# 권한 체크
user = st.session_state.get("user")
role = st.session_state.get("role", "Guest")

if role != "CEO":
    st.error("CEO 전용 메뉴입니다. 접근 권한이 없습니다.")
    st.stop()

# 로그 기록
nickname = user.get("nickname", "Guest") if user else "Visitor"
member_id = user.get("id") if user and not user.get("is_guest") else None
log_access(member_id, nickname, role, "CEO Management Page")

st.title("👑 CEO 시스템 관리")
st.markdown("실시간 접속 현황 및 권한 설정을 관리합니다.")

# 데이터 로드
try:
    stats = get_ceo_dashboard_stats()
except Exception as e:
    st.error("⚠️ 데이터베이스 테이블이 아직 생성되지 않았습니다.")
    st.info("아래 [SQL Editor 안내] 섹션의 SQL을 Supabase 대시보드에서 실행해 주세요.")
    with st.expander("🛠️ SQL Editor용 코드 보기", expanded=True):
        from db.supabase_client import get_menu_settings
        st.code("""
-- 아래 코드를 실행하여 필수 테이블을 생성해 주세요.
CREATE TABLE IF NOT EXISTS tournament_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_date DATE NOT NULL,
    tournament_name TEXT NOT NULL,
    rank TEXT NOT NULL,
    winners TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS menu_settings (
    page_filename TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    order_index INT DEFAULT 99,
    is_hidden BOOLEAN DEFAULT FALSE
);

INSERT INTO menu_settings (page_filename, display_name, order_index) VALUES
('00_공지사항.py', '📢 공지사항', 0),
('01_대시보드.py', '🏠 대시보드', 1),
('02_대진생성.py', '🎾 대진생성', 2),
('03_경기진행.py', '🏃 경기진행', 3),
('03_경기결과.py', '📊 경기결과', 4),
('04_재무.py', '💰 재무', 5),
('05_랭킹.py', '🔥 랭킹', 6),
('06_시드예측.py', '⚡ 시드예측', 7),
('07_멤버정보.py', '👤 멤버정보', 8),
('08_멤버관리.py', '🛠️ 멤버관리', 9),
('09_CEO관리.py', '👑 CEO관리', 10)
ON CONFLICT (page_filename) DO UPDATE SET 
    display_name = EXCLUDED.display_name,
    order_index = EXCLUDED.order_index;
        """, language="sql")
    st.stop()

# ── 1. 요약 통계 ──
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("오늘 총 방문 수", f"{stats['today_total']}회")
with col2:
    # 실시간 접속 (최근 5분 내 로그 수)
    from datetime import datetime, timedelta
    now = datetime.now()
    # 주의: created_at은 UTC일 수 있으므로 로컬 시간 처리가 필요할 수 있음
    # 여기서는 단순 개수만 표시
    st.metric("최근 활동", f"{len(stats['recent_logs'])}건")
with col3:
    st.metric("오늘 게스트 방문", f"{len(stats['guest_logs'])}명")

tab_logs, tab_permission, tab_tourney, tab_menu = st.tabs(["📝 접속 로그", "🔐 권한 설정", "🏆 성과 관리", "⚙️ 메뉴 관리"])

with tab_logs:
    st.subheader("실시간 접속 로그 (최신 30건)")
    if stats['recent_logs']:
        df = pd.DataFrame(stats['recent_logs'])
        # 컬럼 정리
        df = df[['created_at', 'nickname', 'role', 'page_name']]
        df.columns = ['시간', '닉네임', '권한', '페이지']
        st.dataframe(df, use_container_width=True)
    else:
        st.info("기록된 로그가 없습니다.")

    st.divider()
    st.subheader("👤 오늘 방문한 게스트")
    if stats['guest_logs']:
        gdf = pd.DataFrame(stats['guest_logs'])
        gdf.columns = ['닉네임', '접속 시간']
        st.table(gdf)
    else:
        st.write("오늘 방문한 게스트가 없습니다.")

    # 전체 메뉴 목록 (DB 기반)
    menu_data = get_menu_settings()
    all_pages = [m['page_filename'] for m in menu_data]
    
    # 4단계 권한 Loop
    roles = ["CEO", "Staff", "Member", "Guest"]
    
    for r in roles:
        with st.expander(f"⚙️ {r} 권한 설정", expanded=(r=="Guest")):
            current_perms = get_menu_permissions(r)
            # 허용된 페이지 설정 (숨김 여부와 관계없이 설정은 가능하게)
            new_perms = st.multiselect(
                f"{r}가 접근 가능한 페이지", 
                options=all_pages, 
                default=[p for p in current_perms if p in all_pages],
                key=f"perm_{r}"
            )
            if st.button(f"{r} 권한 저장", key=f"save_{r}"):
                update_menu_permissions(r, new_perms)
                st.success(f"{r} 권한이 업데이트되었습니다.")
                st.rerun()

with tab_tourney:
    st.subheader("🏆 2026 대회 성과 기록")
    
    with st.form("add_tourney_form", clear_on_submit=True):
        st.write("새 성과 추가")
        f_date = st.date_input("대회 날짜")
        f_name = st.text_input("대회명", placeholder="ex) 제1회 테연 클럽 대항전")
        f_rank = st.selectbox("최종 순위", ["우승", "준우승", "3위", "공동 3위", "8강", "본선진출", "참가"])
        f_winners = st.text_input("수상자", placeholder="ex) 곽민섭, 정회원")
        
        if st.form_submit_button("성과 추가"):
            if f_name and f_winners:
                add_tournament_result(f_date.isoformat(), f_name, f_rank, f_winners)
                st.success("성과가 기록되었습니다.")
                st.rerun()
            else:
                st.error("대회명과 수상자를 입력해주세요.")

    st.divider()
    st.write("기존 성과 목록")
    t_results = get_tournament_results()
    if t_results:
        for res in t_results:
            col_info, col_del = st.columns([8, 1])
            col_info.write(f"📅 {res['tournament_date']} | **{res['tournament_name']}** — {res['rank']} ({res['winners']})")
            if col_del.button("❌", key=f"del_res_{res['id']}"):
                delete_tournament_result(res['id'])
                st.rerun()
    else:
        st.info("기록된 성과가 없습니다.")

with tab_menu:
    st.subheader("⚙️ 사이드바 메뉴 제어")
    st.info("메뉴 이름, 순서, 숨김 여부를 관리합니다. 설정 즉시 모든 계정에 반영됩니다.")
    
    menu_list = get_menu_settings()
    
    for m in menu_list:
        with st.expander(f"📄 {m['page_filename']} ({m['display_name']})"):
            c1, c2, c3 = st.columns([3, 1, 1])
            new_label = c1.text_input("표시 이름", value=m['display_name'], key=f"label_{m['page_filename']}")
            new_order = c2.number_input("순번", value=m['order_index'], min_value=0, max_value=99, key=f"order_{m['page_filename']}")
            new_hidden = c3.checkbox("숨김", value=m['is_hidden'], key=f"hide_{m['page_filename']}")
            
            if st.button("설정 저장", key=f"save_menu_{m['page_filename']}"):
                update_menu_setting(m['page_filename'], new_label, new_order, new_hidden)
                st.success(f"'{m['page_filename']}' 설정이 변경되었습니다.")
                st.rerun()
