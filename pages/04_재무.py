"""
pages/04_재무.py
─────────────────
재무 관리 (운영진 전용).
- 수입/지출 내역 조회
- 수동 재무 레코드 입력
- 잔액 현황
"""

import streamlit as st
import pandas as pd
import os
from db.supabase_client import get_finance_records, insert_finance_record, check_auth_and_log

st.set_page_config(page_title="재무 관리 | TEYEON", page_icon="💰", layout="wide")

# ── 권한 체크 및 로그 기록 ────────────────────────────────────────────────────────
check_auth_and_log("04_재무.py")

CLUB_ID = os.environ.get("CLUB_ID", "")
user    = st.session_state["user"]

st.markdown("## 💰 재무 관리")

# ── 잔액 요약 ─────────────────────────────────────────────────────────────
st.markdown("### 📊 잔액 현황")
try:
    records = get_finance_records(CLUB_ID, limit=200)
    total   = sum(r["amount"] for r in records)
    income  = sum(r["amount"] for r in records if r["amount"] > 0)
    expense = sum(r["amount"] for r in records if r["amount"] < 0)

    st.markdown("""
    <div style="background: rgba(204, 255, 0, 0.05); padding: 25px; border-radius: 20px; border: 1px solid rgba(204, 255, 0, 0.2); margin-bottom: 25px;">
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div><div style="font-size: 0.8rem; color: #aab8d4;">총 잔액</div><div style="font-size: 1.8rem; font-weight: 900; color: #CCFF00;">{:,.0f}원</div></div>
            <div><div style="font-size: 0.8rem; color: #aab8d4;">총 수입</div><div style="font-size: 1.8rem; font-weight: 900; color: #ffffff;">{:,.0f}원</div></div>
            <div><div style="font-size: 0.8rem; color: #aab8d4;">총 지출</div><div style="font-size: 1.8rem; font-weight: 900; color: #ff4b4b;">{:,.0f}원</div></div>
        </div>
    </div>
    """.format(total, income, expense), unsafe_allow_html=True)
except Exception as e:
    st.error(f"조회 오류: {e}")
    records = []

st.divider()

# ── 내역 테이블 ───────────────────────────────────────────────────────────
st.markdown("### 📋 수입/지출 내역")
if records:
    df = pd.DataFrame(records)[["recorded_at", "type", "amount", "description"]]
    df.columns  = ["일시", "유형", "금액(원)", "설명"]
    df["금액(원)"] = df["금액(원)"].apply(lambda x: f"+{x:,}" if x >= 0 else f"{x:,}")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("재무 내역이 없습니다.")

st.divider()

# ── 수동 입력 ─────────────────────────────────────────────────────────────
st.markdown("### ➕ 수동 레코드 입력")
with st.form("finance_form"):
    col1, col2 = st.columns(2)
    with col1:
        fin_type = st.selectbox("유형", ["manual", "reward", "penalty"])
        amount   = st.number_input("금액 (원, 지출은 음수 입력)", value=0, step=1000)
    with col2:
        desc     = st.text_input("설명")
    submitted = st.form_submit_button("저장", type="primary")
    if submitted:
        if not desc:
            st.warning("설명을 입력해주세요.")
        else:
            try:
                insert_finance_record(
                    club_id=CLUB_ID, type_=fin_type, amount=int(amount),
                    description=desc, created_by=user["id"],
                )
                st.success("저장되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")
