"""
AI-Powered Team Formation Tool
Uses a Constraint Satisfaction (backtracking) solver to split a group of people
into fair, balanced teams that respect real constraints.
"""

import sys
import os

# Force Python to look in the root D:\AI directory first
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st


import pandas as pd
import plotly.graph_objects as go

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from modules.team_solver import Student, solve_team_formation, compute_fairness_metrics
from modules.eligibility_engine import forward_chain, facts_from_profile
from modules.campus_map import LOCATIONS as CAMPUS_LOCATIONS
from modules.meeting_point import find_best_meeting_point
from modules.role_eligibility_backward import RoleEligibilityBackwardEngine
from modules.skill_gap_csp import SkillGapCSPSolver
st.set_page_config(page_title="AI Team Formation Tool", layout="wide")

st.title("👥 AI Team Formation Tool")
st.caption(
    "Enter a list of people with their skills, set your constraints, and let the solver "
    "form fair, balanced teams automatically."
)

SKILL_POOL = ["Python", "Design", "Writing", "PM", "ML", "Testing", "DevOps", "UX"]

DEFAULT_DATA = pd.DataFrame([
    {"Name": "Alice", "Skills": "Python, ML", "Attendance %": 92, "Portfolio Submitted": False, "Leadership Experience": True, "Location": "Hostel A"},
    {"Name": "Bob", "Skills": "Design", "Attendance %": 70, "Portfolio Submitted": True, "Leadership Experience": False, "Location": "Hostel B"},
    {"Name": "Carol", "Skills": "Python, Writing", "Attendance %": 88, "Portfolio Submitted": False, "Leadership Experience": False, "Location": "Library"},
    {"Name": "Dave", "Skills": "Design, PM", "Attendance %": 95, "Portfolio Submitted": True, "Leadership Experience": True, "Location": "Admin Block"},
    {"Name": "Eve", "Skills": "Writing", "Attendance %": 65, "Portfolio Submitted": False, "Leadership Experience": False, "Location": "Cafeteria"},
    {"Name": "Frank", "Skills": "ML, PM", "Attendance %": 80, "Portfolio Submitted": False, "Leadership Experience": False, "Location": "Sports Complex"},
    {"Name": "Grace", "Skills": "Python", "Attendance %": 55, "Portfolio Submitted": False, "Leadership Experience": False, "Location": "Lab Block"},
    {"Name": "Heidi", "Skills": "Design, Writing", "Attendance %": 91, "Portfolio Submitted": True, "Leadership Experience": False, "Location": "Auditorium"},
    {"Name": "Ivan", "Skills": "Testing, DevOps", "Attendance %": 78, "Portfolio Submitted": False, "Leadership Experience": False, "Location": "Parking Lot"},
    {"Name": "Judy", "Skills": "Python, Testing", "Attendance %": 89, "Portfolio Submitted": False, "Leadership Experience": False, "Location": "Food Court"},
    {"Name": "Karl", "Skills": "UX, Design", "Attendance %": 72, "Portfolio Submitted": True, "Leadership Experience": False, "Location": "Park"},
    {"Name": "Liam", "Skills": "ML, Python", "Attendance %": 96, "Portfolio Submitted": False, "Leadership Experience": True, "Location": "Main Gate"},
])

st.markdown("### 1. Enter People & Skills")
st.caption("Edit the table below — add/remove rows, and list skills comma-separated.")
edited_df = st.data_editor(
    DEFAULT_DATA, num_rows="dynamic", use_container_width=True, key="people_editor",
    column_config={
        "Location": st.column_config.SelectboxColumn(
            "Location", options=list(CAMPUS_LOCATIONS.keys()), required=True
        )
    },
)

st.markdown("### 2. Eligibility Check (Logic Engine)")
st.caption(
    "A forward-chaining rule engine derives which roles each person qualifies for, "
    "based on their skills, attendance, portfolio, and leadership experience."
)

eligibility_results = {}
role_pool = set()

for _, row in edited_df.iterrows():
    if not row["Name"]:
        continue
    skills = [s.strip() for s in str(row["Skills"]).split(",") if s.strip()]
    facts = facts_from_profile(
        skills,
        attendance_pct=float(row.get("Attendance %", 0) or 0),
        portfolio_submitted=bool(row.get("Portfolio Submitted", False)),
        leadership_experience=bool(row.get("Leadership Experience", False)),
    )
    result = forward_chain(facts)
    eligibility_results[row["Name"]] = result
    role_pool.update(result["eligible_roles"])

elig_df = pd.DataFrame([
    {"Name": name, "Eligible Roles": ", ".join(res["eligible_roles"]) if res["eligible_roles"] else "—"}
    for name, res in eligibility_results.items()
])
st.dataframe(elig_df, use_container_width=True, hide_index=True)

with st.expander("🔍 View reasoning trace for a person"):
    trace_person = st.selectbox("Person", list(eligibility_results.keys()) if eligibility_results else [])
    if trace_person:
        trace = eligibility_results[trace_person]["trace"]
        if trace:
            for step in trace:
                st.write(f"**{step['rule']}** — used `{', '.join(step['used_facts'])}` → derived `{step['derived']}`")
        else:
            st.write("No rules fired for this person (no roles derived).")

st.markdown("### 3. Set Team Constraints")
col1, col2, col3 = st.columns(3)
with col1:
    num_teams = st.number_input("Number of teams", min_value=2, max_value=10, value=3)
with col2:
    min_size = st.number_input("Min team size", min_value=1, max_value=10, value=3)
with col3:
    max_size = st.number_input("Max team size", min_value=1, max_value=15, value=5)

role_options = [f"Role:{r}" for r in sorted(role_pool)]
critical_skills = st.multiselect(
    "Critical skills/roles — every team should have at least one member with each",
    SKILL_POOL + role_options, default=["Python", "Design"]
)

all_names = [n for n in edited_df["Name"].tolist() if n]

col4, col5 = st.columns(2)
with col4:
    st.markdown("**Must be on the same team** (optional)")
    together_a = st.selectbox("Person A", ["(none)"] + all_names, key="tog_a")
    together_b = st.selectbox("Person B", ["(none)"] + all_names, key="tog_b")
with col5:
    st.markdown("**Must NOT be on the same team** (optional)")
    apart_a = st.selectbox("Person A", ["(none)"] + all_names, key="ap_a")
    apart_b = st.selectbox("Person B", ["(none)"] + all_names, key="ap_b")

pairs_together = [(together_a, together_b)] if together_a != "(none)" and together_b != "(none)" and together_a != together_b else []
pairs_apart = [(apart_a, apart_b)] if apart_a != "(none)" and apart_b != "(none)" and apart_a != apart_b else []

run = st.button("🧩 Form Teams", type="primary")

if run:
    students = []
    name_to_location = {}
    for _, row in edited_df.iterrows():
        if not row["Name"]:
            continue
        skills = [s.strip() for s in str(row["Skills"]).split(",") if s.strip()]
        # Merge in eligible roles (from the Logic engine) as extra "skills"
        # so they can be used directly as CSP critical-skill constraints.
        eligible_roles = eligibility_results.get(row["Name"], {}).get("eligible_roles", [])
        skills += [f"Role:{r}" for r in eligible_roles]
        students.append(Student(row["Name"], skills))
        name_to_location[row["Name"]] = row.get("Location", "Main Gate") or "Main Gate"

    if len(students) < num_teams * min_size:
        st.error(
            f"Not enough people ({len(students)}) for {num_teams} teams of at least "
            f"{min_size} each (need at least {num_teams * min_size})."
        )
    else:
        result = solve_team_formation(
            students, num_teams=num_teams, min_team_size=min_size, max_team_size=max_size,
            critical_skills=critical_skills, pairs_together=pairs_together, pairs_apart=pairs_apart,
        )
        st.session_state["team_result"] = result
        st.session_state["name_to_location"] = name_to_location

if "team_result" in st.session_state:
    result = st.session_state["team_result"]

    if not result["success"]:
        st.error(
            "No valid team arrangement could be found even after relaxing the skill "
            "requirement — try loosening team size limits or reducing constraints."
        )
    else:
        if result["relaxed"]:
            st.warning(
                "⚠️ Couldn't satisfy full critical-skill coverage for every team — "
                "the solver relaxed that requirement. See which skills are missing below."
            )
        else:
            st.success("✅ All constraints satisfied, including full critical-skill coverage.")

        st.markdown("#### 📊 Solver Performance")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nodes Visited", result["nodes_visited"])
        c2.metric("Backtracks", result["backtracks"])
        c3.metric("Time Taken", f"{result['time_taken']*1000:.2f} ms")

        st.markdown("#### 👥 Formed Teams")

        def pretty_skill(s):
            return f"🎖️ {s.split(':', 1)[1]}" if s.startswith("Role:") else s

        for i, team in enumerate(result["teams"], start=1):
            skills_covered = sorted(set().union(*[s.skills for s in team])) if team else []
            missing = result["missing_skills"][i - 1] if result["relaxed"] and i - 1 < len(result["missing_skills"]) else []
            title = f"Team {i} ({len(team)} members)"
            if missing:
                title += f" — ⚠️ missing: {', '.join(pretty_skill(m) for m in missing)}"
            with st.expander(title, expanded=True):
                team_df = pd.DataFrame([
                    {"Name": s.name, "Skills": ", ".join(pretty_skill(sk) for sk in sorted(s.skills))}
                    for s in team
                ])
                st.dataframe(team_df, use_container_width=True, hide_index=True)
                st.caption(f"Combined skills: {', '.join(pretty_skill(sk) for sk in skills_covered) if skills_covered else 'None'}")

        st.markdown("#### ⚖️ Fairness / Balance Metrics")
        metrics = compute_fairness_metrics(result["teams"])
        m1, m2 = st.columns(2)
        with m1:
            fig1 = go.Figure(go.Bar(
                x=[f"Team {i+1}" for i in range(len(metrics["team_sizes"]))],
                y=metrics["team_sizes"], marker_color="#5B8FF9"
            ))
            fig1.update_layout(title=f"Team Sizes (variance: {metrics['team_size_variance']})", height=350)
            st.plotly_chart(fig1, use_container_width=True)
        with m2:
            fig2 = go.Figure(go.Bar(
                x=[f"Team {i+1}" for i in range(len(metrics["unique_skills_per_team"]))],
                y=metrics["unique_skills_per_team"], marker_color="#5AD8A6"
            ))
            fig2.update_layout(title=f"Unique Skills per Team (variance: {metrics['skill_count_variance']})", height=350)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### 4. Optimal Meeting Point per Team (Search)")
        st.caption(
            "Using each team member's campus location, A*/Dijkstra search finds the best "
            "spot for the team to meet — either minimizing total walking distance for "
            "everyone, or minimizing the longest walk any single member has to make."
        )
        name_to_location = st.session_state.get("name_to_location", {})

        fairness_criterion = st.radio(
            "Optimize for", ["Minimize total walking distance", "Minimize longest individual walk (fairest)"],
            horizontal=True, key="meeting_fairness"
        )
        fairness_key = "total" if fairness_criterion.startswith("Minimize total") else "max"

        for i, team in enumerate(result["teams"], start=1):
            member_locations = [name_to_location.get(s.name, "Main Gate") for s in team]
            mp_result = find_best_meeting_point(member_locations, algorithm="A*", fairness=fairness_key)

            with st.expander(f"📍 Team {i} meeting point: {mp_result['best_location']}", expanded=(i == 1)):
                dist_df = pd.DataFrame([
                    {"Member": s.name, "Starting Location": name_to_location.get(s.name, "Main Gate"),
                     "Walking Distance to Meeting Point": mp_result["per_member_distance"].get(
                         name_to_location.get(s.name, "Main Gate"), 0)}
                    for s in team
                ])
                st.dataframe(dist_df, use_container_width=True, hide_index=True)
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Distance", f"{mp_result['total_distance']} units")
                c2.metric("Longest Individual Walk", f"{mp_result['max_distance']} units")
                c3.metric("Nodes Expanded (A*)", mp_result["total_nodes_expanded"])

else:
    st.info("Fill in the people and constraints above, then click **Form Teams**.")



# Inside your Logic or Student portal tab in app.py:
# Inside your Logic or Student portal tab in app.py:
st.subheader("🔍 Backward Chaining Proof Tree (Why is student X eligible?)")

# Get list of student names from the dataframe
student_names = [row["Name"] for _, row in edited_df.iterrows() if row["Name"]]

if not student_names:
    st.warning("Please enter student names in the table above first.")
else:
    selected_person_name = st.selectbox("Select Student", student_names)
    target_role = st.text_input("Target Role", placeholder="Enter the role to prove")

    if st.button("Run Backward Chaining Proof"):
        target_role = target_role.strip()
        if not target_role:
            st.error("Enter a target role before running the proof.")
        else:
            # Find the student row data
            row_data = next(row for _, row in edited_df.iterrows() if row["Name"] == selected_person_name)
            skills = [s.strip() for s in str(row_data["Skills"]).split(",") if s.strip()]
            
            # Construct Student object for the engine
            student_obj = Student(selected_person_name, skills)
            backward_engine = RoleEligibilityBackwardEngine(student_obj)
            proof_result = backward_engine.explain_eligibility(target_role)
            
            if proof_result["is_eligible"]:
                st.success(f"Yes! {proof_result['person']} IS eligible for {target_role}.")
            else:
                st.error(f"No, {proof_result['person']} is NOT eligible for {target_role}.")
            
            st.write("**Proof Steps & Trace:**")
            for step in proof_result["proof_steps"]:
                st.text(step)



if st.button("Run Skill Gap CSP Repair"):
    # Build students list from dataframe
    students_list = [Student(row["Name"], [s.strip() for s in str(row["Skills"]).split(",") if s.strip()]) 
                     for _, row in edited_df.iterrows() if row["Name"]]
    
    if students_list:
        gap_solver = SkillGapCSPSolver(students_list, num_teams=num_teams, critical_skills=critical_skills)
        # Assuming current teams exist in session state or run a base solve
        current_teams = st.session_state.get("team_result", {}).get("teams", [])
        if current_teams:
            optimized_assignment, gap_stats = gap_solver.solve_skill_gaps(current_teams)
            st.success("Skill gap CSP repair completed successfully!")
            st.json(gap_stats)
        else:
            st.warning("Please form teams first using the 'Form Teams' button above.")
    else:
        st.error("No students available for CSP repair.")