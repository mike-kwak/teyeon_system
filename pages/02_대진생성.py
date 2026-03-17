"""
pages/02_대진생성.py
────────────────────
KDK 대진 생성 (운영진 전용).
- 카카오 밴드 API로 참석자 불러오기
- 4인 1조 매칭 + 특정 파트너 지정
- 대진표 미리보기 및 세션 저장
"""

import streamlit as st
import os

st.set_page_config(page_title="대진 생성 | TEYEON", page_icon="⚙️", layout="wide")

# ── 로그인 + 운영진 가드 ──────────────────────────────────────────────────
if not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.stop()
if not st.session_state.get("is_admin"):
    st.error("운영진만 접근 가능한 페이지입니다.")
    st.stop()

CLUB_ID = os.environ.get("CLUB_ID", "")

st.markdown("## ⚙️ KDK 대진 생성")
st.caption("밴드 참석자 정보를 불러와 자동으로 대진표를 생성합니다.")

# ── Step 1: 참석자 불러오기 ───────────────────────────────────────────────
st.markdown("### Step 1 · 참석자 확인")
with st.expander("카카오 밴드에서 참석자 불러오기", expanded=True):
    if st.button("📡 밴드 참석자 불러오기"):
        st.info("🚧 밴드 API 연동은 다음 단계에서 구현됩니다.")
        # TODO: core_logic/band_api.py 구현 후 연동
    
    st.markdown("또는 **직접 입력**:")
    attendees_text = st.text_area(
        "참석자 이름 (줄바꿈 구분, 게스트는 이름 뒤에 '(게스트)' 추가)",
        placeholder="홍길동\n김철수\n이영희(게스트)\n박민준",
        height=150,
    )

st.divider()

# ── Step 2: 파트너 지정 ───────────────────────────────────────────────────
st.markdown("### Step 2 · 특정 파트너 지정 (선택)")
partner_text = st.text_area(
    "파트너로 묶을 쌍 (줄바꿈 구분, 쉼표로 구분)",
    placeholder="홍길동, 김철수\n이영희, 박민준",
    height=80,
)

st.divider()

# ── Step 3: 대진 생성 ─────────────────────────────────────────────────────
st.markdown("### Step 3 · 대진표 생성")
col1, col2 = st.columns(2)
with col1:
    session_date = st.date_input("경기 날짜")
with col2:
    note = st.text_input("비고 (예: 2월 정기 KDK)")

if st.button("🎾 대진표 자동 생성", type="primary", use_container_width=True):
    st.info("🚧 KDK 엔진(core_logic/kdk_engine.py) 구현 후 활성화됩니다.")
    # TODO: kdk_engine.generate_matches(attendees, forced_pairs) 호출

st.divider()

# ── Step 4: 대진표 미리보기 & 저장 ───────────────────────────────────────
st.markdown("### Step 4 · 저장")
st.info("대진표 생성 후 이 영역에 코트별 배정이 표시됩니다.")
if st.button("💾 세션 저장 및 시작", disabled=True):
    pass  # TODO
