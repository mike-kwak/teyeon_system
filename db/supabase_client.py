"""
db/supabase_client.py
─────────────────────
Supabase 연결 싱글턴 + 공통 쿼리 헬퍼.
모든 페이지에서 `from db.supabase_client import get_client` 로 임포트.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

from supabase import create_client, Client

load_dotenv()


def _get_secret(key: str) -> str | None:
    """st.secrets → os.environ 순서로 시크릿 값을 가져옵니다 (Streamlit Cloud & 로컬 호환)."""
    try:
        import streamlit as st
        return st.secrets.get(key) or os.environ.get(key)
    except Exception:
        return os.environ.get(key)


# ── 싱글턴 클라이언트 ────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_client() -> Client:
    """Supabase 클라이언트를 최초 1회만 생성하여 재사용."""
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수를 설정해주세요."
        )
    return create_client(url, key)


# ── 회원(members) 헬퍼 ───────────────────────────────────────────────────
def upsert_member(kakao_id: int, nickname: str, profile_image: str = None, email: str = None) -> dict:
    """
    카카오 로그인 성공 시 회원 정보를 upsert.
    """
    client = get_client()

    # 1. 이미 해당 kakao_id로 등록된 멤버가 있는지 확인
    existing = client.table("members").select("*").eq("kakao_id", kakao_id).execute()
    
    if existing.data:
        data = {
            "nickname": nickname,
            "profile_image": profile_image,
            "email": email,
            "updated_at": "now()"
        }
        if nickname == "곽민섭":
            data["role"] = "CEO"
        res = client.table("members").update(data).eq("kakao_id", kakao_id).execute()
        return res.data[0] if res.data else {}

def delete_kdk_session(session_id: str):
    """KDK 세션 및 관련 데이터(매치, 결과) 삭제 (Archive)."""
    client = get_client()
    client.table("kdk_matches").delete().eq("session_id", session_id).execute()
    client.table("kdk_results").delete().eq("session_id", session_id).execute()
    client.table("kdk_sessions").delete().eq("id", session_id).execute()

    
    # 2. 임시 멤버 연결 (중략...)
    temp_member = client.table("members").select("*").eq("nickname", nickname).lt("kakao_id", 0).execute()
    if temp_member.data:
        member_id = temp_member.data[0]["id"]
        data = {"kakao_id": kakao_id, "profile_image": profile_image, "email": email, "updated_at": "now()"}
        if nickname == "곽민섭":
            data["role"] = "CEO"
        res = client.table("members").update(data).eq("id", member_id).execute()
        return res.data[0] if res.data else {}

    # 3. 신규 생성
    # CEO 곽민섭님 자동 지정
    role = "CEO" if nickname == "곽민섭" else "Member"
    data = {
        "kakao_id": kakao_id, 
        "nickname": nickname, 
        "profile_image": profile_image, 
        "email": email,
        "role": role
    }
    res = client.table("members").insert(data).execute()
    return res.data[0] if res.data else {}

def update_member_info(member_id: str, data: dict) -> dict:
    """
    회원의 상세 정보를 업데이트 (ID 기반).
    """
    client = get_client()
    data["updated_at"] = "now()"
    res = client.table("members").update(data).eq("id", member_id).execute()
    return res.data[0] if res.data else {}


def get_member_by_kakao_id(kakao_id: int) -> dict | None:
    """kakao_id로 회원 조회. 없으면 None 반환."""
    client = get_client()
    res = (
        client.table("members")
        .select("*")
        .eq("kakao_id", kakao_id)
        .single()
        .execute()
    )
    return res.data


def get_all_members(club_id: str = None) -> list[dict]:
    """전체(또는 특정 클럽) 회원 목록 조회."""
    client = get_client()
    query = client.table("members").select("*")
    if club_id:
        query = query.eq("club_id", club_id)
    return query.execute().data or []


# ── KDK 세션 헬퍼 ────────────────────────────────────────────────────────
def create_kdk_session(club_id: str, session_date: str, created_by: str, note: str = "", award_config: dict = None, title: str = "") -> dict:
    """새 KDK 세션을 생성하고 반환."""
    client = get_client()
    data = {
        "club_id": club_id,
        "session_date": session_date,
        "created_by": created_by,
        "note": note,
        "status": "draft",
        "title": title or f"대진표_{session_date}",
    }
    if award_config:
        # award_config 컬럼이 없을 수도 있으므로 note에 백업 저장하거나 
        # 테이블 컬럼이 있다고 가정 (보통 JSONB 타입 권장)
        data["award_config"] = award_config
        
    res = (
        client.table("kdk_sessions")
        .insert(data)
        .execute()
    )
    return res.data[0] if res.data else {}


def get_kdk_sessions(club_id: str, limit: int = 20) -> list[dict]:
    """최근 KDK 세션 목록 조회."""
    client = get_client()
    return (
        client.table("kdk_sessions")
        .select("*")
        .eq("club_id", club_id)
        .order("session_date", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )


def get_kdk_session(session_id: str) -> dict | None:
    """단일 KDK 세션 조회."""
    client = get_client()
    res = (
        client.table("kdk_sessions")
        .select("*, kdk_results(*), kdk_matches(*)")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return res.data


def update_kdk_session_status(session_id: str, status: str) -> dict:
    """KDK 세션 상태 업데이트 (draft → in_progress → completed)."""
    client = get_client()
    res = (
        client.table("kdk_sessions")
        .update({"status": status})
        .eq("id", session_id)
        .execute()
    )
    return res.data[0] if res.data else {}


# ── KDK 매치 헬퍼 ────────────────────────────────────────────────────────
def upsert_kdk_matches(matches: list[dict]) -> list[dict]:
    """매치 목록 배치 upsert (id가 있으면 update, 없으면 insert)."""
    client = get_client()
    res = (
        client.table("kdk_matches")
        .upsert(matches)
        .execute()
    )
    return res.data or []


def update_kdk_match_score(match_id: str, score1: int, score2: int, status: str = "complete") -> dict:
    """단일 매치 점수 업데이트."""
    client = get_client()
    res = (
        client.table("kdk_matches")
        .update({
            "score1": score1,
            "score2": score2,
            "status": status,
            "updated_at": "now()"
        })
        .eq("id", match_id)
        .execute()
    )
    return res.data[0] if res.data else {}


# ── KDK 결과 헬퍼 ────────────────────────────────────────────────────────
def upsert_kdk_results(results: list[dict]) -> list[dict]:
    """경기 결과 배치 upsert. results = [{session_id, member_id, wins, ...}, ...]"""
    client = get_client()
    res = (
        client.table("kdk_results")
        .upsert(results, on_conflict="session_id,member_id")
        .execute()
    )
    return res.data or []


# ── 재무 헬퍼 ────────────────────────────────────────────────────────────
def insert_finance_record(
    club_id: str,
    type_: str,
    amount: int,
    description: str,
    created_by: str,
    session_id: str = None,
    member_id: str = None,
) -> dict:
    """재무 레코드 단건 삽입."""
    client = get_client()
    res = (
        client.table("finance_records")
        .insert({
            "club_id": club_id,
            "session_id": session_id,
            "member_id": member_id,
            "type": type_,
            "amount": amount,
            "description": description,
            "created_by": created_by,
        })
        .execute()
    )
    return res.data[0] if res.data else {}


def get_finance_records(club_id: str, limit: int = 50) -> list[dict]:
    """재무 기록 조회 (최신순)."""
    client = get_client()
    return (
        client.table("finance_records")
        .select("*, members(nickname)")
        .eq("club_id", club_id)
        .order("recorded_at", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )


# ── 랭킹 포인트 헬퍼 ─────────────────────────────────────────────────────
def add_ranking_points(
    club_id: str,
    member_id: str,
    points: int,
    reason: str,
    session_id: str = None,
) -> dict:
    """포인트 적립 (KDK 완료 시 자동 혹은 수동 부여 모두 사용)."""
    client = get_client()
    res = (
        client.table("ranking_points")
        .insert({
            "club_id": club_id,
            "member_id": member_id,
            "session_id": session_id,
            "points": points,
            "reason": reason,
        })
        .execute()
    )
    return res.data[0] if res.data else {}


def get_ranking(club_id: str, start_date: str = None, end_date: str = None) -> list[dict]:
    """
    기간별 랭킹 집계.
    반환: [{member_id, nickname, total_points}, ...] 포인트 내림차순
    """
    client = get_client()
    query = (
        client.table("ranking_points")
        .select("member_id, points, members(nickname)")
        .eq("club_id", club_id)
    )
    if start_date:
        query = query.gte("awarded_at", start_date)
    if end_date:
        query = query.lte("awarded_at", end_date)

    rows = query.execute().data or []

def update_kdk_match_score(match_id: str, score1: int, score2: int, status: str = "complete"):
    """KDK 개별 경기 점수 및 상태 업데이트"""
    client = get_client()
    res = client.table("kdk_matches").update({
        "score1": score1,
        "score2": score2,
        "status": status
    }).eq("id", match_id).execute()
    return res.data

    # Python 쪽에서 집계 (Supabase Free tier에서 GROUP BY RPC 없이 처리)
    aggregated: dict[str, dict] = {}
    for row in rows:
        mid = row["member_id"]
        if mid not in aggregated:
            aggregated[mid] = {
                "member_id": mid,
                "nickname": row.get("members", {}).get("nickname", "알 수 없음"),
                "total_points": 0,
            }
        aggregated[mid]["total_points"] += row["points"]

    return sorted(aggregated.values(), key=lambda x: x["total_points"], reverse=True)


# ── 권한 및 접속 로그 헬퍼 ───────────────────────────────────────────────
def log_access(member_id: str | None, nickname: str, role: str, page_name: str, ip_address: str = None):
    """사용자의 페이지 접속 로그를 기록."""
    client = get_client()
    try:
        client.table("access_logs").insert({
            "member_id": member_id,
            "nickname": nickname,
            "role": role,
            "page_name": page_name,
            "ip_address": ip_address
        }).execute()
    except Exception as e:
        print(f"[db] 로그 기록 실패: {e}")

def get_menu_permissions(role: str) -> list[str]:
    """특정 권한이 접근 가능한 페이지 목록 조회 (menu_settings 순서와 숨김 적용)."""
    client = get_client()
    try:
        # 1. 역할별 허용된 페이지 목록
        res = client.table("menu_permissions").select("accessible_pages").eq("role", role).single().execute()
        allowed = res.data.get("accessible_pages", []) if res.data else []
        
        # 2. 메뉴 설정 (순서 및 숨김) 조회
        settings = client.table("menu_settings").select("*").order("order_index").execute().data or []
        
        # 3. 필터링 및 정렬
        ordered_pages = []
        hidden_pages = {s["page_filename"] for s in settings if s["is_hidden"]}
        settings_map = {s["page_filename"]: s["order_index"] for s in settings}
        
        # 허용된 페이지 중 숨겨지지 않은 것들만 추림
        final_list = [p for p in allowed if p not in hidden_pages]
        
        # 설정에 있는 순서대로 정렬 (설정에 없는 페이지는 뒤로)
        final_list.sort(key=lambda x: settings_map.get(x, 999))
        
        return final_list
    except:
        if role == "Guest": return ["00_공지사항.py", "02_대진생성.py"]
        return []

# ── Step 5: 성과 및 메뉴 관리 헬퍼 ───────────────────────────────────────

def get_tournament_results() -> list[dict]:
    """최근 대회 성과 목록 조회."""
    client = get_client()
    return client.table("tournament_results").select("*").order("tournament_date", desc=True).execute().data or []

def add_tournament_result(date_str: str, name: str, rank: str, winners: str) -> dict:
    """대회 성과 추가."""
    client = get_client()
    res = client.table("tournament_results").insert({
        "tournament_date": date_str,
        "tournament_name": name,
        "rank": rank,
        "winners": winners
    }).execute()
    return res.data[0] if res.data else {}

def delete_tournament_result(res_id: str):
    """대회 성과 삭제."""
    client = get_client()
    client.table("tournament_results").delete().eq("id", res_id).execute()

def get_menu_settings() -> list[dict]:
    """모든 메뉴의 이름, 순서, 숨김 여부 조회."""
    client = get_client()
    return client.table("menu_settings").select("*").order("order_index").execute().data or []

def update_menu_setting(page_filename: str, display_name: str, order_index: int, is_hidden: bool):
    """메뉴 개별 설정 업데이트."""
    client = get_client()
    client.table("menu_settings").upsert({
        "page_filename": page_filename,
        "display_name": display_name,
        "order_index": order_index,
        "is_hidden": is_hidden
    }).execute()

def update_menu_permissions(role: str, pages: list[str]):
    """권한별 접근가능 페이지 업데이트 (CEO 전용)."""
    client = get_client()
    client.table("menu_permissions").upsert({"role": role, "accessible_pages": pages}).execute()

def get_sidebar_items(role: str) -> list[dict]:
    """사이드바 출력을 위한 최종 메뉴 목록 (경로, 라벨 포함) 반환."""
    client = get_client()
    try:
        # 1. 역할별 허용 페이지
        res = client.table("menu_permissions").select("accessible_pages").eq("role", role).single().execute()
        allowed = res.data.get("accessible_pages", []) if res.data else []
        
        # 2. 메뉴 설정 (전체)
        settings = client.table("menu_settings").select("*").order("order_index").execute().data or []
        settings_map = {s["page_filename"]: s for s in settings}
        
        # 3. 조립
        items = []
        for filename in allowed:
            s = settings_map.get(filename)
            if s and not s["is_hidden"]:
                items.append({
                    "path": f"pages/{filename}",
                    "label": s["display_name"],
                    "order": s["order_index"]
                })
            elif not s:
                # 설정에 없으면 기본 경로/파일명을 라벨로 추가 (숨김 처리되지 않았다고 가정)
                items.append({
                    "path": f"pages/{filename}",
                    "label": filename,
                    "order": 999
                })
        
        # 4. 정렬
        items.sort(key=lambda x: x["order"])
        return items
    except Exception as e:
        print(f"[db] 사이드바 아이템 조회 실패: {e}")
        return []

def get_ceo_dashboard_stats():
    """CEO 대시보드용 통계 데이터 (오늘 방문자, 실시간 로그, 게스트 목록)."""
    client = get_client()
    from datetime import datetime, date
    
    today_str = date.today().isoformat()
    
    # 1. 오늘 총 방문수 (중복 포함)
    today_logs = client.table("access_logs").select("*", count="exact").gte("created_at", today_str).execute()
    
    # 2. 최근 실시간 접속 (최신 30건)
    recent_logs = client.table("access_logs").select("*").order("created_at", desc=True).limit(30).execute().data or []
    
    # 3. 오늘 방문한 게스트 목록
    guest_logs = client.table("access_logs").select("nickname, created_at").eq("role", "Guest").gte("created_at", today_str).order("created_at", desc=True).execute().data or []
    
    return {
        "today_total": today_logs.count or 0,
        "recent_logs": recent_logs,
        "guest_logs": guest_logs
    }

def check_auth_and_log(page_name: str):
    """모든 페이지 상단에서 호출하여 권한 체크 및 로그 기록."""
    import streamlit as st
    import os
    
    user = st.session_state.get("user")
    role = st.session_state.get("role", "Guest")
    nickname = user.get("nickname", "Guest") if user else "Visitor"
    member_id = user.get("id") if user and not user.get("is_guest") else None
    
    # 로그 기록
    log_access(member_id, nickname, role, page_name)
    
    # ── 커스스트 사이드바 렌더링 (showSidebarNavigation=false 대응) ──
    with st.sidebar:
        # 상단 홈 버튼 및 프로필
        st.page_link("app.py", label="🏠 홈 (랜딩페이지)", use_container_width=True)
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin: 10px 0;">
            <div style="font-size: 0.8rem; color: #CCFF00; font-weight: 700;">{role}</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: white;">{nickname}님</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 권한 기반 사이드바 아이템 가져오기 (정렬/명칭/숨김 반영)
        items = get_sidebar_items(role)
        for item in items:
            # 현재 페이지와 일치하면 볼드체 등으로 강조하고 싶지만 st.page_link 기능상 기본 지원됨
            st.page_link(item["path"], label=item["label"], use_container_width=True)
        
        st.divider()
        if st.button("로그아웃", use_container_width=True, key="sidebar_logout_btn"):
            st.session_state.clear()
            st.rerun()
    
    # 권한 체크
    allowed_pages = get_menu_permissions(role)
    if page_name not in allowed_pages:
        st.error(f"'{page_name}' 페이지에 접근할 권한이 없습니다. (현재 권한: {role})")
        st.stop()

    # ── 상단 뒤로가기 버튼 (모든 서브페이지 공통) ──────────────────────────
    st.markdown("""
    <style>
    .back-btn-wrap { margin-bottom: 8px; }
    div[data-testid="stPageLink-NavLink"] p {
        font-size: 0.82rem !important; font-weight: 700 !important;
        color: #aab8d4 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.page_link("app.py", label="← 홈으로")
