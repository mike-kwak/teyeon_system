"""
core_logic/kdk_engine.py
─────────────────────────
KDK 대진 생성 + 상벌금 계산 엔진.

TODO (Phase 3):
  - generate_matches()   : 4인 1조 랜덤 배정, forced_pairs 반영, 휴식자 처리
  - calculate_results()  : 라운드 합산 → 개인 승패·득실차 집계
  - calculate_rewards()  : 순위별 상금/벌금 동적 계산
"""

from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class Player:
    id: str
    name: str
    is_guest: bool = False


@dataclass
class Match:
    round: int
    court: int
    team_a: list[Player]  # 2명
    team_b: list[Player]  # 2명
    score_a: Optional[int] = None
    score_b: Optional[int] = None


# ── 상벌금 규칙 테이블 (인원수별) ─────────────────────────────────────────
# 구조: {총인원: [(순위_범위_start, 순위_범위_end, 벌금_금액), ...]}
PENALTY_TABLE: dict[int, list[tuple[int, int, int]]] = {
    6:  [(4, 5, -3_000), (6, 6, -5_000)],
    8:  [(5, 6, -3_000), (7, 8, -5_000)],
    10: [(6, 7, -3_000), (8, 10, -5_000)],
    12: [(7, 9, -3_000), (10, 12, -5_000)],
}
REWARD_1ST = 10_000  # 1위 상금 (원)


def generate_matches(
    players: list[Player],
    forced_pairs: list[tuple[str, str]] | None = None,
    num_rounds: int = 3,
) -> list[list[Match]]:
    """
    4인 1조 대진 생성.
    forced_pairs: [(player_id_1, player_id_2), ...] — 반드시 같은 팀으로 묶을 쌍

    Returns: rounds[round_idx] = [Match, Match, ...]
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")


def calculate_results(matches: list[Match]) -> dict[str, dict]:
    """
    전체 경기 결과를 player_id 기준으로 집계.
    Returns: {player_id: {wins, losses, points_diff}}
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")


def calculate_rewards(
    results: dict[str, dict],
    players: list[Player],
    total_count: int,
) -> dict[str, int]:
    """
    순위 → 상금/벌금 계산.
    게스트는 상금 제외, 벌금은 동일 적용.
    Returns: {player_id: amount}  (+양수: 상금, -음수: 벌금)
    """
    # TODO: Phase 3에서 완전 구현
    raise NotImplementedError("Phase 3에서 구현 예정")
