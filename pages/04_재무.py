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
from db.supabase_client import get_finance_records, insert_finance_record

st.set_page_config(page_title="재무 관리 | TEYEON", page_icon="💰", layout="wide")

if not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.stop()
if not st.session_state.get("is_admin"):
    st.error("운영진만 접근 가능한 페이지입니다.")
    st.stop()

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

    col1, col2, col3 = st.columns(3)
    col1.metric("총 잔액", f"{total:,}원",   delta=None)
    col2.metric("총 수입", f"{income:,}원",  delta=None)
    col3.metric("총 지출", f"{expense:,}원", delta=None)
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
