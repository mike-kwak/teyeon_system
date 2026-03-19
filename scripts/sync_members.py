import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY"))
CLUB_ID = os.environ.get("CLUB_ID")
EXCEL_PATH = "c:/Users/섭이/Desktop/AI/1. Teyeon/teyeon_system/테연 명단.xlsx"

def sync_members():
    print("Starting sync...")
    df = pd.read_excel(EXCEL_PATH, header=None)
    ADMIN_POS = ["회장", "부회장", "총무", "재무", "경기", "섭외"]
    
    for i in range(2, len(df)):
        row = df.iloc[i]
        if pd.isna(row[2]): continue # 이름 없으면 패스
        
        name = str(row[2]).strip()
        pos_raw = str(row[3]).strip() if not pd.isna(row[3]) else ""
        phone = str(row[4]).strip() if not pd.isna(row[4]) else "" # 연락처 추가
        
        is_admin = any(p in pos_raw for p in ADMIN_POS)
        try: tid = -1000 - int(row[1])
        except: tid = -2000 - i
        
        # 기본 데이터 (필수 필드)
        base = {
            "nickname": name,
            "club_id": CLUB_ID,
            "is_admin": is_admin
        }
        
        # 상세 데이터 (SQL 실행 후 들어가는 필드)
        full = {
            **base,
            "phone": phone,
            "position": pos_raw,
            "mbti": str(row[6]).strip() if not pd.isna(row[6]) else "",
            "affiliation": str(row[7]).strip() if not pd.isna(row[7]) else "",
            "achievements": f"{row[8]} | {row[9]}" if not pd.isna(row[8]) or not pd.isna(row[9]) else ""
        }
        
        # 닉네임으로 찾아서 업데이트 또는 삽입
        res = client.table("members").select("id").eq("nickname", name).execute()
        
        if res.data:
            mid = res.data[0]["id"]
            # 1. 기본 정보 먼저 업데이트
            client.table("members").update(base).eq("id", mid).execute()
            # 2. 상세 정보 업데이트 시도 (컬럼 없으면 여기서 에러 발생 및 catch)
            try:
                client.table("members").update(full).eq("id", mid).execute()
                print(f"Updated full: {name}")
            except:
                print(f"Updated core only: {nickname}")
        else:
            # 신규 삽입
            full["kakao_id"] = tid
            try:
                client.table("members").insert(full).execute()
                print(f"Inserted full: {name}")
            except:
                client.table("members").insert({**base, "kakao_id": tid}).execute()
                print(f"Inserted core only: {name}")
                
    print("Sync complete.")

if __name__ == "__main__":
    sync_members()
