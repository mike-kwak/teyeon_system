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
from db.supabase_client import upsert_member, get_member_by_kakao_id

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
/* 전체 배경 */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

/* 카카오 로그인 버튼 */
.kakao-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background-color: #FEE500;
    color: #000000 !important;
    font-weight: 700;
    font-size: 16px;
    padding: 14px 28px;
    border-radius: 12px;
    text-decoration: none !important;
    box-shadow: 0 4px 15px rgba(254,229,0,0.3);
    transition: all 0.2s ease;
    cursor: pointer;
}
.kakao-btn:hover {
    background-color: #ffe033;
    box-shadow: 0 6px 20px rgba(254,229,0,0.5);
    transform: translateY(-2px);
}

/* 로고 텍스트 */
.logo-title {
    font-size: 3.5rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    background: linear-gradient(90deg, #FEE500, #ffc107);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
}

.logo-subtitle {
    color: #aab8d4;
    text-align: center;
    font-size: 1.05rem;
    letter-spacing: 0.08em;
    margin-bottom: 2.5rem;
}

/* 사이드바 프로필 */
.sidebar-profile {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    margin-bottom: 8px;
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

        # URL 정리 (code 파라미터 제거)
        st.query_params.clear()
        st.rerun()


# ── 랜딩 페이지 (비로그인) ────────────────────────────────────────────────
def _render_landing():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="logo-title">🎾 TEYEON</div>', unsafe_allow_html=True)
        st.markdown('<div class="logo-subtitle">테니스 클럽 스마트 매니저</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### ✨ 주요 기능")
        features = [
            ("🏸", "KDK 대진 자동 생성", "4인 1조 매칭, 특정 파트너 지정 반영"),
            ("💰", "상벌금 자동 계산",   "승패·득실차 기반 동적 분배"),
            ("📊", "기간별 랭킹",        "주·월·년 단위 포인트 대시보드"),
            ("📋", "카카오톡 공유",      "결과를 한 번에 복사·공유"),
        ]
        for icon, title, desc in features:
            st.markdown(f"**{icon} {title}** — {desc}")

        st.markdown("---")
        auth_url = get_kakao_auth_url()
        st.markdown(
            f'<a href="{auth_url}" class="kakao-btn">'
            f'<span style="font-size:1.3em;">💬</span> 카카오로 시작하기'
            f'</a>',
            unsafe_allow_html=True,
        )
        st.caption("카카오 계정으로 1초 로그인 · 별도 회원가입 불필요")


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

        # 메뉴 (st.page_link는 pages/ 파일명 기반으로 자동 생성됨)
        st.markdown("#### 📋 메뉴")
        st.page_link("pages/01_대시보드.py",  label="🏠 대시보드")
        st.page_link("pages/03_경기결과.py",  label="📝 경기 결과")
        st.page_link("pages/05_랭킹.py",      label="🏆 랭킹")
        st.page_link("pages/06_시드예측.py",   label="🔮 시드 예측")
        st.page_link("pages/07_멤버정보.py",   label="👥 멤버 정보")

        # 운영진 전용 메뉴
        if is_admin:
            st.markdown("#### 🔐 운영진 메뉴")
            st.page_link("pages/02_대진생성.py", label="⚙️ 대진 생성")
            st.page_link("pages/04_재무.py",     label="💰 재무 관리")
            st.page_link("pages/08_멤버관리.py", label="📝 멤버 관리")

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
