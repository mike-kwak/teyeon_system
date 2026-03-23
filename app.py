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
import extra_streamlit_components as stx

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

/* 📱 모바일 강제 세로 정렬(Stacking) 절대 방어 (Nuclear CSS) */
@media (max-width: 768px) {
    /* 컨테이너를 무조건 가로(row)로 유지하고 줄바꿈(wrap) 허용 */
    div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        align-items: stretch !important;
        gap: 5px !important; /* 버튼 사이 간격 */
    }
    /* 각 컬럼이 정확히 1/3(약 31%) 사이즈를 차지하도록 절대 고정 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 31% !important;
        flex: 1 1 31% !important;
        min-width: 31% !important;
        margin-bottom: 10px !important;
    }
    /* 모바일에서 버튼 안의 글자가 짤리지 않도록 폰트 크기 조정 */
    div[data-testid="stHorizontalBlock"] button {
        padding: 8px 4px !important;
        font-size: 11px !important; 
        height: auto !important;
    }
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

/* ── v4.0 GLOBAL MOBILE STACKING PREVENTION (DEFINITIVE) ── */
@media (max-width: 768px) {
    /* 모든 가로 블록은 무조건 가로(row) 유지 */
    div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
    }
    /* 가로 블록 안의 각 컬럼은 공평하게 너비 배분 */
    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
}

/* 버튼 타일 디자인 (v4.0) */
.icon-btn > div.stButton > button {
    width: 100% !important;
    aspect-ratio: 1 / 1 !important;
    border-radius: 18px !important;
    background: linear-gradient(145deg, rgba(35,45,70,0.95), rgba(20,28,48,0.98)) !important;
    border: 1px solid rgba(254,255,0,0.15) !important;
    color: #ffffff !important;
    font-size: 0.72rem !important; font-weight: 800 !important;
    display: flex !important; flex-direction: column !important;
    align-items: center !important; justify-content: center !important;
    padding: 8px 4px !important;
    transition: all 0.2s ease !important;
}
.icon-btn > div.stButton > button p::first-line { font-size: 2.1rem !important; }

/* ── Action Tower Profile Card (Dark Premium) ── */
.at-profile-card {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, rgba(26,37,61,0.98), rgba(10,14,26,1)) !important;
    border: 1px solid rgba(204,255,0,0.3) !important;
    border-radius: 24px !important;
    padding: 18px 20px !important;
    margin-bottom: 25px !important;
    box-shadow: 0 12px 50px rgba(0,0,0,0.5) !important;
}
.at-profile-info { display: flex; align-items: center; gap: 15px; }
.at-avatar {
    width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
    border: 2px solid #CCFF00;
}
.at-avatar-init {
    width: 52px; height: 52px; border-radius: 50%;
    background: linear-gradient(135deg,#1a253d,#CCFF00 200%);
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 20px; color: #0A0E1A;
    border: 2px solid #CCFF00;
}
.at-name { font-weight: 900; font-size: 1.15rem; color: #fff !important; line-height: 1.2; }
.at-badge {
    display: inline-block; font-size: 0.7rem; font-weight: 700;
    padding: 2px 10px; border-radius: 30px; margin-top: 4px; border: 1px solid;
    background: rgba(255,255,255,0.05); color: #CCFF00; border-color: rgba(204,255,0,0.3);
}
.at-ceo-btn {
    background: linear-gradient(135deg,#CCFF00,#a8d400) !important;
    color: #0A0E1A !important; font-weight: 900 !important;
    font-size: 0.78rem !important; border: none !important;
    border-radius: 14px !important; padding: 10px 16px !important;
    cursor: pointer; white-space: nowrap; text-decoration: none;
    box-shadow: 0 4px 16px rgba(204,255,0,0.35);
}

/* ── 기타 보조 스타일 ── */
.sidebar-profile { background: rgba(255, 255, 255, 0.05); border-radius: 18px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }
.sidebar-profile img { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #FEE500; }
.feature-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 18px; padding: 20px; margin-bottom: 15px; transition: all 0.3s ease; }
.feature-card:hover { background: rgba(255, 255, 255, 0.06); border-color: #CCFF00; transform: translateX(5px); }

/* 스코어 입력창 가로 정렬 강제 */
div[data-testid="stHorizontalBlock"]:has(.score-stepper-row) { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; gap: 10px !important; }
div[data-testid="stHorizontalBlock"]:has(.score-stepper-row) > div[data-testid="column"] { width: auto !important; flex: 1 !important; }

/* 데스크톱 모바일 최적화 및 레거시 버튼 제거 */
header, footer, [data-testid="stHeader"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; width: 0 !important; display: none !important; }
@media (min-width: 768px) {
    [data-testid="collapsedControl"] { display: none !important; }
    button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
}
</style>
""", unsafe_allow_html=True)


# ── 세션 초기화 ───────────────────────────────────────────────────────────
def _init_session(cookie_manager=None):
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

    # ── 자동 로그인 (Cookie Check) ──
    if cookie_manager and not st.session_state.get("user") and not st.session_state.get("is_guest"):
        auth_cookie = cookie_manager.get(cookie="teyeon_auth")
        if auth_cookie and isinstance(auth_cookie, dict):
            # 쿠키에 유효한 정보가 있으면 세션 복구
            for k in ["user", "access_token", "kakao_id", "is_admin", "role"]:
                if k in auth_cookie:
                    st.session_state[k] = auth_cookie[k]


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
            if "KOE320" in str(token_data) or token_data.get("error_code") == "KOE320":
                # 이미 사용된 인가코드 (새로고침/뒤로가기 시 발생). 조용히 URL 비우고 리런
                st.query_params.clear()
                st.rerun()
            st.error(f"카카오 로그인에 실패했습니다. 상세: {token_data}")
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

        # 다음 런에 쿠키를 굽도록 플래그 설정
        st.session_state["needs_cookie_save"] = True

        st.query_params.clear()
        st.toast("✅ 로그인 성공! 대시보드로 이동합니다.")
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
def _render_sidebar(cookie_manager):
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
            cookie_manager.delete("teyeon_auth")
            st.query_params.clear()
            st.toast("👋 로그아웃 되었습니다.")
            
            # 쿠키 삭제 명령이 브라우저에 도달할 시간을 주고 새로고침
            import streamlit.components.v1 as components
            components.html("<script>setTimeout(function(){window.parent.location.reload();}, 600);</script>", height=0)


# ── Action Tower 홈 렌더링 ──────────────────────────────────────────────────
ROLE_LEVEL = {"CEO": 4, "Staff": 3, "Member": 2, "Guest": 1}
ROLE_LABELS = {
    "CEO":    ("👑 최고관리자", "#FFD700"),
    "Staff":  ("🔧 운영진",     "#CCFF00"),
    "Member": ("🎾 정회원",     "#60EFFF"),
    "Guest":  ("🔓 게스트",     "#aab8d4"),
}
HOME_MENU = [
    dict(id="members",    icon="👤", label="멤버 정보",   page="pages/07_멤버정보.py",  min_role="Member", coming_soon=False),
    dict(id="kdk",        icon="🎾", label="KDK 대진표",  page="pages/02_대진생성.py",  min_role="Staff",  coming_soon=False),
    dict(id="ranking",    icon="🏆", label="실시간 랭킹", page="pages/05_랭킹.py",      min_role="Member", coming_soon=False),
    dict(id="finance",    icon="💰", label="상벌금 현황", page="pages/04_재무.py",      min_role="Member", coming_soon=False),
    dict(id="tournament", icon="🏅", label="대회 모드",   page=None,                   min_role="Member", coming_soon=True),
    dict(id="community",  icon="💬", label="커뮤니티",    page="pages/04_재무.py",      min_role="Member", coming_soon=False),
]

def _render_home(user: dict, role: str):
    nickname    = user.get("nickname", "회원")
    profile_img = user.get("profile_image", "")
    initials    = nickname[:1] if nickname else "?"
    role_text, role_color = ROLE_LABELS.get(role, ("🔓 게스트", "#aab8d4"))

    def can_access(min_role):
        return ROLE_LEVEL.get(role, 1) >= ROLE_LEVEL.get(min_role, 2)

    # ── Action Tower ──
    st.markdown('<div class="at-grid-layout">', unsafe_allow_html=True)

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
            <div class="at-name">\u2b50 {nickname} 님 안녕하세요! <small style="font-size:0.6rem;opacity:0.5;">v3.8</small></div>
            <div class="at-badge">{role_text}</div>
        </div>
    </div>
    {ceo_btn}
</div>
<div class="at-grid-title" style="margin-bottom: 18px; color: #CCFF00; font-size: 0.85rem; padding-left: 5px;">\u26a1 \ube60\ub978 \uc774\ub3d9</div>
""", unsafe_allow_html=True)
    # ── v4.0 무적의 NON-STACKING 3열 컬럼 ──
    rows = [HOME_MENU[i:i+3] for i in range(0, len(HOME_MENU), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, item in zip(cols, row):
            locked = not can_access(item["min_role"])
            coming = item["coming_soon"]
            
            if coming:
                btn_class = "icon-btn icon-btn-coming"
                badge = " 🚧"
            elif locked:
                btn_class = "icon-btn icon-btn-locked"
                badge = " 🔒"
            else:
                btn_class = "icon-btn"
                badge = ""

            btn_label = f"{item['icon']}\n\n{item['label']}{badge}"
            with col:
                st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                if st.button(btn_label, key=f"home_v40_{item['id']}", use_container_width=True):
                    if coming:
                        st.toast("🚧 준비 중입니다.")
                    elif locked:
                        st.toast("🔒 정회원만 이용 가능한 메뉴입니다.")
                    elif item["page"]:
                        st.switch_page(item["page"])
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")


# ── 메인 진입점 ───────────────────────────────────────────────────────────
import extra_streamlit_components as stx

def main():
    params = st.query_params
    code = params.get("code")

    if code and not st.session_state.get("user"):
        # OAuth 로그인 진행 중 (쿠키매니저 컴포넌트 렌더링에 의한 st.rerun 쓰레드 중단 방지)
        _init_session(None)
        _handle_oauth_callback()
        return

    # 일반 실행 (로그인 상태이거나, 랜딩 페이지 렌더링 시)
    cookie_manager = stx.CookieManager(key="app_cookie_manager")
    _init_session(cookie_manager)

    # 방금 로그인이 완료되어 쿠키를 구워야 할 경우
    if st.session_state.get("needs_cookie_save"):
        from datetime import datetime, timedelta
        cookie_manager.set("teyeon_auth", {
            "user": st.session_state["user"],
            "access_token": st.session_state["access_token"],
            "kakao_id": st.session_state["kakao_id"],
            "is_admin": st.session_state["is_admin"],
            "role": st.session_state["role"]
        }, expires_at=datetime.now() + timedelta(days=30))
        del st.session_state["needs_cookie_save"]

    user = st.session_state.get("user")
    role = st.session_state.get("role", "Guest")

    # 접속 로그 기록 (항상)
    nickname = user.get("nickname", "Guest") if user else "Visitor"
    member_id = user.get("id") if user and not user.get("is_guest") else None
    log_access(member_id, nickname, role, "Main App")

    if not user:
        _render_landing()
    else:
        _render_sidebar(cookie_manager)
        _render_home(user, role)


if __name__ == "__main__" or True:
    main()
