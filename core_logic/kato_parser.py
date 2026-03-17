"""
core_logic/kato_parser.py
──────────────────────────
KATO 엑셀 파일 파싱 + 복식 시드 예측.

TODO (Phase 3):
  - parse_kato_excel()   : 컬럼 자동 감지 + 이름/포인트 추출
  - predict_seed()       : 두 선수 포인트 합산 → 전체 등록 팀 대비 예상 시드
"""

import pandas as pd


def parse_kato_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    KATO 엑셀 원본 DataFrame → 정규화된 {name, points} DataFrame 반환.
    컬럼명이 버전마다 달라 유연하게 처리.
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")


def predict_doubles_seed(
    df_kato: pd.DataFrame,
    player1_name: str,
    player2_name: str,
) -> dict:
    """
    두 선수 포인트 합산 후 전체 DB 대비 예상 시드 계산.
    Returns: {
        "player1": {"name": ..., "points": ...},
        "player2": {"name": ..., "points": ...},
        "combined_points": int,
        "estimated_seed": int,
        "total_pairs": int,
    }
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")
