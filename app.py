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
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.markdown("""
        <div class="logo-container">
            <div class="teyeon-logo">
                <div class="tennis-ball-icon">
                    <svg viewBox="0 0 100 100" width="100" height="100">
                        <circle cx="50" cy="50" r="48" fill="#FEE500" />
                        <path d="M25,20 Q50,50 25,80" fill="none" stroke="#666" stroke-width="2.5" />
                        <path d="M75,20 Q50,50 75,80" fill="none" stroke="#666" stroke-width="2.5" />
                    </svg>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-start;">
                    <div class="logo-main-text">테연</div>
                    <div class="logo-sub-text">테니스</div>
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
        # 기본 홈 콘텐츠 (페이지 이동 전 진입 시 표시)
        st.markdown("## 🏠 홈")
        st.info("왼쪽 사이드바에서 메뉴를 선택하세요.")
        st.markdown(f"환영합니다, **{user.get('nickname', '회원')}** 님! 🎾")


if __name__ == "__main__" or True:
    main()
