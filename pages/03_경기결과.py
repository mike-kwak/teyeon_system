"""
pages/03_경기결과.py
────────────────────
경기 결과 입력 + 상벌금 확인 + 카카오톡 공유용 텍스트 생성.
"""

import streamlit as st
import os
from db.supabase_client import get_kdk_sessions, check_auth_and_log

st.set_page_config(page_title="경기 결과 | TEYEON", page_icon="📝", layout="wide")

# ── 권한 체크 및 로그 기록 ────────────────────────────────────────────────────────
check_auth_and_log("03_경기결과.py")

CLUB_ID  = os.environ.get("CLUB_ID", "")
role = st.session_state.get("role", "Member")
is_admin = role in ("CEO", "Staff")

st.markdown("## 📝 경기 결과")

# ── 세션 선택 ─────────────────────────────────────────────────────────────
try:
    sessions = get_kdk_sessions(CLUB_ID, limit=10)
    session_labels = {s["id"]: f"{s['session_date']} — {s.get('note','')}" for s in sessions}
except Exception:
    session_labels = {}

if not session_labels:
    st.info("진행된 세션이 없습니다.")
    st.stop()

selected_id = st.selectbox("세션 선택", options=list(session_labels.keys()),
                            format_func=lambda x: session_labels[x])

st.divider()

# ── 점수 입력 (운영진) ────────────────────────────────────────────────────
if is_admin:
    st.markdown("### ✏️ 점수 입력")
    st.info("🚧 경기 점수 입력 폼은 KDK 엔진 구현 후 활성화됩니다.")
    # TODO: 각 매치별 score_a, score_b 입력 → upsert_kdk_results()

    if st.button("✅ 결과 확정 및 상벌금 계산", type="primary"):
        st.info("🚧 kdk_engine.calculate_rewards() 구현 후 활성화됩니다.")

st.divider()

# ── 결과 요약 & 카카오톡 공유 ──────────────────────────────────────────────
st.markdown("### 🏆 결과 요약")
st.info("결과 확정 후 이 영역에 순위와 상벌금이 표시됩니다.")

st.markdown("### 💬 카카오톡 공유용 텍스트")
# 예시 텍스트 (실제 데이터 연동 전 미리보기용)
example_text = """🎾 TEYEON KDK 결과 (YYYY.MM.DD)
━━━━━━━━━━━━━━━━━━━
🥇 1위 홍길동 — 3승 0패 (+8) 💰+10,000원
🥈 2위 김철수 — 2승 1패 (+3)
🥉 3위 이영희 — 2승 1패 (+1)
...
━━━━━━━━━━━━━━━━━━━
💸 상벌금 내역
홍길동 +10,000 / 박민준 -3,000 / 최하위 -5,000
━━━━━━━━━━━━━━━━━━━
수고하셨습니다! 🎾"""

share_text = st.text_area("공유 텍스트 (결과 확정 후 자동 생성)", value=example_text, height=250)
if st.button("📋 클립보드에 복사"):
    st.code(share_text)
    st.success("위 텍스트를 선택해 복사하세요! (브라우저 보안 정책으로 자동 복사는 제한됩니다)")
