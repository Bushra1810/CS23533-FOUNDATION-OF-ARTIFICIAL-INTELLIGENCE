# AI Team Formation Tool

## What it does
1. **Logic engine (forward chaining):** Enter each person's skills, attendance,
   portfolio status, and leadership experience. A rule engine derives which
   roles (Developer, Designer, TeamLead, Writer, ProjectManager) each person
   is eligible for — showing the full reasoning trace.
2. **CSP solver (backtracking):** Set team constraints (size limits, required
   skills OR required earned roles per team, who must/must-not be together).
   The solver forms fair, balanced teams automatically. If no perfect
   arrangement exists, it relaxes the requirement and reports exactly what's
   missing rather than silently failing.
3. **Fairness metrics:** See team size balance and skill diversity balance
   across the formed teams.

## How to run
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python -m streamlit run app.py`
3. Open the link it prints (usually http://localhost:8501)

## Project structure
- `app.py` — Streamlit UI
- `modules/team_solver.py` — CSP solver (backtracking, symmetry breaking,
  constraint propagation) and fairness metrics
- `modules/eligibility_engine.py` — forward-chaining rule engine for role
  eligibility

## Technique notes
- **Forward chaining:** starting from known facts about a person, rules fire
  repeatedly until no new facts can be derived (fixed point) — including
  multi-step cascades (e.g., leadership + high attendance -> TeamLead ->
  combined with PM skill -> ProjectManager).
- **CSP:** students who must be together are merged via union-find into a
  single unit; symmetry breaking (teams are interchangeable) and constraint
  propagation (skill/role coverage checked the moment a team fills up)
  make the backtracking search fast even for classroom-sized groups.
- Eligible roles derived by the Logic engine are fed directly into the CSP
  as constraints (e.g. "every team needs an eligible Team Lead"), so the
  two units work together as one pipeline rather than as separate demos.
