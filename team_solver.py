"""
Team Formation Solver — a Constraint Satisfaction Problem.

Variables: students (grouped into units when "must be together" pairs exist)
Domain: team IDs (0 .. num_teams-1)
Hard constraints:
  - Each team's size stays within [min_size, max_size]
  - "Must not be together" pairs are never placed in the same team
  - "Must be together" pairs are always placed in the same team (handled via
    union-find grouping, so they are assigned as a single unit)
Soft constraint (optimized, relaxed if truly infeasible):
  - Every "critical skill" is present in every team

Technique: Backtracking Search with symmetry breaking (team labels are
interchangeable, so we only ever open a new team ID one higher than the
highest already used — this collapses a huge number of equivalent branches)
and constraint checking at each assignment step (an incremental form of
constraint propagation).
"""
import time


class Student:
    def __init__(self, name, skills):
        self.name = name
        self.skills = set(skills)

    def __repr__(self):
        return f"{self.name}({','.join(sorted(self.skills))})"


def _union_find_groups(students, pairs_together):
    """Merge students that must be together into groups using union-find.
    Returns a list of groups, where each group is a list of Student objects."""
    parent = {s.name: s.name for s in students}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for a, b in pairs_together:
        if a in parent and b in parent:
            union(a, b)

    groups_map = {}
    for s in students:
        root = find(s.name)
        groups_map.setdefault(root, []).append(s)

    return list(groups_map.values())


def solve_team_formation(
    students,
    num_teams,
    min_team_size,
    max_team_size,
    critical_skills=None,
    pairs_together=None,
    pairs_apart=None,
    enforce_skill_coverage=True,
    max_nodes=20_000,
):
    """
    Solve the team-formation CSP.

    Returns a dict with: success, teams (list of lists of Student), stats,
    relaxed (bool, whether skill coverage had to be dropped), missing_skills
    (per-team list of skills that could not be covered, if relaxed).
    """
    critical_skills = critical_skills or []
    pairs_together = pairs_together or []
    pairs_apart = pairs_apart or []

    groups = _union_find_groups(students, pairs_together)
    # Variable ordering heuristic: place larger / more-constrained groups first
    # (more likely to cause failure early -> better pruning, similar in spirit
    # to the "most constrained variable" heuristic).
    apart_names = set()
    for a, b in pairs_apart:
        apart_names.add(a)
        apart_names.add(b)

    def group_degree(g):
        conflict_count = sum(1 for s in g if s.name in apart_names)
        return (conflict_count, len(g))

    groups.sort(key=group_degree, reverse=True)

    t0 = time.perf_counter()
    stats = {"nodes_visited": 0, "backtracks": 0}

    def attempt(check_skills):
        team_members = [[] for _ in range(num_teams)]
        team_name_sets = [set() for _ in range(num_teams)]

        def apart_conflict(team_idx, group):
            names_in_team = team_name_sets[team_idx]
            for s in group:
                for other_name in names_in_team:
                    pair = tuple(sorted((s.name, other_name)))
                    for a, b in pairs_apart:
                        if tuple(sorted((a, b))) == pair:
                            return True
            return False

        def backtrack(i, highest_used):
            stats["nodes_visited"] += 1
            if stats["nodes_visited"] > max_nodes:
                return False
            if i == len(groups):
                # check min size satisfied for all teams that received members,
                # and every team has at least min_team_size if fully used
                for t in range(num_teams):
                    size = len(team_members[t])
                    if size > 0 and size < min_team_size:
                        return False
                if check_skills:
                    for t in range(num_teams):
                        team_skills = set()
                        for s in team_members[t]:
                            team_skills |= s.skills
                        for crit in critical_skills:
                            if crit not in team_skills and len(team_members[t]) > 0:
                                return False
                return True

            group = groups[i]
            # symmetry breaking: only try team indices up to highest_used + 1
            max_team_to_try = min(num_teams - 1, highest_used + 1)
            for t in range(max_team_to_try + 1):
                if len(team_members[t]) + len(group) > max_team_size:
                    continue
                if apart_conflict(t, group):
                    continue

                team_members[t].extend(group)
                for s in group:
                    team_name_sets[t].add(s.name)
                new_highest = max(highest_used, t)

                # Constraint propagation: if this team just became full, check
                # skill coverage NOW instead of waiting for the full assignment
                # to complete. Pruning here avoids exploring the (often huge)
                # remaining search space when this team can never be fixed.
                team_now_full = len(team_members[t]) >= max_team_size
                prune = False
                if check_skills and team_now_full:
                    team_skills = set()
                    for s in team_members[t]:
                        team_skills |= s.skills
                    for crit in critical_skills:
                        if crit not in team_skills:
                            prune = True
                            break

                if not prune and backtrack(i + 1, new_highest):
                    return True

                for s in group:
                    team_name_sets[t].discard(s.name)
                for _ in group:
                    team_members[t].pop()
                stats["backtracks"] += 1

            return False

        found = backtrack(0, -1)
        return found, team_members

    found, team_members = attempt(check_skills=enforce_skill_coverage)
    relaxed = False
    missing_skills = []

    if not found and enforce_skill_coverage:
        # Relax the skill-coverage soft constraint and retry with hard constraints only.
        stats["nodes_visited"] = 0
        stats["backtracks"] = 0
        found, team_members = attempt(check_skills=False)
        relaxed = True

    result_teams = [t for t in team_members if t] if found else []

    if found and relaxed:
        for team in result_teams:
            team_skills = set()
            for s in team:
                team_skills |= s.skills
            missing = [c for c in critical_skills if c not in team_skills]
            missing_skills.append(missing)

    return {
        "success": found,
        "teams": result_teams,
        "relaxed": relaxed,
        "missing_skills": missing_skills,
        "nodes_visited": stats["nodes_visited"],
        "backtracks": stats["backtracks"],
        "time_taken": time.perf_counter() - t0,
    }


def compute_fairness_metrics(teams):
    """Compute simple balance/fairness metrics across the formed teams."""
    if not teams:
        return {}

    sizes = [len(t) for t in teams]
    avg_size = sum(sizes) / len(sizes)
    size_variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)

    skill_counts = []
    for team in teams:
        skills = set()
        for s in team:
            skills |= s.skills
        skill_counts.append(len(skills))
    avg_skills = sum(skill_counts) / len(skill_counts)
    skill_variance = sum((c - avg_skills) ** 2 for c in skill_counts) / len(skill_counts)

    return {
        "team_sizes": sizes,
        "avg_team_size": round(avg_size, 2),
        "team_size_variance": round(size_variance, 3),
        "unique_skills_per_team": skill_counts,
        "avg_unique_skills": round(avg_skills, 2),
        "skill_count_variance": round(skill_variance, 3),
    }
