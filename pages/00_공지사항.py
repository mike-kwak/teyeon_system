import streamlit as st
import os
from db.supabase_client import log_access

st.set_page_config(page_title="공지사항 | TEYEON", page_icon="📢", layout="wide")

# 권한 체크 및 로그 기록
user = st.session_state.get("user")
role = st.session_state.get("role", "Guest")
nickname = user.get("nickname", "Guest") if user else "Visitor"
member_id = user.get("id") if user and not user.get("is_guest") else None
log_access(member_id, nickname, role, "Notice Page")

st.markdown("""
<style>
.notice-card {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 20px;
    padding: 25px;
    border-left: 6px solid #CCFF00;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.notice-card:hover {
    transform: translateY(-5px);
    background: rgba(204, 255, 0, 0.03);
    border-color: #CCFF00;
}
.notice-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 8px;
    font-family: 'Oswald', sans-serif;
}
.notice-date {
    font-size: 0.85rem;
    color: #CCFF00;
    font-weight: 700;
    margin-bottom: 15px;
    letter-spacing: 1px;
}
.notice-content {
    color: #dae1ed;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

st.title("📢 공지사항")
st.markdown("테연 테니스 클럽의 최신 소식을 전해드립니다.")

notices = [
    {
        "title": "🎾 2026년 3월 정기 모임 안내",
        "date": "2026-03-20",
        "content": "이번 달 정기 모임은 3월 28일 토요일 오후 6시부터 진행됩니다. 많은 참석 부탁드립니다!"
    },
    {
        "title": "🏆 상반기 클럽 대항전 결과",
        "date": "2026-03-15",
        "content": "우리 클럽이 이번 상반기 연합 대회에서 준우승을 차지했습니다! 고생하신 모든 멤버분들 축하드립니다."
    },
    {
        "title": "🛠️ 시스템 업데이트 안내 (v1.2)",
        "date": "2026-03-10",
        "content": "이제 권한 시스템과 접속 로그 기능이 추가되었습니다. 비회원분들도 공지사항을 확인하실 수 있습니다."
    }
]

for notice in notices:
    st.markdown(f"""
    <div class="notice-card">
        <div class="notice-title">{notice['title']}</div>
        <div class="notice-date">{notice['date']}</div>
        <div class="notice-content">{notice['content']}</div>
    </div>
    """, unsafe_allow_html=True)

if role == "CEO":
    st.divider()
    if st.button("➕ 새 공지사항 작성 (CEO 전용)"):
        st.info("공지사항 작성 기능은 다음 업데이트에서 구현될 예정입니다.")
