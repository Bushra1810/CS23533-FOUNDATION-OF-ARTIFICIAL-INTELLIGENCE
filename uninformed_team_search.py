"""Uninformed Search module (Unit I): BFS, DFS, and UCS for exploring student team allocations."""
from core.models import Person, Constraints, Assignment

class UninformedTeamSearch:
    def __init__(self, people: list[Person], constraints: Constraints):
        self.people = people
        self.constraints = constraints

    def search_team_formation(self, strategy: str = "BFS") -> tuple[Assignment | None, dict]:
        """
        Explores team assignment state space using uninformed search strategies:
        - BFS (Breadth-First Search)
        - DFS (Depth-First Search)
        - UCS (Uniform Cost Search)
        """
        # State representation: tuple of team assignments for each person index
        initial_state = tuple([-1] * len(self.people))
        
        # Priority queue or queue: (cost/depth, state, current_person_idx)
        if strategy == "DFS":
            stack = [(initial_state, 0)]
            nodes_visited = 0
            while stack:
                state, idx = stack.pop()
                nodes_visited += 1
                if idx == len(self.people):
                    if self._is_valid_assignment(state):
                        return self._build_assignment_obj(state), {"nodes": nodes_visited, "strategy": strategy}
                    continue

                for t_idx in range(self.constraints.num_teams):
                    new_state = list(state)
                    new_state[idx] = t_idx
                    stack.append((tuple(new_state), idx + 1))
        else:
            # BFS or UCS
            queue = [(0, initial_state, 0)]
            nodes_visited = 0
            while queue:
                cost, state, idx = queue.pop(0)
                nodes_visited += 1
                if idx == len(self.people):
                    if self._is_valid_assignment(state):
                        return self._build_assignment_obj(state), {"nodes": nodes_visited, "strategy": strategy}
                    continue

                for t_idx in range(self.constraints.num_teams):
                    new_state = list(state)
                    new_state[idx] = t_idx
                    # cost metric: imbalance penalty for UCS
                    step_cost = cost + self._state_cost(tuple(new_state), idx + 1)
                    queue.append((step_cost, tuple(new_state), idx + 1))

        return None, {"nodes": nodes_visited if 'nodes_visited' in locals() else 0, "strategy": strategy, "status": "failed"}

    def _is_valid_assignment(self, state: tuple[int, ...]) -> bool:
        teams = [[] for _ in range(self.constraints.num_teams)]
        for p_idx, t_idx in enumerate(state):
            if t_idx == -1:
                return False
            teams[t_idx].append(self.people[p_idx])

        for t in teams:
            if not (self.constraints.min_size <= len(t) <= self.constraints.max_size):
                return False
        return True

    def _state_cost(self, state: tuple[int, ...], assigned_count: int) -> float:
        # Cost function for UCS based on team size variance
        teams_count = [0] * self.constraints.num_teams
        for i in range(assigned_count):
            if state[i] != -1:
                teams_count[state[i]] += 1
        mean_sz = sum(teams_count) / self.constraints.num_teams
        variance = sum((c - mean_sz)**2 for c in teams_count)
        return variance

    def _build_assignment_obj(self, state: tuple[int, ...]) -> Assignment:
        person_to_team = {}
        teams = [[] for _ in range(self.constraints.num_teams)]
        for p_idx, t_idx in enumerate(state):
            p = self.people[p_idx]
            person_to_team[p.name] = t_idx
            teams[t_idx].append(p)
        return Assignment(person_to_team=person_to_team, teams=teams)