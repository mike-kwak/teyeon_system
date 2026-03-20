from db.supabase_client import get_client

def migrate():
    client = get_client()
    
    print("🚀 Step 5 테이블 생성을 시작합니다...")
    
    # 1. tournament_results 테이블 생성
    try:
        # RPC가 없을 수 있으므로 직접 query 시도 (단, supabase-py는 DDL을 직접 지원하지 않음)
        # 따라서 여기서는 가장 안전하게 SQL Editor에 복사할 용도의 SQL을 출력하거나,
        # 가능한 경우 조작을 시도합니다.
        # 현 환경에서는 사용자가 직접 SQL Editor에 붙여넣는 것이 가장 확실합니다.
        pass
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    # 이 스크립트는 직접 실행하기보다 SQL Editor 안내용으로 작성되었습니다.
    print("""
    ⚠️ Supabase SQL Editor에 아래 SQL을 복사하여 실행해 주세요:
    
    -- 1. tournament_results
    CREATE TABLE IF NOT EXISTS tournament_results (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tournament_date   DATE NOT NULL,
        tournament_name   TEXT NOT NULL,
        rank              TEXT NOT NULL,
        winners           TEXT NOT NULL,
        created_at        TIMESTAMPTZ DEFAULT now()
    );

    -- 2. menu_settings
    CREATE TABLE IF NOT EXISTS menu_settings (
        page_filename  TEXT PRIMARY KEY,
        display_name   TEXT NOT NULL,
        order_index    INT DEFAULT 99,
        is_hidden      BOOLEAN DEFAULT FALSE
    );

    -- 초기 데이터
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
    """)
