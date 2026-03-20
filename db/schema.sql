-- ==========================================================
-- TEYEON 테니스 클럽 관리 앱 — Supabase 초기 스키마
-- Supabase Dashboard → SQL Editor에 붙여넣어 실행하세요.
-- ==========================================================

-- 1. clubs (클럽 테이블 — 멀티 클럽 확장 대비)
CREATE TABLE IF NOT EXISTS clubs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 기본 클럽 삽입 (TEYEON)
INSERT INTO clubs (name) VALUES ('TEYEON')
ON CONFLICT DO NOTHING;

-- ==========================================================

-- 2. members (회원)
CREATE TABLE IF NOT EXISTS members (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kakao_id      BIGINT UNIQUE,
    nickname      TEXT NOT NULL,
    profile_image TEXT,
    email         TEXT,
    club_id       UUID REFERENCES clubs(id) ON DELETE SET NULL,
    is_admin      BOOLEAN DEFAULT FALSE,
    is_guest      BOOLEAN DEFAULT FALSE,
    role          TEXT DEFAULT 'Member' CHECK (role IN ('CEO', 'Staff', 'Member', 'Guest')),
    position      TEXT,
    mbti          TEXT,
    birthdate     DATE,
    affiliation   TEXT,
    achievements  TEXT,
    joined_at     TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_members_kakao_id ON members(kakao_id);
CREATE INDEX IF NOT EXISTS idx_members_club_id  ON members(club_id);

-- ==========================================================

-- 3. kdk_sessions (KDK 경기 세션)
CREATE TABLE IF NOT EXISTS kdk_sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    club_id       UUID REFERENCES clubs(id) ON DELETE CASCADE,
    session_date  DATE NOT NULL,
    status        TEXT DEFAULT 'draft'
                  CHECK (status IN ('draft', 'in_progress', 'completed')),
    note          TEXT,
    created_by    UUID REFERENCES members(id),
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kdk_sessions_club_id ON kdk_sessions(club_id);

-- ==========================================================

-- 4. kdk_matches (개별 경기)
CREATE TABLE IF NOT EXISTS kdk_matches (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id    UUID REFERENCES kdk_sessions(id) ON DELETE CASCADE,
    round         INT NOT NULL,
    court         INT NOT NULL,
    team_a        UUID[] NOT NULL,
    team_b        UUID[] NOT NULL,
    score_a       INT,
    score_b       INT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kdk_matches_session_id ON kdk_matches(session_id);

-- ==========================================================

-- 5. kdk_results (세션 최종 개인 결과)
CREATE TABLE IF NOT EXISTS kdk_results (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id    UUID REFERENCES kdk_sessions(id) ON DELETE CASCADE,
    member_id     UUID REFERENCES members(id) ON DELETE CASCADE,
    wins          INT DEFAULT 0,
    losses        INT DEFAULT 0,
    points_diff   INT DEFAULT 0,
    rank          INT,
    reward        INT DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(session_id, member_id)
);

-- ==========================================================

-- 6. finance_records (재무)
CREATE TABLE IF NOT EXISTS finance_records (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    club_id       UUID REFERENCES clubs(id) ON DELETE CASCADE,
    session_id    UUID REFERENCES kdk_sessions(id) ON DELETE SET NULL,
    member_id     UUID REFERENCES members(id) ON DELETE SET NULL,
    type          TEXT NOT NULL
                  CHECK (type IN ('reward', 'penalty', 'manual')),
    amount        INT NOT NULL,
    description   TEXT,
    recorded_at   TIMESTAMPTZ DEFAULT now(),
    created_by    UUID REFERENCES members(id)
);

CREATE INDEX IF NOT EXISTS idx_finance_club_id ON finance_records(club_id);

-- ==========================================================

-- 7. ranking_points (포인트 누적)
CREATE TABLE IF NOT EXISTS ranking_points (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    club_id       UUID REFERENCES clubs(id) ON DELETE CASCADE,
    member_id     UUID REFERENCES members(id) ON DELETE CASCADE,
    session_id    UUID REFERENCES kdk_sessions(id) ON DELETE SET NULL,
    points        INT NOT NULL DEFAULT 0,
    reason        TEXT,
    awarded_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ranking_points_club_member ON ranking_points(club_id, member_id);
CREATE INDEX IF NOT EXISTS idx_ranking_points_awarded_at  ON ranking_points(awarded_at);

-- ==========================================================

-- 8. access_logs (접속 로그)
CREATE TABLE IF NOT EXISTS access_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id     UUID REFERENCES members(id) ON DELETE SET NULL,
    nickname      TEXT,
    role          TEXT,
    page_name     TEXT NOT NULL,
    ip_address    TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_member_id ON access_logs(member_id);

-- 9. menu_permissions (메뉴 권한 설정)
CREATE TABLE IF NOT EXISTS menu_permissions (
    role              TEXT PRIMARY KEY,
    accessible_pages  TEXT[] NOT NULL
);

-- 초기 권한 데이터 삽입
INSERT INTO menu_permissions (role, accessible_pages) VALUES
('CEO',    ARRAY['01_대시보드.py', '02_대진생성.py', '03_경기결과.py', '03_경기진행.py', '04_재무.py', '05_랭킹.py', '06_시드예측.py', '07_멤버정보.py', '08_멤버관리.py', '09_CEO관리.py', '00_공지사항.py']),
('Staff',  ARRAY['01_대시보드.py', '02_대진생성.py', '03_경기결과.py', '03_경기진행.py', '04_재무.py', '05_랭킹.py', '06_시드예측.py', '07_멤버정보.py', '08_멤버관리.py', '00_공지사항.py']),
('Member', ARRAY['01_대시보드.py', '03_경기결과.py', '05_랭킹.py', '06_시드예측.py', '07_멤버정보.py', '00_공지사항.py']),
('Guest',  ARRAY['00_공지사항.py', '02_대진생성.py'])
ON CONFLICT (role) DO UPDATE SET accessible_pages = EXCLUDED.accessible_pages;

-- ==========================================================
-- Row Level Security (RLS)
-- ==========================================================

-- members 테이블 RLS
ALTER TABLE members ENABLE ROW LEVEL SECURITY;

-- 모든 로그인 사용자: 전체 회원 조회 가능 (닉네임, 프로필 표시용)
CREATE POLICY "members_select_all" ON members
    FOR SELECT TO authenticated USING (true);

-- 본인 행만 수정 가능
CREATE POLICY "members_update_own" ON members
    FOR UPDATE TO authenticated
    USING (kakao_id::text = current_setting('app.kakao_id', true));

-- INSERT는 서버 측(anon key upsert)에서 처리하므로 서비스 롤로 처리
-- (Supabase SDK anon key는 RLS를 거침 — upsert 정책 필요 시 추가)
CREATE POLICY "members_insert_own" ON members
    FOR INSERT TO authenticated
    WITH CHECK (true);

-- kdk_sessions, kdk_results 등 나머지 테이블은 초기 개발 편의상
-- RLS 비활성화 후, 운영 전환 시 정책 추가 권장
-- ALTER TABLE kdk_sessions ENABLE ROW LEVEL SECURITY;
-- ... (필요 시 추가)

-- ==========================================================
-- 10. tournament_results (대회 성과 관리)
-- ==========================================================
CREATE TABLE IF NOT EXISTS tournament_results (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_date   DATE NOT NULL,
    tournament_name   TEXT NOT NULL,
    rank              TEXT NOT NULL, -- 우승, 준우승, 3위 등
    winners           TEXT NOT NULL, -- 수상자 명단
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- ==========================================================
-- 11. menu_settings (메뉴 제어 설정)
-- ==========================================================
CREATE TABLE IF NOT EXISTS menu_settings (
    page_filename  TEXT PRIMARY KEY,
    display_name   TEXT NOT NULL,
    order_index    INT DEFAULT 99,
    is_hidden      BOOLEAN DEFAULT FALSE
);

-- 초기 메뉴 데이터 삽입
INSERT INTO menu_settings (page_filename, display_name, order_index) VALUES
('00_공지사항.py', '📢 공지사항', 0),
('01_대시보드.py', '🏠 대시보드', 1),
('02_대진생성.py', '🎾 대진생성', 2),
('03_경기진행.py', '🏃 경기진행', 3),
('03_경기결과.py', '📊 경기결과', 4),
('04_재무.py', '💰 재무', 5),
('05_랭킹.py', '🔥 랭킹', 6),
('06_시드예측.py', '⚡ 시드예측', 7),
('07_멤버정보.py', '👤 멤버정보', 8),
('08_멤버관리.py', '🛠️ 멤버관리', 9),
('09_CEO관리.py', '👑 CEO관리', 10)
ON CONFLICT (page_filename) DO UPDATE SET 
    display_name = EXCLUDED.display_name,
    order_index = EXCLUDED.order_index;
