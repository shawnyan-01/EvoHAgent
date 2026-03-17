from typing import Optional, List, Tuple
import math
from agents.planet_wars_agent import PlanetWarsPlayer
from core.game_state import GameState, Action, Player, GameParams

def policy1(
    N: int,
    pid: List[int],
    owner: List[int],
    ships: List[float],
    growth: List[float],
    x: List[float],
    y: List[float],
    busy: List[int],
    game_tick: int,
    player_code: int,
    speed: float
    ) -> Optional[Tuple[int, int, float]]:
       

        def distance(a: int, b: int) -> float:
            return ((x[a] - x[b]) ** 2 + (y[a] - y[b]) ** 2) ** 0.5

        candidates = []

        for i in range(N):
            if owner[i] == player_code and busy[i] == 0 and ships[i] > 1.0:
                nearest_enemy = None
                min_dist = float("inf")

                for j in range(N):
                    if owner[j] == -1:
                        d = distance(i, j)
                        if d < min_dist:
                            min_dist = d
                            nearest_enemy = j

                if nearest_enemy is not None:
                    travel_ticks = min_dist / speed
                    required = ships[nearest_enemy] + growth[nearest_enemy] * travel_ticks + 1.0

                    if ships[i] > required:
                        score = growth[i] / (min_dist + 1.0)
                        candidates.append((score, i, nearest_enemy, required))

        if not candidates:
            return None

        _, src, dst, req = max(candidates, key=lambda c: c[0])

        num = min(req, ships[src] - 1.0)
        if num < 1.0:
            return None

        return (src, dst, num)
from typing import List, Optional, Tuple

def policy2(
    N: int,
    pid: List[int],
    owner: List[int],
    ships: List[float],
    growth: List[float],
    x: List[float],
    y: List[float],
    busy: List[int],
    game_tick: int,
    player_code: int,
    speed: float
) -> Optional[Tuple[int, int, float]]:
    """
    Sends ships from the strongest self-owned planet to the nearest enemy planet,
    only if the attack is expected to succeed after accounting for enemy growth
    during travel. Also performs a simple local-defense check: if a nearby friendly
    planet is weak, do not launch.

    Returns:
        None or (source_id, destination_id, num_ships)
        Note: source_id/destination_id are indices [0..N-1] (same as your code).
    """

    def dist(a: int, b: int) -> float:
        return ((x[a] - x[b]) ** 2 + (y[a] - y[b]) ** 2) ** 0.5

    # 1) Choose a source: strongest self planet that can launch now
    self_planets = [i for i in range(N) if owner[i] == player_code and busy[i] == 0 and ships[i] > 0]
    if not self_planets:
        return None
    source = max(self_planets, key=lambda i: ships[i])

    # 2) Choose a target: nearest enemy to the source
    enemy_planets = [i for i in range(N) if owner[i] == -1]
    if not enemy_planets:
        return None
    target = min(enemy_planets, key=lambda i: dist(source, i))

    if source == target:
        return None

    # 3) Attack feasibility: enemy will grow while fleet travels
    travel_ticks = dist(source, target) / speed
    required_ships = ships[target] + growth[target] * travel_ticks + 1.0  # +1 as safety margin

    # Need enough ships to win, and also keep at least 1 ship at home (common legality/sanity)
    if ships[source] <= required_ships + 1.0:
        return None

    # 4) Local defense heuristic: if a nearby friendly planet is weak, don't launch
    for i in range(N):
        if owner[i] == player_code and i != source:
            if dist(i, source) < 25.0 and ships[i] < 8.0:
                return None

    # 5) Send exactly the required ships, but do not exceed available ships minus 1
    num_ships = min(required_ships, ships[source] - 1.0)
    if num_ships < 1.0:
        return None

    return (source, target, num_ships)

    # If your environment expects real planet IDs rather than indices, use:
    # return (pid[source], pid[target], num_ships)

def policy3(
    N: int,
    pid: list[int],
    owner: list[int],
    ships: list[float],
    growth: list[float],
    x: list[float],
    y: list[float],
    busy: list[int],
    game_tick: int,
    player_code: int,
    speed: float,
):
    """

    Explanation (no behavior changes):
        - Iterates over each self-owned, non-busy planet with ships > 1.0 as a candidate source.
        - For each source, finds:
            * the nearest enemy planet (closest_enemy, min_enemy_dist)
            * the nearest friendly planet (closest_friend, min_self_dist)
        - If no enemy exists, skip the source.
        - Estimates travel time = distance_to_enemy / speed.
        - Computes ships required to capture the closest enemy:
            required = enemy_ships + enemy_growth * travel + 1.0
        - Computes surplus = source_ships - required; if surplus <= 0, skip.
        - Computes three terms:
            * safety = source_ships / (min_enemy_dist + 1.0)
            * defensive_pressure = (friendly_ships / (min_self_dist + 1.0)) if a friendly exists else 0
            * expansion_potential = (enemy_growth * surplus) / (required + 1.0)
        - Combined score = safety + expansion_potential + defensive_pressure.
        - Chooses the source with the highest combined score, and sets action:
            send_amount = min(source_ships - 1.0, required * 1.2)
            best_action = (src, closest_enemy, send_amount)
        - Returns best_action (or None if nothing qualifies).
    """
    best_action = None
    best_combined_score = -float("inf")

    for src in range(N):
        if owner[src] != player_code or busy[src] != 0 or ships[src] <= 1.0:
            continue

        min_enemy_dist = float("inf")
        closest_enemy = -1
        min_self_dist = float("inf")
        closest_friend = -1

        for other in range(N):
            if other == src:
                continue
            dist = ((x[src] - x[other]) ** 2 + (y[src] - y[other]) ** 2) ** 0.5
            if owner[other] == -1 and dist < min_enemy_dist:
                min_enemy_dist = dist
                closest_enemy = other
            if owner[other] == player_code and dist < min_self_dist:
                min_self_dist = dist
                closest_friend = other

        if closest_enemy == -1:
            continue

        travel = min_enemy_dist / speed
        required = ships[closest_enemy] + growth[closest_enemy] * travel + 1.0
        surplus = ships[src] - required
        if surplus <= 0.0:
            continue

        defensive_pressure = 0.0
        if min_self_dist != float("inf"):
            defensive_pressure = ships[closest_friend] / (min_self_dist + 1.0)

        safety = ships[src] / (min_enemy_dist + 1.0)
        expansion_potential = (growth[closest_enemy] * surplus) / (required + 1.0)
        combined_score = safety + expansion_potential + defensive_pressure

        if combined_score > best_combined_score:
            best_combined_score = combined_score
            send_amount = min(ships[src] - 1.0, required * 1.2)
            best_action = (src, closest_enemy, send_amount)

    return best_action


def policy4(
    N: int,
    pid: List[int],
    owner: List[int],
    ships: List[float],
    growth: List[float],
    x: List[float],
    y: List[float],
    busy: List[int],
    game_tick: int,
    player_code: int,
    speed: float,
) -> Optional[Tuple[int, int, float]]:
    """
    Implements:
    - For each self-owned non-busy planet, evaluate defensive vulnerability and offensive opportunity.
    - If the most threatened self-owned planet exceeds a vulnerability threshold, reinforce it.
    - Otherwise, attack cautiously from the safest self-owned planet to the most valuable capturable target.

    Returns:
        None
            -> do nothing
        or (source_id, destination_id, num_ships)
            -> launch fleet
    """

    # --------- helpers ----------
    def dist(i: int, j: int) -> float:
        return math.hypot(x[i] - x[j], y[i] - y[j])

    def clamp_send(src: int, amount: float) -> Optional[float]:
        """Return a legal send amount, or None if impossible."""
        max_send = ships[src] - 1.0
        if max_send < 1.0:
            return None
        a = float(amount)
        if a < 1.0:
            a = 1.0
        if a > max_send:
            a = max_send
        if a < 1.0:
            return None
        return a

    # --------- collect sets ----------
    my_planets = [i for i in range(N) if owner[i] == player_code]
    enemy_planets = [i for i in range(N) if owner[i] == -1]
    neutral_planets = [i for i in range(N) if owner[i] == 0]

    # Only planets that can launch this tick and have enough ships
    launchable = [
        i for i in my_planets
        if busy[i] == 0 and ships[i] >= 2.0
    ]

    if not launchable:
        return None

    # If no opponents/targets exist, nothing to do
    if not enemy_planets and not neutral_planets:
        return None

    # --------- 1) defensive vulnerability (per my planet) ----------
    # We define vulnerability as accumulated enemy "pressure" on that planet.
    # pressure from enemy e: ships[e] / (dist+1)
    vulnerability = [0.0] * N
    closest_enemy_dist = [float("inf")] * N
    closest_enemy = [-1] * N

    for p in my_planets:
        total_threat = 0.0
        ce = -1
        cd = float("inf")
        for e in enemy_planets:
            d = dist(p, e)
            if d < cd:
                cd = d
                ce = e
            total_threat += ships[e] / (d + 1.0)
        vulnerability[p] = total_threat
        closest_enemy[p] = ce
        closest_enemy_dist[p] = cd

    # pick most threatened planet (must exist)
    threatened = None
    threatened_score = -float("inf")
    for p in my_planets:
        # normalize by local strength to represent "vulnerability"
        # larger threat and smaller stationed ships => more vulnerable
        v = vulnerability[p] / (ships[p] + 1.0)
        if v > threatened_score:
            threatened_score = v
            threatened = p

    # pick safest launch planet: low vulnerability, high reserve, not same as threatened
    safest = None
    safest_score = -float("inf")
    for s in launchable:
        # higher is safer: more ships, more growth, less threat
        safe = (ships[s] + 0.5 * growth[s]) / (vulnerability[s] + 1.0)
        if safe > safest_score:
            safest_score = safe
            safest = s

    # --------- 2) build defensive reinforce action (if needed) ----------
    # vulnerability threshold: use your original "1.5" spirit, but now on normalized vulnerability
    VULN_THRESHOLD = 1.5

    defensive_action = None  # (src, dst, send, score)
    if threatened is not None and safest is not None and threatened != safest:
        # Reinforce amount proportional to threat, but must be legal from source
        # You used total_threat*2; we keep similar scale.
        raw_send = vulnerability[threatened] * 2.0

        send = clamp_send(safest, raw_send)
        if send is not None:
            # Defensive score: threatened_score * growth(threatened) to prioritize valuable planets
            dscore = threatened_score * (growth[threatened] + 1.0)
            defensive_action = (safest, threatened, send, dscore)

    # --------- 3) offensive opportunity: choose safest->best capturable target ----------
    # targets include enemy + neutral, but treat required ships differently:
    # - enemy: need ships[target] + growth[target]*travel + 1
    # - neutral: typically no growth (growth can exist though), still use same formula but owner==0
    offensive_action = None  # (src, dst, send, score)

    # candidate sources: prefer safer ones (as algorithm text says "safest")
    # we evaluate each source against best target.
    targets = enemy_planets + neutral_planets

    for src in launchable:
        # skip if src is extremely threatened and can't spare ships
        for dst in targets:
            if dst == src:
                continue

            d = dist(src, dst)
            travel_time = d / speed if speed > 0 else float("inf")
            if not math.isfinite(travel_time):
                continue

            # required to win on arrival
            required = ships[dst] + growth[dst] * travel_time + 1.0

            surplus = ships[src] - required
            if surplus <= 0.0:
                continue

            # "most valuable capturable target": high growth / low required
            target_value = (growth[dst] + 1.0) / (required + 1.0)

            # "cautious attack": require a small margin and penalize distance
            oscore = (surplus * target_value) / (d + 1.0)

            # send slightly above required, but never all ships
            raw_send = required * 1.1
            send = clamp_send(src, raw_send)
            if send is None:
                continue

            if (offensive_action is None) or (oscore > offensive_action[3]):
                offensive_action = (src, dst, send, oscore)

    # --------- 4) choose action ----------
    # If vulnerability exceeds threshold, prefer defense; else offense.
    if threatened is not None and threatened_score > VULN_THRESHOLD and defensive_action is not None:
        return (defensive_action[0], defensive_action[1], defensive_action[2])

    if offensive_action is not None:
        return (offensive_action[0], offensive_action[1], offensive_action[2])

    return None
def policy5(N: int, pid: list[int], owner: list[int], ships: list[float], growth: list[float], 
           x: list[float], y: list[float], busy: list[int], game_tick: int, 
           player_code: int, speed: float):
    """
    这个策略算法的核心思想是：选择自己拥有的、不繁忙的、拥有足够飞船的、增长率最高的星球，
    向最近的一个敌人星球派遣舰队，派遣的舰队数量考虑了敌人增长和旅行时间，并保留少量备用飞船。
    
    Args:
        N (int): 星球数量
        pid (list[int]): 星球ID（可作为索引使用，范围[0, N-1]）
        owner (list[int]): 星球所有权代码
            +1 = 自己拥有
            0 = 中立
            -1 = 敌人拥有
        ships (list[float]): 每个星球上的飞船数量（可能是小数）
        growth (list[float]): 每个星球每tick的增长率
        x (list[float]): 每个星球的X坐标
        y (list[float]): 每个星球的Y坐标
        busy (list[int]): 繁忙标志
            1 = 星球本tick不能发射舰队（有出发的运输船）
            0 = 星球可以发射
        game_tick (int): 当前tick索引
        player_code (int): 总是+1（从自己的角度）
        speed (float): 舰队每tick的移动速度

    Returns:
        None: 本tick不执行任何操作
        或者 (source_id: int, destination_id: int, num_ships: float): 
            从source_id向destination_id发射num_ships艘飞船
    """
    
    # 第一步：选择最佳发射星球
    best_source = None
    best_source_growth = -1.0
    
    # 遍历所有星球，选择满足条件的最佳发射星球
    for i in range(N):
        # 条件：自己拥有、不繁忙、有至少1.0艘飞船
        if owner[i] == player_code and busy[i] == 0 and ships[i] > 1.0:
            # 选择增长率最高的星球
            if growth[i] > best_source_growth:
                best_source_growth = growth[i]
                best_source = i
    
    # 如果没有找到合适的发射星球，返回None（不执行任何操作）
    if best_source is None:
        return None
    
    # 第二步：选择最佳目标星球（最近的敌人星球）
    best_target = None
    best_dist = float('inf')
    
    for i in range(N):
        # 只考虑敌人拥有的星球
        if owner[i] == -1:
            # 计算欧几里得距离
            dist = math.sqrt((x[best_source] - x[i])**2 + (y[best_source] - y[i])**2)
            if dist < best_dist:
                best_dist = dist
                best_target = i
    
    # 如果没有找到目标星球，返回None
    if best_target is None:
        return None
    
    # 第三步：计算需要派遣的飞船数量
    # 计算旅行时间（tick数）
    travel_ticks = best_dist / speed
    
    # 计算需要的飞船数量 = 目标当前飞船 + 旅行期间敌人的增长 + 0.5的安全余量
    required = ships[best_target] + travel_ticks * growth[best_target] + 0.5
    
    # 第四步：决定实际派遣的飞船数量
    if required <= ships[best_source] - 0.5:
        # 如果发射星球有足够飞船，派遣计算出的所需数量
        send_ships = required
    else:
        # 如果不够，派遣尽可能多的飞船（保留0.5作为备用）
        if ships[best_source] > 1.0:
            send_ships = ships[best_source] - 0.5
        else:
            # 如果发射星球只有1.0或更少飞船，不发射（保留至少1.0）
            return None
    
    return (best_source, best_target, send_ships)

    
class EvoHAgent(PlanetWarsPlayer):
    """Wrap a numeric policy into a PlanetWars-style agent.

    Numeric policy signature:
        policy(N, pid, owner, ships, growth, x, y, busy, game_tick, player_code)
            -> None OR (source_id:int, dest_id:int, num_ships:float)
    """

    def __init__(self):

        self.player: Optional[Player] = None
        self.params: Optional[GameParams] = None


    def prepare_to_play_as(self, player: Player, params: GameParams):
        self.player = player
        self.params = params
    from typing import List, Optional, Tuple

    
    def get_agent_type(self) -> str:
        return "LLM4AD-NumericPolicyAgent2(ActionWrapped)"

    def get_action(self, game_state: GameState) -> Action:
        if self.player is None:
            return Action.do_nothing()

        planets = game_state.planets
        N = len(planets)

        pid = [0] * N
        owner = [0] * N
        ships = [0.0] * N
        growth = [0.0] * N
        x = [0.0] * N
        y = [0.0] * N
        busy = [0] * N
        speed = float(self.params.transporter_speed) if self.params is not None else 1.0

        # ---- unpack objects -> primitives
        for i in range(N):
            p = planets[i]
            pid[i] = int(p.id)
            ships[i] = float(p.n_ships)
            growth[i] = float(p.growth_rate)
            x[i] = float(p.position.x)
            y[i] = float(p.position.y)
            busy[i] = 1 if (p.transporter is not None) else 0

            if p.owner == self.player:
                owner[i] = 1
            elif p.owner == Player.Neutral:
                owner[i] = 0
            else:
                owner[i] = -1

        # ---- numeric policy -> primitive action tuple
        out = policy5(N, pid, owner, ships, growth, x, y, busy, int(game_state.game_tick), 1,speed)

        # ---- convert to Action
        if out is None:
            return Action.do_nothing()

        if not (isinstance(out, tuple) or isinstance(out, list)) or len(out) != 3:
            # If policy returns invalid format, treat as no-op (or raise to log)
            return Action.do_nothing()

        src, dst, num = out
        try:
            src = int(src)
            dst = int(dst)
            num = float(num)
        except Exception:
            return Action.do_nothing()

        return Action(
            player_id=self.player,
            source_planet_id=src,
            destination_planet_id=dst,
            num_ships=num,
        )
    def get_agent_type(self) -> str:
        return "EvoH Agent in Python"
