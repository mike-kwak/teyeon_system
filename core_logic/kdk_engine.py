from datetime import datetime, timedelta
import math
import random

def generate_kdk_matches_v3(players_info, group_court_map, target_matches=4, concept="기본(랜덤)", fixed_partners=None, fixed_partner_games=1):
    """
    고도화된 KDK 대진 생성 로직 (고정 파트너 유지 횟수 및 중복 방지 강화)
    """
    all_matches = []
    fixed_partners = fixed_partners or []
    
    # 조별 플레이어 분리
    groups = {}
    for p in players_info:
        g = p['group']
        if g not in groups: groups[g] = []
        groups[g].append(p)

    # 고정 파트너 경기 횟수 추적
    pair_match_counts = {tuple(sorted(pair)): 0 for pair in fixed_partners}

    for g_name, g_players in groups.items():
        courts = group_court_map.get(g_name, [])
        if not courts or len(g_players) < 4: continue
        
        match_counts = {p['name']: 0 for p in g_players}
        rest_counts = {p['name']: 0 for p in g_players}
        partner_history = {p['name']: set() for p in g_players}
        
        start_dt = datetime.strptime("19:30", "%H:%M") 
        duration = 30
        
        for r in range(1, 15): # 최대 15라운드까지 시도
            r_time = (start_dt + timedelta(minutes=(r-1)*duration)).strftime("%H:%M")
            
            # 1. 이번 라운드 참여 가능 인원 (시간 및 경기 수 조건)
            available = []
            for p in g_players:
                p_s, p_e = p['times']
                if p_s <= r_time < p_e and match_counts[p['name']] < target_matches:
                    available.append(p)
            
            if len(available) < 4:
                continue
            
            # 경기 수가 적은 사람 우선, 동일 경기 수라면 휴식 횟수가 많은 사람(덜 보채는 사람) 우선
            # -> 반대로 말하면 휴식 횟수가 적은 사람이 먼저 쉬게 됨
            available.sort(key=lambda x: (match_counts[x['name']], -rest_counts[x['name']]))
            used_in_round = set()
            
            for court_num in courts:
                current_pool = [p for p in available if p['name'] not in used_in_round]
                if len(current_pool) < 4: break
                
                # p1: 가장 경기 적은 사람
                p1_info = current_pool[0]
                p1 = p1_info['name']
                
                # p2: 파트너 결정
                p2_info = None
                # A. 고정 파트너 우선 확인 (설정된 게임 수 이하인 경우만)
                for pair in fixed_partners:
                    if p1 in pair:
                        pair_key = tuple(sorted(pair))
                        if pair_match_counts.get(pair_key, 0) < fixed_partner_games:
                            other_name = pair[0] if pair[1] == p1 else pair[1]
                            other_info = next((p for p in current_pool if p['name'] == other_name), None)
                            if other_info:
                                p2_info = other_info
                                pair_match_counts[pair_key] += 1
                                break
                
                # B. 고정 파트너가 없거나 횟수 초과, 혹은 가용하지 않으면 중복 없는 사람 우선
                if not p2_info:
                    p2_candidates = [p for p in current_pool[1:] if p['name'] not in partner_history[p1]]
                    if p2_candidates:
                        p2_candidates.sort(key=lambda x: match_counts[x['name']])
                        p2_info = p2_candidates[0]
                    else:
                        p2_info = current_pool[1] # 어쩔 수 없는 경우
                
                p2 = p2_info['name']
                
                # p3, p4: 상대팀 결정 (컨셉 반영)
                remaining = [p for p in current_pool if p['name'] not in [p1, p2]]
                
                def get_concept_score(p_inf):
                    if "YB" in concept: # 생년월일 기반 (늦을수록 YB)
                        bd = p_inf.get("birthdate", "1900-01-01")
                        return bd
                    if "MBTI" in concept: return p_inf.get("mbti", "I")
                    if "입상자" in concept: return "W" if p_inf.get("achievements") else "N"
                    return 0

                p1p2_score = get_concept_score(p1_info)
                # 컨셉이 같으면 팀이 될 확률을 조정 (YB/OB 등)
                remaining.sort(key=lambda x: (get_concept_score(x) == p1p2_score, match_counts[x['name']]))
                
                p3_info, p4_info = remaining[0], remaining[1]
                p3, p4 = p3_info['name'], p4_info['name']
                
                # 기록 업데이트
                partner_history[p1].add(p2); partner_history[p2].add(p1)
                partner_history[p3].add(p4); partner_history[p4].add(p3)
                
                match_counts[p1] += 1; match_counts[p2] += 1
                match_counts[p3] += 1; match_counts[p4] += 1
                
                used_in_round.update([p1, p2, p3, p4])
                
                all_matches.append({
                    "group": g_name, "round": r, "court": court_num,
                    "team1": [p1, p2], "team2": [p3, p4],
                    "score1": 0, "score2": 0, "status": "pending",
                    "pair_round": pair_match_counts.get(pair_key) if p2_info and any(p1 in pair for pair in fixed_partners) else None
                })

            # 라운드 종료 후 쉬는 사람들의 휴식 횟수 증가
            for p in available:
                if p['name'] not in used_in_round:
                    rest_counts[p['name']] += 1

    return all_matches

def get_rankings_v3(matches, players_info):
    """
    전체 통합 순위 및 조별 순위를 한 번에 산출
    """
    overall = get_overall_rankings(matches, players_info)
    
    # 조별 분리
    groups = {}
    for p in players_info:
        g = p.get('group', 'A')
        if g not in groups: groups[g] = []
        groups[g].append(p['name'])
        
    by_group = {}
    for g_name, g_members in groups.items():
        # overall에서 해당 조 멤버만 추출 후 순위 재매김
        g_results = [dict(r) for r in overall if r["이름"] in g_members]
        for i, r in enumerate(g_results): r["순위"] = i + 1
        by_group[g_name] = g_results
        
    return overall, by_group

def get_overall_rankings(matches, players_info):
    """
    조 구분 없이 전체 통합 순위 산정
    """
    stats = {p['name']: {
        "wins": 0, "losses": 0, "pts_diff": 0, "matches": 0,
        "birthdate": p.get("birthdate", "1900-01-01"), "is_guest": p.get("is_guest", False)
    } for p in players_info}
    
    for m in matches:
        if m["status"] == "complete":
            s1, s2 = m["score1"], m["score2"]
            t1, t2 = m["team1"], m["team2"]
            w_team, l_team = (t1, t2) if s1 > s2 else (t2, t1)
            diff = abs(s1 - s2)
            
            for p in w_team:
                if p in stats:
                    stats[p]["wins"] += 1; stats[p]["pts_diff"] += diff; stats[p]["matches"] += 1
            for p in l_team:
                if p in stats:
                    stats[p]["losses"] += 1; stats[p]["pts_diff"] -= diff; stats[p]["matches"] += 1
                    
    results = []
    for name, s in stats.items():
        results.append({
            "이름": name, "승": s["wins"], "패": s["losses"],
            "득실차": s["pts_diff"], "경기수": s["matches"],
            "birthdate": s["birthdate"], "is_guest": s["is_guest"]
        })
    
    # 정렬: 승(D) -> 득실차(D) -> 생년월일(D, 늦을수록 연소자)
    results.sort(key=lambda x: (x["승"], x["득실차"], x["birthdate"]), reverse=True)
    for i, val in enumerate(results): val["순위"] = i + 1
    return results

def calculate_rewards_v2(overall_rankings, reward_1st=10000, fine_25=3000, fine_last_25=5000):
    """
    통합 순위 기반 상벌금 계산 (커스텀 금액 반영)
    - reward_1st: 1등 상금
    - fine_25: 하위 25% 벌금 (3000원)
    - fine_last_25: 최하위 25% 벌금 (5000원)
    """
    n = len(overall_rankings)
    fines = {} # {name: amount}
    reward = {} # {name: amount}
    
    if n == 0: return fines, reward
    
    # 🥇 1위 상금 (게스트 제외)
    top_player = overall_rankings[0]
    if not top_player["is_guest"]:
        reward[top_player["이름"]] = reward_1st
    
    # 💸 벌금 대상자 (하위 50%를 25% / 25%로 나눔)
    # 전체 n에서 하위 50% (올림)
    total_fine_count = math.ceil(n / 2)
    
    # 그 중 최하위 25% (올림) -> 5000원
    lowest_25_count = math.ceil(n * 0.25)
    # 나머지 (하위 25%) -> 3000원
    middle_25_count = total_fine_count - lowest_25_count
    
    fine_list = overall_rankings[-total_fine_count:]
    
    # fine_list는 순위 높은 순으로 되어 있음 (ex: 6등, 7등, 8등, 9등, 10등, 11등)
    # 하위 25% (앞쪽) -> middle_25_count 만큼 3000원
    # 최하위 25% (뒤쪽) -> lowest_25_count 만큼 5000원
    
    for i, p in enumerate(fine_list):
        if i < middle_25_count:
            fines[p["이름"]] = fine_25
        else:
            fines[p["이름"]] = fine_last_25
            
    return fines, reward
