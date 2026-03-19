import streamlit as st
from datetime import datetime, timedelta
from core_logic.kdk_engine import get_rankings_v2
import pandas as pd

st.set_page_config(page_title="경기 진행 | TEYEON", page_icon="🎾", layout="wide")

# ── 100% 이미지 싱크 CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
.kdk-table {
    width: 100%; border-collapse: collapse; background-color: white; color: black; font-family: 'Malgun Gothic', 'Dotum', sans-serif;
}
.kdk-table th {
    background-color: #fff9db; border: 1px solid #444; padding: 10px; font-weight: bold; text-align: center; font-size: 1.1rem;
}
.kdk-table td {
    border: 1px solid #444; padding: 8px; text-align: center; vertical-align: middle; font-size: 1rem; font-weight: 500;
}
.kdk-table .vs-cell { color: #999; font-weight: normal; font-size: 0.9rem; }
.kdk-table .seq-cell { background-color: white; }
.kdk-table .time-cell { font-weight: bold; font-size: 1.1rem; }
.kdk-table .court-cell { color: #555; font-size: 0.9rem; font-family: monospace; }
/* 모바일 스크롤 */
.table-wrapper { overflow-x: auto; margin-bottom: 20px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

if "kdk_all_data" not in st.session_state:
    st.warning("먼저 '대진 생성' 페이지에서 대진표를 생성해주세요.")
    st.stop()

d = st.session_state.kdk_all_data
matches = d["matches"]
players = d["players"]
groups = d["groups"]
start_time_str = d.get("start_time", "19:30")
duration = d.get("duration", 30)

def get_time_slot(rd):
    st_dt = datetime.strptime(start_time_str, "%H:%M")
    s = st_dt + timedelta(minutes=(rd-1)*duration)
    return s.strftime('%H:%M')

st.markdown("## 📊 KDK 정밀 대진표 (이미지 방식)")

tab_board, tab_rank = st.tabs(["🎾 정밀 대진표", "🏆 실시간 순위"])

with tab_board:
    for g in groups:
        rules_text = d.get("match_rules", "(모든 게임 1:1 시작, 노에드, 5:5 타이 7포인트 선승)")
        st.markdown(f"#### 📍 {g}조 대진표 <small style='color:#666; font-weight:normal;'>{rules_text}</small>", unsafe_allow_html=True)
        
        g_ms = [m for m in matches if m["group"] == g]
        g_ms.sort(key=lambda x: (x["round"], x["court"]))
        
        # ── HTML 테이블 생성 시작 ────────────────
        html = f"""
        <div class="table-wrapper">
        <table class="kdk-table">
            <thead>
                <tr>
                    <th colspan="2">순서</th>
                    <th colspan="2">이름</th>
                    <th>VS</th>
                    <th colspan="2">이름</th>
                    <th>시간</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # 라운드별로 루프를 돌며 rowspan 처리
        rounds_list = sorted(list(set(m["round"] for m in g_ms)))
        global_seq = 1
        
        for r in rounds_list:
            r_ms = [m for m in g_ms if m["round"] == r]
            r_span = len(r_ms)
            t_slot = get_time_slot(r)
            
            for i, m in enumerate(r_ms):
                html += "<tr>"
                # 순서/코트
                html += f"<td class='seq-cell' width='5%'>{global_seq}</td>"
                html += f"<td class='court-cell' width='8%'>{m['court']}코트</td>"
                
                # 팀 1 (선수 분리 + 고정 회차 표시)
                p1_name = m['team1'][0]
                p2_name = m['team1'][1]
                if m.get('pair_round'):
                    p1_name += f"({m['pair_round']})"
                    p2_name += f"({m['pair_round']})"
                html += f"<td width='15%'>{p1_name}</td>"
                html += f"<td width='15%'>{p2_name}</td>"
                
                # VS (첫 매치에서만 혹은 매번 표시)
                html += f"<td class='vs-cell' width='8%'>VS</td>"
                
                # 팀 2 (선수 분리)
                html += f"<td width='15%'>{m['team2'][0]}</td>"
                html += f"<td width='15%'>{m['team2'][1]}</td>"
                
                # 시간 (Rowspan 적용)
                if i == 0:
                    html += f"<td rowspan='{r_span}' class='time-cell' width='12%'>{t_slot}</td>"
                
                html += "</tr>"
                global_seq += 1
        
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)

        # ── 결과 입력창 (사용성 위해 하단 배치) ──────────────
        st.markdown(f"#### 📝 {g}조 결과 입력")
        with st.expander(f"{g}조 스코어 기록 열기"):
            for m in g_ms:
                real_idx = matches.index(m)
                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
                with c1: st.write(f"**{m['round']}R {m['court']}코트**")
                with c2: s1 = st.number_input(f"{'&'.join(m['team1'])}", 0, 10, m['score1'], key=f"s1_{g}_{real_idx}")
                with c3: s2 = st.number_input(f"{'&'.join(m['team2'])}", 0, 10, m['score2'], key=f"s2_{g}_{real_idx}")
                with c4:
                    if st.button("저장", key=f"sv_{g}_{real_idx}"):
                        m["score1"], m["score2"] = s1, s2
                        m["status"] = "complete"
                        st.rerun()
        st.write("---")

    # ── 카톡 공유 ──────────────────
    st.markdown("### 💬 카톡 공유용 텍스트")
    share_text = f"🎾 테연 대진표 ({datetime.now().strftime('%m/%d')})\n"
    for r in sorted(list(set(m["round"] for m in matches))):
        share_text += f"\n[{get_time_slot(r)}]\n"
        for m in [m for m in matches if m["round"] == r]:
            status = f" ({m['score1']}:{m['score2']})" if m["status"]=="complete" else ""
            share_text += f"{m['court']}코트: [{' & '.join(m['team1'])}] vs [{' & '.join(m['team2'])}]{status}\n"
    st.info("결과 화면을 캡처하거나 아래 텍스트를 복사하세요.")
    st.code(share_text)

with tab_rank:
    r_dict = get_rankings_v2(matches, players)
    import math

    for g in groups:
        st.markdown(f"### 🏆 {g}조 실시간 순위 및 정산")
        if g in r_dict:
            results_g = r_dict[g]
            N = len(results_g)
            p_count = math.ceil(N / 2)
            five_k_count = p_count // 2
            three_k_count = p_count - five_k_count
            
            # 벌금 및 상금 계산 로직 적용
            for i, p in enumerate(results_g):
                rank = i + 1
                p["상벌금"] = 0
                p["비고"] = ""
                
                # 상금 (1등)
                if rank == 1:
                    if not p.get("is_guest"):
                        p["상벌금"] = 10000
                        p["비고"] = "👑 1등 상금"
                    else:
                        p["비고"] = "🎗️ 1등 (게스트 제외)"
                
                # 벌금 (하위 50%)
                penalty_idx_start = N - p_count
                if i >= penalty_idx_start:
                    # 하위 50% 중에서도 더 못하면 5000원
                    # 예: 11명 -> 6명 벌금. 6,7,8등(3k), 9,10,11등(5k)
                    if i >= N - five_k_count:
                        p["상벌금"] = -5000
                        p["비고"] = "❗ 벌금 대상 (5,000)"
                    else:
                        p["상벌금"] = -3000
                        p["비고"] = "❗ 벌금 대상 (3,000)"

            df = pd.DataFrame(results_g)
            
            # 가독성을 위한 컬럼 정리 (생년월일 등 숨김)
            display_df = df[["순위", "이름", "승", "패", "득실차", "경기수", "비고"]].copy()
            
            # 스타일링: 벌금 대상자 빨간색 강조
            def highlight_penalty(row):
                if "벌금" in str(row["비고"]):
                    return ['background-color: #ffe3e3'] * len(row)
                if "상금" in str(row["비고"]):
                    return ['background-color: #e3f2fd'] * len(row)
                return [''] * len(row)

            st.dataframe(display_df.style.apply(highlight_penalty, axis=1), hide_index=True, use_container_width=True)
            
            # 총 벌금 합계
            total_penalty = abs(sum(p["상벌금"] for p in results_g if p["상벌금"] < 0))
            st.markdown(f"""
            <div style="background: rgba(255, 75, 75, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; text-align: center; margin-top: 10px;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #ff4b4b;">오늘의 {g}조 총 예상 벌금 합계:</span>
                <span style="font-size: 1.8rem; font-weight: 900; color: #ff4b4b; margin-left: 10px;">{total_penalty:,}원</span>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
