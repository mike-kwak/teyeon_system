"""
pages/01_대시보드.py
────────────────────────────────────────────
Action Tower Mobile UI + PC 대시보드
- 모바일: 프로필 카드 + 3×2 아이콘 그리드 + 권한별 잠금
- PC: 기존 헤더 + 퀵 메뉴 + KPI 카드
"""

import streamlit as st
from datetime import datetime, timezone
from db.supabase_client import check_auth_and_log, get_tournament_results
import os

st.set_page_config(page_title="홈 | TEYEON", page_icon="🏠", layout="wide")
check_auth_and_log("01_대시보드.py")

# ── 권한 헬퍼 ──────────────────────────────────────────────────────────────
ROLE_LEVEL = {"CEO": 4, "Staff": 3, "Member": 2, "Guest": 1}

def get_role() -> str:
    return st.session_state.get("user", {}).get("role", "Guest")

def can_access(min_role: str) -> bool:
    return ROLE_LEVEL.get(get_role(), 1) >= ROLE_LEVEL.get(min_role, 2)

def is_ceo() -> bool:
    return get_role() == "CEO"

def is_staff_or_above() -> bool:
    return get_role() in ("CEO", "Staff")

# ── 사용자 정보 ─────────────────────────────────────────────────────────────
user        = st.session_state.get("user", {})
role        = get_role()
nickname    = user.get("nickname", "게스트")
profile_img = user.get("profile_image", None)

ROLE_LABELS = {
    "CEO":    ("👑 최고관리자", "#FFD700"),
    "Staff":  ("🔧 운영진",     "#CCFF00"),
    "Member": ("🎾 정회원",     "#60EFFF"),
    "Guest":  ("🔓 게스트",     "#aab8d4"),
}
role_text, role_color = ROLE_LABELS.get(role, ("🔓 게스트", "#aab8d4"))

# ── 아바타 HTML 헬퍼 ────────────────────────────────────────────────────────
def avatar_html(img_url, initials, size=54):
    if img_url:
        return f'<img src="{img_url}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #CCFF00;">'
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:linear-gradient(135deg,#1a253d,#CCFF00 200%);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-weight:900;font-size:{size//2.5:.0f}px;color:#0A0E1A;'
        f'border:2px solid #CCFF00;">{initials}</div>'
    )

initials = nickname[:1] if nickname else "?"

# ══════════════════════════════════════════════════════════════════════════════
#  전역 CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap');

/* ── 숨김 유틸 ── */
.mobile-only { display: block; }
.pc-only     { display: none;  }
@media (min-width: 769px) {
    .mobile-only { display: none;  }
    .pc-only     { display: block; }
}

/* ── 프로필 카드 ── */
.profile-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, rgba(26,37,61,0.9), rgba(10,14,26,0.95));
    border: 1px solid rgba(204,255,0,0.2);
    border-radius: 20px;
    padding: 16px 18px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.profile-info { display: flex; align-items: center; gap: 14px; }
.profile-name {
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 1.15rem;
    color: #ffffff;
    line-height: 1.2;
}
.profile-role-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 30px;
    margin-top: 4px;
    border: 1px solid;
}
.ceo-btn {
    background: linear-gradient(135deg, #CCFF00, #a8d400);
    color: #0A0E1A !important;
    font-weight: 900 !important;
    font-size: 0.78rem !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 8px 14px !important;
    cursor: pointer;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(204,255,0,0.35);
    text-decoration: none;
}

/* ── 아이콘 그리드 공통 버튼 베이스 ── */
.icon-btn > div.stButton > button {
    width: 100% !important;
    min-height: 88px !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    color: #d0ddf0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    line-height: 1.35 !important;
    transition: all 0.25s ease !important;
    padding: 14px 6px !important;
    white-space: pre-line !important;
}
.icon-btn > div.stButton > button:hover {
    background: rgba(204,255,0,0.08) !important;
    border-color: rgba(204,255,0,0.45) !important;
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(204,255,0,0.15) !important;
    color: #ffffff !important;
}
.icon-btn-locked > div.stButton > button {
    opacity: 0.45 !important;
    cursor: not-allowed !important;
}
.icon-btn-locked > div.stButton > button:hover {
    transform: none !important;
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(255,255,255,0.09) !important;
    box-shadow: none !important;
}
.icon-btn-coming > div.stButton > button {
    opacity: 0.35 !important;
    cursor: default !important;
}
.icon-btn-coming > div.stButton > button:hover {
    transform: none !important;
}

/* ── PC 퀵 메뉴 버튼 ── */
div.stButton > button { border-radius: 12px !important; font-weight: 700 !important; }

/* ── 섹션 헤더 ── */
.section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    color: #aab8d4;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  📱 MOBILE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

# ── 메뉴 정의 ──
# min_role: 이 이상 권한이어야 접근 가능 / coming_soon: True면 잠금
MENU = [
    # Row 1
    dict(icon="👤", label="멤버\n정보",    page="pages/07_멤버정보.py",  min_role="Member",  coming_soon=False),
    dict(icon="🎾", label="KDK\n대진표",   page="pages/02_대진생성.py",  min_role="Staff",   coming_soon=False),
    dict(icon="🏆", label="실시간\n랭킹",   page="pages/05_랭킹.py",      min_role="Member",  coming_soon=False),
    # Row 2
    dict(icon="💰", label="상벌금\n현황",   page="pages/04_재무.py",      min_role="Member",  coming_soon=False),
    dict(icon="🏅", label="대회\n모드",     page=None,                    min_role="Member",  coming_soon=True),
    dict(icon="💬", label="커뮤니티",       page=None,                    min_role="Member",  coming_soon=True),
]

# ── 프로필 카드 ──
ceo_btn_html = ""
if is_ceo():
    ceo_btn_html = '<a href="pages/09_CEO관리.py" class="ceo-btn">⚙️ 설정 마스터</a>'

st.markdown(f"""
<div class="mobile-only">
<div class="profile-card">
    <div class="profile-info">
        {avatar_html(profile_img, initials)}
        <div>
            <div class="profile-name">⭐ {nickname} 님<br>안녕하세요!</div>
            <div class="profile-role-badge" style="color:{role_color};border-color:{role_color}33;">
                {role_text}
            </div>
        </div>
    </div>
    {ceo_btn_html}
</div>
<div class="section-title">빠른 이동</div>
</div>
""", unsafe_allow_html=True)

# ── 아이콘 그리드 (Streamlit 버튼으로 클릭 처리) ──
# 모바일에서는 CSS로 보이고, PC에서는 숨김
st.markdown('<div class="mobile-only"><div class="icon-grid">', unsafe_allow_html=True)

# 잠금 토스트 트리거용 세션
if "lock_trigger" not in st.session_state:
    st.session_state.lock_trigger = None

rows = [MENU[i:i+3] for i in range(0, len(MENU), 3)]
for row in rows:
    cols = st.columns(3)
    for col, item in zip(cols, row):
        locked = not can_access(item["min_role"])
        coming = item["coming_soon"]

        # 상태별 CSS 클래스 결정
        if coming:
            div_class = "icon-btn icon-btn-coming"
        elif locked:
            div_class = "icon-btn icon-btn-locked"
        else:
            div_class = "icon-btn"

        # 버튼 라벨: 이모지 + 텍스트 + 뱃지
        badge = "\n🔒" if locked and not coming else ("\n🚧" if coming else "")
        btn_label = f"{item['icon']}\n{item['label']}{badge}"

        with col:
            st.markdown(f'<div class="{div_class}">', unsafe_allow_html=True)
            btn_key = f"mnav_{item['icon']}_{item['label']}"
            if st.button(btn_label, key=btn_key, use_container_width=True):
                if coming:
                    st.toast("🚧 준비 중입니다.")
                elif locked:
                    st.toast("🔒 정회원만 이용 가능한 메뉴입니다.")
                elif item["page"]:
                    st.switch_page(item["page"])
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  🖥️ PC LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="pc-only">', unsafe_allow_html=True)

# PC 헤더
st.markdown(f"""
<div style="display:flex;align-items:center;gap:18px;margin-bottom:24px;">
    <div style="filter:drop-shadow(0 0 10px rgba(204,255,0,0.6));">
        <svg viewBox="0 0 100 100" width="55" height="55">
            <circle cx="50" cy="50" r="48" fill="#CCFF00"/>
            <path d="M25,20 Q50,50 25,80" fill="none" stroke="#0A0E1A" stroke-width="3"/>
            <path d="M75,20 Q50,50 75,80" fill="none" stroke="#0A0E1A" stroke-width="3"/>
        </svg>
    </div>
    <div>
        <div style="font-family:'Outfit',sans-serif;font-weight:900;font-size:2.4rem;
                    letter-spacing:-2px;color:white;line-height:0.85;">테연</div>
        <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:0.95rem;
                    color:#CCFF00;font-style:italic;letter-spacing:4px;">테니스</div>
    </div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:12px;">
        <div style="background:rgba(204,255,0,0.08);color:#CCFF00;padding:5px 16px;
                    border-radius:30px;font-size:0.8rem;font-weight:900;
                    border:1px solid rgba(204,255,0,0.25);">SINCE 2025</div>
        {'<a href="pages/09_CEO관리.py" class="ceo-btn">⚙️ 설정 마스터</a>' if is_ceo() else ''}
    </div>
</div>
""", unsafe_allow_html=True)

today = datetime.now(timezone.utc)
st.caption(f"📅 {today.strftime('%Y. %m. %d')} — {nickname}님 환영합니다! | 권한: {role_text}")

# PC 퀵 메뉴
st.markdown("#### 🚀 퀵 메뉴")
pc_nav = [
    dict(icon="🎾", label="대진 생성",  page="pages/02_대진생성.py",  min_role="Staff"),
    dict(icon="🏃", label="경기 진행",  page="pages/03_경기진행.py",  min_role="Staff"),
    dict(icon="📊", label="경기 결과",  page="pages/03_경기결과.py",  min_role="Guest"),
    dict(icon="🏆", label="클럽 랭킹",  page="pages/05_랭킹.py",      min_role="Member"),
    dict(icon="💰", label="재무 기록",  page="pages/04_재무.py",      min_role="Member"),
    dict(icon="👥", label="멤버 정보",  page="pages/07_멤버정보.py",  min_role="Member"),
]
pc_rows = [pc_nav[i:i+3] for i in range(0, len(pc_nav), 3)]
for row in pc_rows:
    pc_cols = st.columns(3)
    for col, item in zip(pc_cols, row):
        with col:
            if can_access(item["min_role"]):
                st.page_link(item["page"], label=f"{item['icon']} {item['label']}", use_container_width=True)
            else:
                if st.button(f"🔒 {item['label']}", use_container_width=True, key=f"pc_{item['label']}"):
                    st.toast("🔒 정회원만 이용 가능한 메뉴입니다.")

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  🏆 명예의 전당 (공통)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
try:
    results = get_tournament_results()
    if results:
        st.markdown("#### 🏆 2026 명예의 전당")
        hof_cols = st.columns(min(len(results), 3))
        for i, res in enumerate(results[:3]):
            with hof_cols[i]:
                st.markdown(f"""
                <div style="background:rgba(204,255,0,0.05);padding:20px;border-radius:20px;
                            border:1px solid rgba(204,255,0,0.15);box-shadow:0 8px 32px rgba(0,0,0,0.3);
                            margin-bottom:20px;">
                    <div style="font-size:0.72rem;font-weight:700;color:#CCFF00;opacity:.8;">{res['tournament_date']}</div>
                    <div style="font-size:1.1rem;font-weight:800;color:white;margin:6px 0;">{res['tournament_name']}</div>
                    <div style="font-size:1.3rem;font-weight:900;color:#CCFF00;">{res['rank']}</div>
                    <div style="font-size:0.88rem;color:#aab8d4;margin-top:8px;
                                border-top:1px solid rgba(255,255,255,.05);padding-top:8px;">{res['winners']}</div>
                </div>
                """, unsafe_allow_html=True)
except Exception:
    pass

# ── 클럽 현황 KPI ──
st.markdown("#### 📈 클럽 현황")
k1, k2, k3, k4 = st.columns(4)
with k1: st.metric("이번 달 세션", "—")
with k2: st.metric("총 회원 수",   "—")
with k3: st.metric("내 이달 포인트", "—")
with k4: st.metric("클럽 잔액",    "—원")
