import streamlit as st
from db.supabase_client import get_all_members, update_member_info
import os

st.set_page_config(page_title="멤버 관리 | TEYEON", page_icon="📝", layout="wide")

if not st.session_state.get("is_admin"):
    st.error("운영진만 접근 가능한 페이지입니다.")
    st.stop()

CLUB_ID = os.environ.get("CLUB_ID", "")
members = get_all_members(CLUB_ID)

st.markdown("## 📝 멤버 정보 관리")
st.caption("회원의 명단 정보를 직접 수정할 수 있습니다.")

search = st.text_input("🔍 멤버 검색 (이름)", placeholder="이름을 입력하세요...")
filtered = [m for m in members if search.lower() in m.get("nickname", "").lower()] if search else members

if not filtered:
    st.info("검색 결과가 없습니다.")
else:
    for m in filtered:
        nickname = m.get("nickname", "이름없음")
        m_id = m.get("id")
        
        with st.expander(f"👤 {nickname} ({m.get('position') or '일반회원'})"):
            with st.form(key=f"edit_form_{m_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_nickname = st.text_input("이름(닉네임)", value=m.get("nickname"))
                    new_phone = st.text_input("연락처", value=m.get("phone") or "")
                    new_pos = st.text_input("직책", value=m.get("position") or "")
                    # 생년월일 추가 (데이터가 없으면 오늘 날짜 혹은 특정 기본값)
                    import datetime
                    b_val = m.get("birthdate")
                    if isinstance(b_val, str): b_val = datetime.date.fromisoformat(b_val)
                    elif not b_val: b_val = datetime.date(1990, 1, 1)
                    new_birth = st.date_input("생년월일", value=b_val, min_value=datetime.date(1950, 1, 1), max_value=datetime.date.today())
                with col2:
                    new_mbti = st.text_input("MBTI", value=m.get("mbti") or "")
                    new_aff = st.text_input("소속", value=m.get("affiliation") or "")
                    new_ach = st.text_area("입상 경력", value=m.get("achievements") or "")
                
                if st.form_submit_button("💾 정보 수정 저장"):
                    edit_data = {
                        "nickname": new_nickname,
                        "phone": new_phone,
                        "position": new_pos,
                        "birthdate": new_birth.isoformat(),
                        "mbti": new_mbti,
                        "affiliation": new_aff,
                        "achievements": new_ach
                    }
                    try:
                        res = update_member_info(m_id, edit_data)
                        if res:
                            st.success(f"✅ {new_nickname}님의 정보가 성공적으로 수정되었습니다!")
                            st.rerun()
                        else:
                            st.error("수정에 실패했습니다 (응답 없음).")
                    except Exception as e:
                        if "birthdate" in str(e) or "생년월일" in str(e):
                            st.error("❌ '생년월일' 컬럼이 DB에 없습니다. 아래 SQL을 Supabase SQL Editor에서 실행해주세요:")
                            st.code("ALTER TABLE members ADD COLUMN birthdate DATE;")
                        else:
                            st.error(f"❌ 수정 중 오류 발생: {e}")
