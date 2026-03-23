"""
core_logic/auth.py
──────────────────
카카오 OAuth 2.0 인증 흐름 처리.

흐름:
  1. get_kakao_auth_url()  → 사용자를 카카오 인가 URL로 안내
  2. exchange_code_for_token(code) → access_token 획득
  3. get_kakao_user_info(token)    → 사용자 정보 조회
  4. app.py에서 Supabase upsert 후 st.session_state에 저장
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── 카카오 API 엔드포인트 ─────────────────────────────────────────────────
_KAKAO_AUTH_BASE  = "https://kauth.kakao.com/oauth/authorize"
_KAKAO_TOKEN_URL  = "https://kauth.kakao.com/oauth/token"
_KAKAO_USER_URL   = "https://kapi.kakao.com/v2/user/me"


def _get_secret(key: str, default: str = "") -> str:
    """st.secrets → os.environ 순서로 값을 읽습니다.
    ⚠️ 반드시 함수 내부에서만 호출 (모듈 로드 시점에 st가 미초기화 상태일 수 있음).
    """
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(key, default)


def get_kakao_auth_url() -> str:
    """카카오 로그인 인가 URL 생성. 버튼 href로 사용."""
    client_id    = _get_secret("KAKAO_CLIENT_ID")
    redirect_uri = _get_secret("KAKAO_REDIRECT_URI", "http://localhost:8501")
    params = (
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )
    return _KAKAO_AUTH_BASE + params


def exchange_code_for_token(code: str) -> dict:
    """
    인가 코드(code)를 access_token으로 교환.
    반환: {"access_token": ..., "refresh_token": ..., ...}
    실패 시 빈 dict 반환.
    """
    client_id     = _get_secret("KAKAO_CLIENT_ID")
    client_secret = _get_secret("KAKAO_CLIENT_SECRET")
    redirect_uri  = _get_secret("KAKAO_REDIRECT_URI", "http://localhost:8501")

    payload = {
        "grant_type":   "authorization_code",
        "client_id":    client_id,
        "redirect_uri": redirect_uri,
        "code":         code,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    try:
        res = requests.post(_KAKAO_TOKEN_URL, data=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        err_msg = e.response.text if e.response is not None else str(e)
        print(f"[auth] 토큰 교환 실패: {err_msg}")
        return {"error": err_msg}


def get_kakao_user_info(access_token: str) -> dict:
    """
    access_token으로 카카오 사용자 정보 조회.
    반환: {
        "kakao_id": int,
        "nickname": str,
        "profile_image": str | None,
        "email": str | None,
    }
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get(_KAKAO_USER_URL, headers=headers, timeout=10)
        res.raise_for_status()
        raw = res.json()

        kakao_account = raw.get("kakao_account", {})
        profile       = kakao_account.get("profile", {})

        return {
            "kakao_id":      raw.get("id"),
            "nickname":      profile.get("nickname", ""),
            "profile_image": profile.get("profile_image_url"),
            "email":         kakao_account.get("email"),
        }
    except requests.RequestException as e:
        print(f"[auth] 사용자 정보 조회 실패: {e}")
        return {}


def logout(session_state) -> None:
    """st.session_state에서 인증 정보 제거."""
    for key in ("user", "access_token", "is_admin", "role"):
        session_state.pop(key, None)

import streamlit as st
import extra_streamlit_components as stx

@st.cache_resource
def get_manager():
    return stx.CookieManager(key="cookie_manager")
