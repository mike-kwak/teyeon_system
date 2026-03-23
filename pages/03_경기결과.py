import streamlit as st
import os
import pandas as pd
from datetime import datetime
from db.supabase_client import (
    get_kdk_sessions, get_kdk_session, check_auth_and_log,
    upsert_kdk_results, add_ranking_points, insert_finance_record,
    update_kdk_session_status, get_all_members
)
from core_logic.kdk_engine import get_rankings_v3, calculate_rewards_v2

st.set_page_config(page_title="경기 결과 | TEYEON", page_icon="📝", layout="wide")

# ── 권한 체크 및 로그 기록 ────────────────────────────────────────────────────────
check_auth_and_log("03_경기결과.py")

CLUB_ID = os.environ.get("CLUB_ID", "")
user = st.session_state.get("user", {})
role = st.session_state.get("role", "Member")
is_admin = role in ("CEO", "Staff")

st.markdown("## 📝 경기 결과 및 확정")

# ── 세션 선택 ─────────────────────────────────────────────────────────────
try:
    sessions = get_kdk_sessions(CLUB_ID, limit=20)
    session_labels = {s["id"]: f"[{s['status'].upper()}] {s['session_date']} — {s.get('note','')}" for s in sessions}
except Exception:
    session_labels = {}

if not session_labels:
    st.info("진행된 세션이 없습니다.")
    st.stop()

selected_id = st.selectbox("세션 선택", options=list(session_labels.keys()),
                            format_func=lambda x: session_labels[x])

st.divider()

# ── 데이터 로드 ────────────────────────────────────────────────────────────
session_data = get_kdk_session(selected_id)
if not session_data:
    st.error("세션 데이터를 불러오지 못했습니다.")
    st.stop()

matches = session_data.get("kdk_matches", [])
if not matches:
    st.warning("이 세션에 등록된 매치가 없습니다.")
    st.stop()

# ── 랭킹 계산 준비 ──────────────────────────────────────────────────────────
# 1. 플레이어 정보 수집 (birthdate, is_guest 등 정밀 순위용)
all_members = get_all_members(CLUB_ID)
member_map = {m["nickname"]: m for m in all_members}

# 매치에 참여한 모든 고유 이름 추출
player_names = set()
for m in matches:
    player_names.update(m["team1"])
    player_names.update(m["team2"])

players_info = []
for name in player_names:
    m_info = member_map.get(name, {})
    players_info.append({
        "name": name,
        "birthdate": m_info.get("birthdate", "1900-01-01"),
        "is_guest": (m_info.get("kakao_id") or 0) < 0 or name.startswith("Guest") or m_info.get("is_guest") == True
    })

# 2. 랭킹 계산
overall_rank, group_rank_dict = get_rankings_v3(matches, players_info)

# 3. 상벌금 계산 (award_config 반영)
award_config = session_data.get("award_config", {
    "reward_1st": 10000,
    "fine_25": 3000,
    "fine_last_25": 5000
})
fines, rewards = calculate_rewards_v2(
    overall_rank, 
    reward_1st=award_config.get("reward_1st", 10000),
    fine_25=award_config.get("fine_25", 3000),
    fine_last_25=award_config.get("fine_last_25", 5000)
)

# ── 결과 요약 표시 ─────────────────────────────────────────────────────────
st.subheader("🏆 최종 순위 및 정산")
status_color = "#CCFF00" if session_data["status"] == "completed" else "#ff4b4b"
st.markdown(f"상태: <span style='color:{status_color}; font-weight:bold;'>{session_data['status'].upper()}</span>", unsafe_allow_html=True)

res_data = []
for r in overall_rank:
    name = r["이름"]
    amt = rewards.get(name, 0) - fines.get(name, 0)
    note = ""
    if name in rewards: note = f"👑 1등 상금 (+{rewards[name]:,})"
    elif name in fines: note = f"❗ 벌금 (-{fines[name]:,})"
    res_data.append({
        "순위": r["순위"], "이름": name, "승": r["승"], "패": r["패"], 
        "득실차": r["득실차"], "경기수": r["경기수"], "정산액": f"{amt:,}원", "비고": note
    })
df_display = pd.DataFrame(res_data)
st.dataframe(
    df_display.style.set_properties(**{'text-align': 'center'}),
    use_container_width=True, 
    hide_index=True
)

if fines:
    st.markdown("#### 💸 벌금 입금 계좌")
    st.code(award_config.get("account_number", "카카오뱅크 곽민섭 3333-01-5235337"), language=None)


# ── 결과 확정 버튼 (운영진 전용) ─────────────────────────────────────────────
if is_admin and session_data["status"] != "completed":
    st.divider()
    st.warning("⚠️ 결과를 확정하면 하이라이트 포인트와 상벌금 기록이 DB에 정식으로 등록됩니다.")
    
    confirm_final = st.checkbox("모든 결과를 확인했으며, 저장을 확정합니다.", key="confirm_final")
    
    if st.button("🚀 결과 최종 확정 및 기록 저장", type="primary", use_container_width=True, disabled=not confirm_final):
        with st.spinner("결과 기록 중..."):
            try:
                # 1. kdk_results 저장
                db_results = []
                for r in overall_rank:
                    name = r["이름"]
                    m_id = member_map.get(name, {}).get("id")
                    if m_id:
                        db_results.append({
                            "session_id": selected_id,
                            "member_id": m_id,
                            "wins": r["승"],
                            "losses": r["패"],
                            "points_diff": r["득실차"],
                            "rank": r["순위"],
                            "reward": rewards.get(name, 0) - fines.get(name, 0)
                        })
                if db_results:
                    upsert_kdk_results(db_results)

                # 2. 포인트 및 재무 기록 (상금/벌금)
                user_id = user.get("id")
                for r in overall_rank:
                    name = r["이름"]
                    m_id = member_map.get(name, {}).get("id")
                    if not m_id: continue

                    # 포인트 부여 (승점당 10점 + 참가 10점 예시)
                    points = (r["승"] * 10) + 10
                    add_ranking_points(CLUB_ID, m_id, points, f"KDK 세션 참여 ({r['승']}승)", session_id=selected_id)

                    # 재무 기록 (상금)
                    if name in rewards:
                        insert_finance_record(CLUB_ID, "reward", -rewards[name], f"KDK 1등 상금 지급 ({name})", user_id, session_id=selected_id, member_id=m_id)
                    # 재무 기록 (벌금)
                    if name in fines:
                        insert_finance_record(CLUB_ID, "penalty", fines[name], f"KDK 벌금 납부 ({name})", user_id, session_id=selected_id, member_id=m_id)

                # 3. 세션 상태 업데이트
                update_kdk_session_status(selected_id, "completed")
                
                st.success("✅ 모든 결과가 성공적으로 기록되었습니다!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 확정 중 오류 발생: {e}")

# ── 카카오톡 공유용 텍스트 생성 ─────────────────────────────────────────────
st.divider()
st.subheader("💬 카카오톡 공유용 텍스트")

share_date = datetime.strptime(session_data["session_date"], "%Y-%m-%d").strftime("%m/%d")
share_text = f"🎾 TEYEON KDK 결과 ({share_date})\n"
share_text += "━━━━━━━━━━━━━━━━━━━\n"

for i, r in enumerate(overall_rank[:5]): # 상위 5명
    medal = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else "🔹"
    reward_str = f" 💰+{rewards[r['이름']]:,}" if r['이름'] in rewards else ""
    share_text += f"{medal} {r['순위']}위 {r['이름']} — {r['승']}승 {r['패']}패 ({r['득실차']:+}){reward_str}\n"

share_text += "...\n"
share_text += "━━━━━━━━━━━━━━━━━━━\n"
share_text += "💸 상벌금 내역\n"

fine_items = []
for name, amt in fines.items():
    fine_items.append(f"{name}({amt//1000}k)")
share_text += " / ".join(fine_items)
share_text += "\n\n입금 계좌: " + award_config.get("account_number", "카카오뱅크 곽민섭 3333-01-5235337")
share_text += "\n━━━━━━━━━━━━━━━━━━━\n"
share_text += "모두 수고하셨습니다! 🎾"

st.text_area("공유 텍스트 (복사해서 사용하세요)", value=share_text, height=300)
if st.button("📋 복사 안내"):
    st.info("위 텍스트 박스의 내용을 드래그하여 복사해 주세요.")
