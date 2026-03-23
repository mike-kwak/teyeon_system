import os
import base64
import streamlit as st

# 사진 검색 경로 (v6.0 통합 관리)
SEARCH_DIRS = [
    "member_pics",
    "teyeon_system/member_pics",
    "../member_pics",
    "Teyeon pic",
    "c:/Users/섭이/Desktop/AI/1. Teyeon/member_pics",
    "c:/Users/섭이/Desktop/AI/1. Teyeon/Teyeon pic"
]

def get_local_img_base64(path):
    """이미지 파일을 base64 문자열로 변환"""
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
                return base64.b64encode(data).decode()
        except:
            return None
    return None

def find_member_image_path(nickname):
    """닉네임으로 이미지 파일 경로 검색"""
    if not nickname: return None
    name = nickname.strip()
    exts = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]
    
    for d in SEARCH_DIRS:
        if not os.path.exists(d): continue
        for ext in exts:
            # 다양한 이름 변형 시도
            variants = [name, name.replace(" ", ""), name.replace("_", "")]
            for v in set(variants):
                path = os.path.join(d, f"{v}{ext}")
                if os.path.exists(path):
                    return path
    return None

def get_member_photo_html(nickname, size=40, border=True):
    """닉네임으로 원형 프로필 HTML 생성"""
    path = find_member_image_path(nickname)
    b64 = get_local_img_base64(path)
    
    border_style = "border: 2px solid rgba(255,255,255,0.2);" if border else ""
    
    if b64:
        return f'<img src="data:image/png;base64,{b64}" style="width:{size}px; height:{size}px; border-radius:50%; object-fit:cover; {border_style}">'
    else:
        # 이미지가 없을 경우 기본 🎾 표시 (배경색 포함)
        return (f'<div style="width:{size}px; height:{size}px; border-radius:50%; '
                f'background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); '
                f'display:flex; align-items:center; justify-content:center; font-size:{size*0.6}px; {border_style}">🎾</div>')

def get_member_official_role(nickname, db_position=None):
    """닉네임과 DB 데이터를 바탕으로 공식 직책 반환"""
    ADMIN_MAP = {"박광현": "회장", "강정호": "부회장", "정상윤": "총무", "곽민섭": "재무이사", "김민준": "경기이사", "남인우": "섭외이사"}
    return ADMIN_MAP.get(nickname) or db_position or "회원"
