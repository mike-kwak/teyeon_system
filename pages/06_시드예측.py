"""
pages/06_시드예측.py
─────────────────────
KATO 엑셀 업로드 → 회원 2명 포인트 합산 → 예상 복식 시드 계산.
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="시드 예측 | TEYEON", page_icon="🔮", layout="wide")

if not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.stop()

st.markdown("## 🔮 KATO 시드 예측")
st.caption("KATO 공식 엑셀 파일을 업로드하면 2인 복식 예상 시드를 계산합니다.")

# ── 파일 업로드 ───────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "KATO 엑셀 파일 업로드 (.xlsx / .xls)",
    type=["xlsx", "xls"],
    help="KATO 홈페이지에서 다운로드한 랭킹 엑셀 파일을 업로드하세요.",
)

if uploaded:
    try:
        df_raw = pd.read_excel(uploaded)
        st.success(f"파일 로드 완료: {len(df_raw)}개 행")
        st.markdown("#### 원본 데이터 미리보기")
        st.dataframe(df_raw.head(10), use_container_width=True)

        # TODO: core_logic/kato_parser.py 구현 후 실제 파싱 연동
        st.info("🚧 KATO 파서(core_logic/kato_parser.py) 구현 후 자동 파싱됩니다.")

        st.divider()

        # ── 수동 선택으로 시드 계산 (파서 전 임시) ───────────────────────
        st.markdown("### 🎾 파트너 선택")
        col1, col2 = st.columns(2)
        with col1:
            p1_name = st.text_input("선수 1 이름 (KATO 등록명과 동일하게)")
        with col2:
            p2_name = st.text_input("선수 2 이름")

        if st.button("시드 계산", type="primary"):
            if not p1_name or not p2_name:
                st.warning("두 선수 이름을 모두 입력해주세요.")
            else:
                st.info("🚧 파서 구현 후 실제 포인트 합산을 보여줍니다.")

    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")
else:
    st.info("👆 KATO 엑셀 파일을 업로드하세요.")

    with st.expander("💡 사용 방법"):
        st.markdown("""
1. [KATO 홈페이지](https://www.kato.or.kr) → 랭킹 페이지에서 엑셀 다운로드
2. 위 업로드 버튼으로 파일 선택
3. 파트너로 출전할 두 선수 이름 입력
4. `시드 계산` 버튼 클릭 → 합산 포인트 & 예상 시드 확인
        """)
