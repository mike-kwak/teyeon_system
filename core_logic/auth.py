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

KAKAO_CLIENT_ID   = os.environ.get("KAKAO_CLIENT_ID", "")
KAKAO_REDIRECT_URI = os.environ.get("KAKAO_REDIRECT_URI", "http://localhost:8501")

# ── 카카오 API 엔드포인트 ─────────────────────────────────────────────────
_KAKAO_AUTH_BASE  = "https://kauth.kakao.com/oauth/authorize"
_KAKAO_TOKEN_URL  = "https://kauth.kakao.com/oauth/token"
_KAKAO_USER_URL   = "https://kapi.kakao.com/v2/user/me"


def get_kakao_auth_url() -> str:
    """카카오 로그인 인가 URL 생성. 버튼 href로 사용."""
    params = (
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return _KAKAO_AUTH_BASE + params


def exchange_code_for_token(code: str) -> dict:
    """
    인가 코드(code)를 access_token으로 교환.
    반환: {"access_token": ..., "refresh_token": ..., ...}
    실패 시 빈 dict 반환.
    """
    payload = {
        "grant_type":   "authorization_code",
        "client_id":    KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code":         code,
    }
    try:
        res = requests.post(_KAKAO_TOKEN_URL, data=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"[auth] 토큰 교환 실패: {e}")
        return {}


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
            "kakao_id":     raw.get("id"),
            "nickname":     profile.get("nickname", ""),
            "profile_image": profile.get("profile_image_url"),
            "email":        kakao_account.get("email"),
        }
    except requests.RequestException as e:
        print(f"[auth] 사용자 정보 조회 실패: {e}")
        return {}


def logout(session_state) -> None:
    """st.session_state에서 인증 정보 제거."""
    for key in ("user", "access_token", "is_admin"):
        session_state.pop(key, None)
