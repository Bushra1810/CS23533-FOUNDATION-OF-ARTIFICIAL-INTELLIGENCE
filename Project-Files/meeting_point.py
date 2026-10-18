"""
Optimal Meeting Point Finder — Search algorithms (A* / Dijkstra) applied to a
real sub-problem: given a formed team, whose members are located at various
points on campus, find the single location that minimizes total (or maximum)
walking distance for the whole team to gather.
"""
import time
import heapq
from modules.campus_map import GRAPH, LOCATIONS


def _straight_line_heuristic(a, b):
    (x1, y1), (x2, y2) = LOCATIONS[a], LOCATIONS[b]
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def dijkstra(start, goal):
    """Uniform Cost Search / Dijkstra — guarantees the shortest walking path."""
    t0 = time.perf_counter()
    frontier = [(0, start)]
    cost_so_far = {start: 0}
    nodes_expanded = 0

    while frontier:
        cost, node = heapq.heappop(frontier)
        nodes_expanded += 1
        if node == goal:
            break
        for nbr, dist in GRAPH[node]:
            new_cost = cost_so_far[node] + dist
            if nbr not in cost_so_far or new_cost < cost_so_far[nbr]:
                cost_so_far[nbr] = new_cost
                heapq.heappush(frontier, (new_cost, nbr))

    return {
        "algorithm": "Dijkstra (UCS)",
        "distance": cost_so_far.get(goal),
        "nodes_expanded": nodes_expanded,
        "time_taken": time.perf_counter() - t0,
    }


def a_star(start, goal):
    """A* Search — uses straight-line distance heuristic for faster convergence."""
    t0 = time.perf_counter()
    frontier = [(0, start)]
    cost_so_far = {start: 0}
    nodes_expanded = 0

    while frontier:
        _, node = heapq.heappop(frontier)
        nodes_expanded += 1
        if node == goal:
            break
        for nbr, dist in GRAPH[node]:
            new_cost = cost_so_far[node] + dist
            if nbr not in cost_so_far or new_cost < cost_so_far[nbr]:
                cost_so_far[nbr] = new_cost
                priority = new_cost + _straight_line_heuristic(nbr, goal)
                heapq.heappush(frontier, (priority, nbr))

    return {
        "algorithm": "A*",
        "distance": cost_so_far.get(goal),
        "nodes_expanded": nodes_expanded,
        "time_taken": time.perf_counter() - t0,
    }


PATHFINDERS = {"A*": a_star, "Dijkstra (UCS)": dijkstra}


def find_best_meeting_point(member_locations, algorithm="A*", fairness="total"):
    """
    Given the locations of a team's members, evaluate every candidate location
    on the map as a possible meeting point, computing the shortest-path
    distance from each member to that candidate. Returns the best candidate
    under the chosen fairness criterion:
      - "total": minimizes the SUM of everyone's walking distance (most efficient overall)
      - "max":   minimizes the LONGEST individual walk (fairest to the worst-off member)
    """
    pathfind = PATHFINDERS[algorithm]
    t0 = time.perf_counter()
    total_nodes_expanded = 0
    candidate_scores = []

    for candidate in LOCATIONS:
        per_member = {}
        for member_loc in member_locations:
            if member_loc == candidate:
                per_member[member_loc] = per_member.get(member_loc, 0)  # 0 distance if already there
                continue
            result = pathfind(member_loc, candidate)
            total_nodes_expanded += result["nodes_expanded"]
            # if multiple members share the same home location, keep the (identical) distance
            per_member[member_loc] = result["distance"]

        distances = [per_member[m] for m in member_locations]
        total_dist = sum(distances)
        max_dist = max(distances)
        candidate_scores.append({
            "location": candidate,
            "total_distance": round(total_dist, 2),
            "max_distance": round(max_dist, 2),
            "per_member_distance": {m: per_member[m] for m in set(member_locations)},
        })

    key = "total_distance" if fairness == "total" else "max_distance"
    best = min(candidate_scores, key=lambda c: c[key])

    return {
        "best_location": best["location"],
        "total_distance": best["total_distance"],
        "max_distance": best["max_distance"],
        "per_member_distance": best["per_member_distance"],
        "all_candidates": sorted(candidate_scores, key=lambda c: c[key]),
        "algorithm": algorithm,
        "fairness_criterion": fairness,
        "total_nodes_expanded": total_nodes_expanded,
        "time_taken": time.perf_counter() - t0,
    }
