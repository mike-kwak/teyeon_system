import streamlit as st
from db.supabase_client import get_all_members, check_auth_and_log
import os
import base64

st.set_page_config(page_title="멤버 정보 | TEYEON", page_icon="👥", layout="wide")

# ── 권한 체크 및 로그 기록 ────────────────────────────────────────────────────────
check_auth_and_log("07_멤버정보.py")

from core_logic.utils import get_local_img_base64, find_member_image_path, get_member_photo_html, get_member_official_role

st.markdown("""
<style>
/* v5.3 모바일 2열 프리미엄 그리드 */
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important; /* wrap 허용 */
        gap: 12px 10px !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        width: calc(50% - 5px) !important;
        min-width: calc(50% - 5px) !important;
        max-width: calc(50% - 5px) !important;
        flex: 0 0 calc(50% - 5px) !important;
    }
    .member-card { 
        padding: 18px 12px !important; 
        border-radius: 16px !important;
        margin-bottom: 0 !important;
        height: 100% !important;
        flex: 1;
    }
    .profile-img-container {
        width: 60px !important; 
        height: 60px !important;
        margin-right: 0 !important;
        margin-bottom: 12px !important;
        border-width: 2px !important;
    }
    .member-header {
        flex-direction: column !important;
        margin-bottom: 15px !important;
        padding-bottom: 10px !important;
    }
    .member-name { font-size: 1.1rem !important; }
    .member-role { font-size: 0.8rem !important; padding: 2px 10px !important; }
    .info-section { display: flex !important; padding: 12px !important; gap: 8px; }
    .info-label { font-size: 0.7rem !important; margin-bottom: 1px !important; }
    .info-value { font-size: 0.85rem !important; min-height: 1.2em !important; line-height: 1.3; }
}

.member-card { 
    background: rgba(255, 255, 255, 0.07); 
    border-radius: 20px; 
    border: 1px solid rgba(255, 255, 255, 0.1); 
    padding: 28px;
    margin-bottom: 25px;
    display: flex;
    flex-direction: column;
}
.member-header {
    display: flex;
    align-items: center; 
    margin-bottom: 35px;
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
    margin-right: 20px;
    overflow: hidden;
    flex-shrink: 0;
    border: 3px solid rgba(255, 255, 255, 0.1);
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
    align-items: center;
    text-align: center;
}
.member-name { font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-bottom: 6px; flex-shrink: 0; width: 100%; }
.member-role { 
    display: inline-block; 
    padding: 2px 10px; 
    border-radius: 20px; 
    font-size: 0.85rem; 
    font-weight: 700; 
}
.role-admin { background-color: #FEE500; color: #000000; }
.role-member { background-color: #4a5568; color: #ffffff; }

.info-section { 
    background: rgba(0, 0, 0, 0.25); 
    border-radius: 12px; 
    padding: 15px; 
    margin-top: 5px;
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
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    min-height: 2.4em;
}
</style>
""", unsafe_allow_html=True)

CLUB_ID = os.environ.get("CLUB_ID", "")
members = get_all_members(CLUB_ID)

# ── 운영진 및 프로필 설정 ───────────────────────────────────────────────────
# (core_logic.utils에서 통합 관리됨)

def get_sort_priority(m):
    n = m.get("nickname", "").strip()
    prio = {"박광현":1, "강정호":2, "정상윤":3, "곽민섭":4, "김민준":5, "남인우":6}
    return prio.get(n, 7 if m.get("is_admin") else 100)

members.sort(key=get_sort_priority)

# ── v5.4 진단 모드 (운영진 전용) ──────────────────────────────────────────────────
is_ceo_or_staff = st.session_state.get("user_role") in ["CEO", "Staff"]
if is_ceo_or_staff:
    with st.expander("🛠️ 시스템 진단 (운영진 전용)"):
        st.write(f"현재 작업 디렉토리 (CWD): `{os.getcwd()}`")
        for d in SEARCH_DIRS:
            exists = os.path.exists(d)
            color = "green" if exists else "red"
            st.markdown(f"경로: `:{color}[{d}]` (존재: {exists})")
            if exists:
                files = os.listdir(d)
                st.write(f"  - 파일 목록 ({len(files)}개): {files[:10]}...")

st.markdown("## 👥 멤버 정보")
search_query = st.text_input("", placeholder="🔍 이름을 검색하세요...", label_visibility="collapsed")
filtered = [m for m in members if search_query.lower() in m.get("nickname", "").lower()] if search_query else members

if not filtered:
    st.info("검색 결과가 없습니다.")
else:
    # ── v5.2 풍성한 2열 그리드 루프 ──
    rows = [filtered[i:i+2] for i in range(0, len(filtered), 2)]
    
    for row in rows:
        cols = st.columns(2)
        for idx, m in enumerate(row):
            with cols[idx]:
                nickname = m.get("nickname", "이름 없음").strip()
                is_admin = m.get("is_admin", False)
                
                # 직책 및 이미지 연동 (v6.0 Utility 사용)
                pos = get_member_official_role(nickname, m.get("position"))
                role_class = "role-admin" if pos in ["회장", "부회장", "총무", "재무이사", "경기이사", "섭외이사", "운영진"] else "role-member"
                
                # 프로필 이미지 처리
                img_html = get_member_photo_html(nickname, size=75, border=True)
                
                # 카드 HTML 구성
                st.markdown(f"""
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
                """, unsafe_allow_html=True)
