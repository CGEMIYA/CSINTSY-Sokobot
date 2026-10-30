"""
sokobot.py

Desc:
    g(n) = steps taken so far
    h(n) = estimated guesses left

Program Flow:
    solveSokobanPuzzle() -> read board -> reverse BFS -> A* -> moves
    heuristic()          -> estimate remaining crate pushes
    reachable_paths()    -> BFS for legal player walking paths

Usage:
    Run from the repository root:
        .\\sokobot.bat testlevel
        .\\sokobot.bat testlevel --gui

References:
    https://timallanwheeler.com/blog/2022/01/19/basic-search-algorithms-on-sokoban/
    https://www.asiergoni.com/projects/weighted-sokoban-solver-a     
"""

from collections import deque
from functools import lru_cache
from heapq import heappush, heappop
from itertools import count
from math import inf
import time

# ==================== MOVEMENT DIRECTIONS ====================
DIRECTIONS = ((-1, 0, 'u'), (1, 0, 'd'), (0, -1, 'l'), (0, 1, 'r'))


class SokoBot:
    def solveSokobanPuzzle(self, width, height, mapData, itemsData):
        # ==================== TIME LIMIT ====================
        start = time.monotonic()
        deadline = start + 14.5  

        # ==================== READ BOARD ====================
        walls, goals, crates = set(), set(), set()
        player = None
        for r in range(height):
            for c in range(width):
                pos = (r, c)
                if mapData[r][c] == '#':
                    walls.add(pos)
                elif mapData[r][c] == '.':
                    goals.add(pos)
                if itemsData[r][c] == '$':
                    crates.add(pos)
                elif itemsData[r][c] == '@':
                    player = pos

        if player is None or len(crates) != len(goals):
            return ''
        if crates == goals:
            return ''

        floor = {(r, c) for r in range(height) for c in range(width)} - walls
        goals_list = sorted(goals)

        # ==================== REVERSE-PUSH BFS (for crates) ====================
        # how many pushes away every tile is start from goal tiles
        reverse_distances = []
        for goal in goals_list:
            d = {goal: 0}
            q = deque([goal])
            while q:
                curr = q.popleft()
                for dr, dc, _ in DIRECTIONS:
                    prev = (curr[0] - dr, curr[1] - dc)
                    stance = (prev[0] - dr, prev[1] - dc)
                    if prev in floor and stance in floor and prev not in d:
                        d[prev] = d[curr] + 1
                        q.append(prev)
            reverse_distances.append(d)

        # finds tiles that could lead to softlock/corners
        dead_squares = {
            p for p in floor
            if p not in goals and all(p not in d for d in reverse_distances)
        }

        # ==================== A* HEURISTIC: h(n) ====================
        @lru_cache(maxsize=200000)
        def heuristic(ordered_crates):
            # estimate remaining pushes by matching crates to goals
            n = len(ordered_crates)
            # distance from every crate to every goal
            costs = [
                [reverse_distances[j].get(crate, inf) for j in range(n)]
                for crate in ordered_crates
            ]
            if any(all(value == inf for value in row) for row in costs):
                return inf

            # binary tracker for which goals are already taken
            dp = {0: 0}
            for i in range(n):
                next_dp = {}
                for mask, base in dp.items():
                    for j in range(n):
                        if not (mask & (1 << j)) and costs[i][j] != inf:
                            m = mask | (1 << j)
                            next_dp[m] = min(
                                next_dp.get(m, inf), base + costs[i][j]
                            )
                dp = next_dp
                if not dp:
                    return inf
            return dp.get((1 << n) - 1, inf)

        # ==================== PLAYER WALKING BFS ====================
        def reachable_paths(position, occupied):
            # BFS: find shortest walking paths without hitting walls/crates
            paths = {position: ''}
            q = deque([position])
            while q:
                cur = q.popleft()
                for dr, dc, move in DIRECTIONS:
                    nxt = (cur[0] + dr, cur[1] + dc)
                    if nxt in floor and nxt not in occupied and nxt not in paths:
                        paths[nxt] = paths[cur] + move
                        q.append(nxt)
            return paths

        # ==================== A* INITIAL STATE ====================
        # track location of player and crates
        initial_crates = tuple(sorted(crates))
        initial_h = heuristic(initial_crates)
        if initial_h == inf:
            return ''

        serial = count()
        # Heap priority: f(n) = g(n) + h(n)
        heap = [(initial_h, 0, next(serial), player, initial_crates)]
        best = {(player, initial_crates): 0}
        parents = {}  # for path reconstruction

        # ==================== MAIN A* SEARCH LOOP ====================
        while heap:
            if time.monotonic() >= deadline:
                return ''

            estimate, cost, _, current_player, current_crates = heappop(heap)
            state = (current_player, current_crates)

            # ifnore old paths
            if cost != best.get(state):
                continue

            # wincon check
            if set(current_crates) == goals:
                segments = []
                while state in parents:
                    previous, segment = parents[state]
                    segments.append(segment)
                    state = previous
                return ''.join(reversed(segments))

            occupied = set(current_crates)
            paths = reachable_paths(current_player, occupied)

            # ==================== GENERATE SUCCESSORS (LEGAL PUSHES) ====================
            for crate in current_crates:
                for dr, dc, move in DIRECTIONS:
                    behind = (crate[0] - dr, crate[1] - dc)
                    destination = (crate[0] + dr, crate[1] + dc)

                    # check for open space to push
                    if (behind not in paths
                            or destination not in floor
                            or destination in occupied
                            or destination in dead_squares):
                        continue


                    changed = tuple(sorted((occupied - {crate}) | {destination}))
                    h = heuristic(changed)
                    if h == inf:
                        continue

                    next_state = (crate, changed)
                    segment = paths[behind] + move  # walk + push
                    next_cost = cost + len(segment)  # g(n)

                    # update if path has a lower cost
                    if next_cost < best.get(next_state, inf):
                        best[next_state] = next_cost
                        parents[next_state] = (state, segment)
                        heappush(
                            heap,
                            (next_cost + h, next_cost, next(serial), crate, changed)
                        )
        return ''  # cant solve