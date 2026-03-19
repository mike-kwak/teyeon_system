import os
import base64
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY"))
IMAGE_PATH = "c:/Users/섭이/Desktop/AI/1. Teyeon/Teyeon pic/곽민섭.png"

def register_profile():
    name = "곽민섭"
    print(f"Registering profile for {name}...")
    
    if not os.path.exists(IMAGE_PATH):
        print("Image not found path:", IMAGE_PATH)
        return

    # 1. 파일 읽기 및 Base64 변환 (간단하게 DB에 넣거나 Storage 업로드)
    # 여기서는 정석대로 Storage 업로드를 시도합니다.
    bucket_name = "profile_images"
    
    # 버킷 존재 여부 확인 및 생성 (권한에 따라 실패할 수 있음)
    try:
        with open(IMAGE_PATH, 'rb') as f:
            file_data = f.read()
            file_ext = os.path.splitext(IMAGE_PATH)[1].lower()
            storage_path = f"{name}{file_ext}"
            
            # 업로드 (이미 있으면 덮어쓰기)
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": f"image/png", "x-upsert": "true"}
            )
            
            # 공용 URL 가져오기
            url = client.storage.from_(bucket_name).get_public_url(storage_path)
            
            # DB 업데이트
            client.table("members").update({"profile_image": url}).eq("nickname", name).execute()
            print(f"Successfully registered: {url}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Storage upload failed. Trying to update DB with local metadata is not ideal for web apps.")

if __name__ == "__main__":
    register_profile()
