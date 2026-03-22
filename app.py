"""
app.py
──────
TEYEON 테니스 클럽 관리 앱 메인 진입점.

역할:
  - 카카오 OAuth 흐름 처리 (URL 파라미터 ?code= 감지)
  - st.session_state에 로그인 상태 유지
  - 로그인 전 → 랜딩 페이지(카카오 로그인 버튼)
  - 로그인 후 → 사이드바 메뉴 + 대시보드 리다이렉션
"""

import streamlit as st
from dotenv import load_dotenv

from core_logic.auth import get_kakao_auth_url, exchange_code_for_token, get_kakao_user_info, logout
from db.supabase_client import upsert_member, get_member_by_kakao_id, log_access, get_menu_permissions

load_dotenv()

# ── 페이지 기본 설정 ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="TEYEON | 테니스 클럽",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── UI/UX Pro Max 글로벌 테마 ────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #0A0E1A; /* Deep Navy */
}

/* 폰트 및 글로벌 스타일 */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800&family=Oswald:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
}

/* 버튼 스타일 고도화 */
.stButton > button {
    border-radius: 18px !important;
    border: none !important;
    padding: 12px 24px !important;
    font-weight: 700 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 8px 25px rgba(204, 255, 0, 0.2) !important;
}

/* 카카오 로그인 버튼 전용 */
.kakao-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background-color: #FEE500;
    color: #000000 !important;
    font-weight: 800;
    font-size: 18px;
    padding: 18px 40px;
    border-radius: 20px;
    text-decoration: none !important;
    box-shadow: 0 10px 30px rgba(254,229,0,0.2);
    transition: all 0.3s ease;
}
.kakao-btn:hover {
    background-color: #CCFF00; /* 네온그린으로 전환되는 효과 */
    transform: translateY(-4px);
    box-shadow: 0 15px 40px rgba(204,255,0,0.4);
}

/* 로고 타이틀 디자인 (고도화) */
.logo-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-bottom: 3.5rem;
    padding: 20px;
}

.teyeon-logo {
    display: flex;
    align-items: center;
    gap: 18px;
}

.tennis-ball-icon {
    filter: drop-shadow(0 0 10px rgba(204, 255, 0, 0.6));
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); filter: drop-shadow(0 0 5px rgba(204, 255, 0, 0.4)); }
    50% { transform: scale(1.05); filter: drop-shadow(0 0 15px rgba(204, 255, 0, 0.8)); }
    100% { transform: scale(1); filter: drop-shadow(0 0 5px rgba(204, 255, 0, 0.4)); }
}

.logo-main-text {
    font-size: 5.5rem;
    font-weight: 900;
    color: white;
    letter-spacing: -4px;
    line-height: 0.8;
    font-family: 'Montserrat', sans-serif;
}

.logo-sub-text {
    font-size: 1.8rem;
    color: #CCFF00;
    font-style: italic;
    letter-spacing: 5px;
    font-weight: 800;
    line-height: 1;
    display: block;
    transform: skewX(-10deg);
}

.since-badge {
    background: rgba(204, 255, 0, 0.15);
    color: #CCFF00;
    padding: 6px 20px;
    border-radius: 30px;
    font-size: 0.9rem;
    font-weight: 900;
    letter-spacing: 2px;
    border: 1px solid rgba(204, 255, 0, 0.4);
    margin-top: 25px;
    box-shadow: 0 4px 15px rgba(204, 255, 0, 0.2);
}

/* 사이드바 프로필 */
.sidebar-profile {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 18px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 기능 카드 (Landing) */
.feature-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 15px;
    transition: all 0.3s ease;
}
.feature-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: #CCFF00;
    transform: translateX(10px);
}
.sidebar-profile img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid #FEE500;
}

/* ── 데스크톱에서 사이드바 숨기기 버튼 제거 (항상 펼쳐진 상태 유지) ── */
@media (min-width: 768px) {
    [data-testid="collapsedControl"] { display: none !important; }
    button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
    section[data-testid="stSidebar"] > div:first-child { min-width: 250px !important; }
}
</style>
""", unsafe_allow_html=True)


# ── 세션 초기화 ───────────────────────────────────────────────────────────
def _init_session():
    defaults = {
        "user": None,
        "access_token": None,
        "is_admin": False,
        "kakao_id": None,
        "role": "Guest",  # 기본 권한은 Guest
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── 카카오 OAuth 콜백 처리 ─────────────────────────────────────────────────
def _handle_oauth_callback():
    """URL에 ?code= 파라미터가 있으면 토큰 교환 → 사용자 정보 조회 → DB upsert."""
    params = st.query_params
    code = params.get("code")
    if not code or st.session_state.get("user"):
        return  # 이미 로그인됐거나 code가 없으면 스킵

    with st.spinner("카카오 로그인 처리 중..."):
        token_data = exchange_code_for_token(code)
        if not token_data.get("access_token"):
            st.error(f"카카오 로그인에 실패했습니다. 상세: {token_data.get('error', '알 수 없거나 응답 없음')}")
            st.query_params.clear()
            return

        access_token = token_data["access_token"]
        user_info    = get_kakao_user_info(access_token)

        if not user_info.get("kakao_id"):
            st.error("사용자 정보를 가져오지 못했습니다.")
            st.query_params.clear()
            return

        # Supabase upsert
        try:
            member = upsert_member(
                kakao_id      = user_info["kakao_id"],
                nickname      = user_info["nickname"],
                profile_image = user_info.get("profile_image"),
                email         = user_info.get("email"),
            )
        except EnvironmentError:
            st.warning("⚠️ Supabase DB가 설정되지 않아 임시 세션으로 로그인합니다.")
            member = None
        except Exception as e:
            st.warning(f"⚠️ Supabase DB 권한/연동 에러로 인해 임시 세션으로 로그인합니다. (RLS 설정 등을 확인해주세요)")
            member = None

        # 세션에 저장
        st.session_state["user"]         = member or user_info
        st.session_state["access_token"] = access_token
        st.session_state["kakao_id"]     = user_info["kakao_id"]
        st.session_state["is_admin"]     = member.get("is_admin", False) if member else False
        st.session_state["role"]         = member.get("role", "Member") if member else "Member"

        # URL 정리 (code 파라미터 제거)
        st.query_params.clear()
        st.rerun()


# ── 랜딩 페이지 (비로그인) ────────────────────────────────────────────────
def _render_landing():
    import base64, pathlib

    def _img_to_b64(path: str) -> str:
        try:
            data = pathlib.Path(path).read_bytes()
            return base64.b64encode(data).decode()
        except Exception:
            return ""

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        # ── 로고 이미지 (텍스트 대신 이미지 → 자동번역 방지) ──
        logo_b64 = _img_to_b64("assets/logo.png")
        if logo_b64:
            st.markdown(f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{logo_b64}"
                     alt="TEYEON TENNIS"
                     style="max-width:160px; width:60%; border-radius:16px; margin-bottom:18px;" />
                <div class="since-badge">SINCE 2025</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 이미지 로드 실패 시 폴백
            st.markdown("""
            <div class="logo-container">
                <div class="teyeon-logo">
                    <div class="tennis-ball-icon">
                        <svg viewBox="0 0 100 100" width="80" height="80">
                            <circle cx="50" cy="50" r="48" fill="#CCFF00" />
                            <path d="M25,20 Q50,50 25,80" fill="none" stroke="#666" stroke-width="2.5" />
                            <path d="M75,20 Q50,50 75,80" fill="none" stroke="#666" stroke-width="2.5" />
                        </svg>
                    </div>
                    <div style="display:flex;flex-direction:column;align-items:flex-start;">
                        <div class="logo-main-text">TEYEON</div>
                        <div class="logo-sub-text">TENNIS</div>
                    </div>
                </div>
                <div class="since-badge">SINCE 2025</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### ✨ Pro Max 주요 기능")
        features = [
            ("🏸", "KDK 대진 자동 생성", "4인 1조 매칭, 특정 파트너 지정 반영"),
            ("💰", "상벌금 자동 계산",   "승패·득실차 기반 동적 분배"),
            ("📊", "기간별 랭킹",        "주·월·년 단위 포인트 대시보드"),
            ("🛡️", "완벽한 보안 절차",      "4단계 권한 및 실시간 접속 감시"),
        ]
        for icon, title, desc in features:
            st.markdown(f"""
            <div class="feature-card">
                <strong>{icon} {title}</strong><br/>
                <small style="color: #aab8d4;">{desc}</small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        auth_url = get_kakao_auth_url()
        st.markdown(
            f'<a href="{auth_url}" class="kakao-btn">'
            f'<span style="font-size:1.3em;">💬</span> 카카오로 시작하기'
            f'</a>',
            unsafe_allow_html=True,
        )
        st.caption("카카오 계정으로 1초 로그인 · 별도 회원가입 불필요")

        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🏟️ Guest로 접속하기", use_container_width=True):
            st.session_state["user"] = {"nickname": f"Guest_{st.query_params.get('id', 'visitor')}", "is_guest": True}
            st.session_state["role"] = "Guest"
            st.rerun()


# ── 사이드바 (로그인 후) ──────────────────────────────────────────────────
def _render_sidebar():
    user     = st.session_state.get("user", {})
    is_admin = st.session_state.get("is_admin", False)

    with st.sidebar:
        # 프로필
        img_url  = user.get("profile_image", "")
        nickname = user.get("nickname", "회원")
        badge    = "👑 운영진" if is_admin else "🎾 회원"

        if img_url:
            st.markdown(
                f'<div class="sidebar-profile">'
                f'<img src="{img_url}" />'
                f'<div><strong>{nickname}</strong><br/><small>{badge}</small></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**{nickname}** · {badge}")

        st.markdown("---")

        # 메뉴 (권한 및 설정 기반 동적 렌더링)
        st.markdown("#### 📋 메뉴")
        from db.supabase_client import get_sidebar_items
        
        role = st.session_state.get("role", "Guest")
        sidebar_items = get_sidebar_items(role)
        
        for item in sidebar_items:
            st.page_link(item["path"], label=item["label"])

        st.markdown("---")
        if st.button("로그아웃", use_container_width=True):
            logout(st.session_state)
            st.query_params.clear()
            st.rerun()


# ── Action Tower 홈 렌더링 ──────────────────────────────────────────────────
ROLE_LEVEL = {"CEO": 4, "Staff": 3, "Member": 2, "Guest": 1}
ROLE_LABELS = {
    "CEO":    ("👑 최고관리자", "#FFD700"),
    "Staff":  ("🔧 운영진",     "#CCFF00"),
    "Member": ("🎾 정회원",     "#60EFFF"),
    "Guest":  ("🔓 게스트",     "#aab8d4"),
}
HOME_MENU = [
    dict(icon="👤", label="멤버\n정보",   page="pages/07_멤버정보.py",  min_role="Member", coming_soon=False),
    dict(icon="🎾", label="KDK\n대진표",  page="pages/02_대진생성.py",  min_role="Staff",  coming_soon=False),
    dict(icon="🏆", label="실시간\n랭킹",  page="pages/05_랭킹.py",      min_role="Member", coming_soon=False),
    dict(icon="💰", label="상벌금\n현황",  page="pages/04_재무.py",      min_role="Member", coming_soon=False),
    dict(icon="🏅", label="대회\n모드",    page=None,                    min_role="Member", coming_soon=True),
    dict(icon="💬", label="커뮤니티",      page=None,                    min_role="Member", coming_soon=True),
]

def _render_home(user: dict, role: str):
    nickname    = user.get("nickname", "회원")
    profile_img = user.get("profile_image", "")
    initials    = nickname[:1] if nickname else "?"
    role_text, role_color = ROLE_LABELS.get(role, ("🔓 게스트", "#aab8d4"))

    def can_access(min_role):
        return ROLE_LEVEL.get(role, 1) >= ROLE_LEVEL.get(min_role, 2)

    # ── CSS ──
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap');
.at-profile-card {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, rgba(26,37,61,0.95), rgba(10,14,26,0.98));
    border: 1px solid rgba(204,255,0,0.22); border-radius: 22px;
    padding: 18px 20px; margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.45);
}
.at-profile-info { display: flex; align-items: center; gap: 14px; }
.at-avatar {
    width: 54px; height: 54px; border-radius: 50%; object-fit: cover;
    border: 2.5px solid #CCFF00;
}
.at-avatar-init {
    width: 54px; height: 54px; border-radius: 50%;
    background: linear-gradient(135deg,#1a253d,#2a3f5f);
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 1.4rem; color: #CCFF00;
    border: 2.5px solid #CCFF00;
}
.at-name {
    font-family: 'Outfit',sans-serif; font-weight: 900;
    font-size: 1.05rem; color: #fff; line-height: 1.25;
}
.at-badge {
    display: inline-block; font-size: 0.68rem; font-weight: 700;
    padding: 2px 10px; border-radius: 30px; margin-top: 5px; border: 1px solid;
}
.at-ceo-btn {
    background: linear-gradient(135deg,#CCFF00,#a8d400);
    color: #0A0E1A !important; font-weight: 900 !important;
    font-size: 0.78rem !important; border: none !important;
    border-radius: 14px !important; padding: 9px 15px !important;
    cursor: pointer; white-space: nowrap; text-decoration: none;
    box-shadow: 0 4px 16px rgba(204,255,0,0.35);
}
.at-grid-title {
    font-family: 'Outfit',sans-serif; font-size: 0.72rem; font-weight: 700;
    color: #aab8d4; letter-spacing: 1.5px; text-transform: uppercase;
    margin-bottom: 10px;
}
/* 아이콘 그리드 버튼 스타일 */
.icon-btn > div.stButton > button {
    width: 100% !important; min-height: 90px !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    color: #d0ddf0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.73rem !important; font-weight: 700 !important;
    line-height: 1.4 !important; transition: all 0.25s ease !important;
    padding: 14px 6px !important; white-space: pre-line !important;
}
.icon-btn > div.stButton > button:hover {
    background: rgba(204,255,0,0.09) !important;
    border-color: rgba(204,255,0,0.5) !important;
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(204,255,0,0.18) !important;
    color: #fff !important;
}
.icon-btn-locked > div.stButton > button {
    opacity: 0.42 !important; cursor: not-allowed !important;
}
.icon-btn-locked > div.stButton > button:hover {
    transform: none !important; background: rgba(255,255,255,0.04) !important;
    border-color: rgba(255,255,255,0.09) !important; box-shadow: none !important;
}
.icon-btn-coming > div.stButton > button {
    opacity: 0.32 !important; cursor: default !important;
}
.icon-btn-coming > div.stButton > button:hover { transform: none !important; }

/* ── 완벽 반응형(Responsive Fluid) 그리드: Z폴드/태블릿/다양한 해상도 완벽 대응 ── */
div[data-testid="stHorizontalBlock"]:has(.icon-btn, .icon-btn-locked, .icon-btn-coming) {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 12px !important;
    width: 100% !important;
}

/* 기본 상태 (Z폴드 접힌 화면이나 좁은 스마트폰): 2열 자동 꽉 채우기 & 글자 잘림 방지 */
div[data-testid="stHorizontalBlock"]:has(.icon-btn, .icon-btn-locked, .icon-btn-coming) > div[data-testid="column"] {
    flex: 1 1 calc(50% - 10px) !important; 
    min-width: 120px !important; /* 화면이 아무리 좁아져도 아이콘 텍스트 유지 */
    width: auto !important;
}

/* 중간 너비 이상의 화면 (Z폴드 펼침, 넓은 폰 가로모드, 태블릿): 부드럽게 3열로 자동 재배치 */
@media (min-width: 480px) {
    div[data-testid="stHorizontalBlock"]:has(.icon-btn, .icon-btn-locked, .icon-btn-coming) > div[data-testid="column"] {
        flex: 1 1 calc(33.333% - 10px) !important;
    }
}
</style>
""", unsafe_allow_html=True)

    # ── 프로필 카드 ──
    if profile_img:
        avatar = f'<img class="at-avatar" src="{profile_img}">'
    else:
        avatar = f'<div class="at-avatar-init">{initials}</div>'

    ceo_btn = f'<a href="pages/09_CEO관리.py" class="at-ceo-btn">⚙️ 설정 마스터</a>' if role == "CEO" else ""

    st.markdown(f"""
<div class="at-profile-card">
    <div class="at-profile-info">
        {avatar}
        <div>
            <div class="at-name">⭐ {nickname} 님<br>안녕하세요!</div>
            <div class="at-badge" style="color:{role_color};border-color:{role_color}44;">{role_text}</div>
        </div>
    </div>
    {ceo_btn}
</div>
<div class="at-grid-title">⚡ 빠른 이동</div>
""", unsafe_allow_html=True)

    # ── 완벽 반응형(Fluid) 아이콘 그리드 ──
    # 단일 블록 안에 전부 던져놓고, CSS flex-wrap의 힘으로 2열/3열을 화면 크기별로 자동 계산하게 만듭니다.
    cols = st.columns(len(HOME_MENU))
    for col, item in zip(cols, HOME_MENU):
        locked = not can_access(item["min_role"])
        coming = item["coming_soon"]
        if coming:
            div_class = "icon-btn icon-btn-coming"
            badge = "\n🚧"
        elif locked:
            div_class = "icon-btn icon-btn-locked"
            badge = "\n🔒"
        else:
            div_class = "icon-btn"
            badge = ""
        btn_label = f"{item['icon']}\n{item['label']}{badge}"
        with col:
            st.markdown(f'<div class="{div_class}">', unsafe_allow_html=True)
            if st.button(btn_label, key=f"home_{item['icon']}", use_container_width=True):
                if coming:
                    st.toast("🚧 준비 중입니다.")
                elif locked:
                    st.toast("🔒 정회원만 이용 가능한 메뉴입니다.")
                elif item["page"]:
                    st.switch_page(item["page"])
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")


# ── 메인 진입점 ───────────────────────────────────────────────────────────
def main():
    _init_session()
    _handle_oauth_callback()

    user = st.session_state.get("user")
    role = st.session_state.get("role", "Guest")

    # 접속 로그 기록 (항상)
    nickname = user.get("nickname", "Guest") if user else "Visitor"
    member_id = user.get("id") if user and not user.get("is_guest") else None
    log_access(member_id, nickname, role, "Main App")

    if not user:
        _render_landing()
    else:
        _render_sidebar()
        _render_home(user, role)


if __name__ == "__main__" or True:
    main()
