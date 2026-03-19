import streamlit as st
from db.supabase_client import get_all_members
import os
import base64

st.set_page_config(page_title="멤버 정보 | TEYEON", page_icon="👥", layout="wide")

# 로컬 이미지 표시를 위한 함수 (Storage 업로드 실패 대비)
def get_local_img_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    return None

st.markdown("""
<style>
.member-card { 
    background: rgba(255, 255, 255, 0.07); 
    border-radius: 20px; 
    border: 1px solid rgba(255, 255, 255, 0.1); 
    padding: 28px; /* 패딩 추가 확대 */
    margin-bottom: 25px;
    display: flex;
    flex-direction: column;
}
.member-header {
    display: flex;
    align-items: center; 
    margin-bottom: 35px; /* 헤더와 아래 섹션 간격 대폭 확보 */
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    flex-shrink: 0;
}
.profile-img-container {
    width: 75px; 
    height: 75px; 
    border-radius: 50%; 
    background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    font-size: 38px; 
    margin-right: 20px; /* 여백 확대 */
    overflow: hidden;
    flex-shrink: 0;
    border: 3px solid rgba(255, 255, 255, 0.1); /* 테두리 강조 */
    box-shadow: 0 4px 10px rgba(0,0,0,0.2); 
}
.profile-img-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.name-role-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center; /* 가로 중앙 정렬 */
    text-align: center;
}
.member-name { font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-bottom: 6px; flex-shrink: 0; width: 100%; }
.member-role { 
    display: inline-block; 
    padding: 2px 10px; 
    border-radius: 20px; 
    font-size: 0.85rem; 
    font-weight: 700; 
    flex-shrink: 0;
}
.role-admin { background-color: #FEE500; color: #000000; }
.role-member { background-color: #4a5568; color: #ffffff; }

.info-section { 
    background: rgba(0, 0, 0, 0.25); 
    border-radius: 12px; 
    padding: 15px; 
    margin-top: 5px; /* 헤더와의 간격 유지 */
    height: auto; 
    display: flex;
    flex-direction: column;
}
.info-item { margin-bottom: 10px; }
.info-label { color: #a0aec0; font-size: 0.8rem; font-weight: 600; margin-bottom: 2px; }
.info-value { 
    color: #f7fafc; 
    font-size: 0.95rem; 
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2; /* 최대 2줄만 표시 */
    -webkit-box-orient: vertical;
    min-height: 2.4em; /* 높이 일정하게 유지 */
}
</style>
""", unsafe_allow_html=True)

CLUB_ID = os.environ.get("CLUB_ID", "")
members = get_all_members(CLUB_ID)

# ── 운영진 및 프로필 설정 ───────────────────────────────────────────────────
ADMIN_MAP = {"박광현": "회장", "강정호": "부회장", "정상윤": "총무", "곽민섭": "재무이사", "김민준": "경기이사", "남인우": "섭외이사"}
PIC_DIR = "c:/Users/섭이/Desktop/AI/1. Teyeon/Teyeon pic"

def get_sort_priority(m):
    n = m.get("nickname", "").strip()
    prio = {"박광현":1, "강정호":2, "정상윤":3, "곽민섭":4, "김민준":5, "남인우":6}
    return prio.get(n, 7 if m.get("is_admin") else 100)

members.sort(key=get_sort_priority)

st.markdown("## 👥 멤버 정보")
search_query = st.text_input("", placeholder="🔍 이름을 검색하세요...", label_visibility="collapsed")
filtered = [m for m in members if search_query.lower() in m.get("nickname", "").lower()] if search_query else members

if not filtered:
    st.info("검색 결과가 없습니다.")
else:
    cols = st.columns(3)
    for idx, m in enumerate(filtered):
        with cols[idx % 3]:
            nickname = m.get("nickname", "이름 없음").strip()
            is_admin = m.get("is_admin", False)
            
            # 직책 결정
            pos = ADMIN_MAP.get(nickname) or m.get("position") or ("운영진" if is_admin else "회원")
            role_class = "role-admin" if (is_admin or nickname in ADMIN_MAP) else "role-member"
            
            # 프로필 이미지 처리
            img_html = "🎾"
            # 1. DB에 이미지 URL이 있는 경우
            m_img = m.get("profile_image")
            # 2. 로컬 폴더에 이름과 일치하는 이미지가 있는 경우 (우선순위)
            local_path = os.path.join(PIC_DIR, f"{nickname}.png")
            if not os.path.exists(local_path):
                local_path = os.path.join(PIC_DIR, f"{nickname}.jpg")
            
            b64_img = get_local_img_base64(local_path)
            if b64_img:
                img_html = f'<img src="data:image/png;base64,{b64_img}">'
            elif m_img:
                img_html = f'<img src="{m_img}">'
            
            # 카드 HTML 구성
            html = f"""
            <div class="member-card">
                <div class="member-header">
                    <div class="profile-img-container">{img_html}</div>
                    <div class="name-role-container">
                        <div class="member-name">{nickname}</div>
                        <div class="member-role {role_class}">{pos}</div>
                    </div>
                </div>
                <div class="info-section">
                    <div class="info-item">
                        <div class="info-label">📞 연락처</div>
                        <div class="info-value">{m.get("phone") or "-"}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🏠 소속</div>
                        <div class="info-value">{m.get("affiliation") or "-"}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">✨ MBTI</div>
                        <div class="info-value">{m.get("mbti") or "-"}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🏆 입상 경력</div>
                        <div class="info-value">{m.get("achievements") or "-"}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
