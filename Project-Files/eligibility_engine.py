"""
Eligibility Rule Engine — Logic-based reasoning (forward chaining).

Each student has a set of known FACTS (e.g., attendance level, skills they
have, whether they submitted a portfolio, leadership experience). A small
set of RULES is repeatedly applied — inferring new facts (like
"eligible_for(TeamLead)") from existing ones — until no rule can fire any
further (fixed point). This is a direct forward-chaining inference engine,
plus a full trace of which rule fired on which facts, for transparency.
"""


class Rule:
    def __init__(self, name, conditions, conclusion):
        """
        conditions: list of fact strings that must ALL be present for the rule to fire
        conclusion: the single fact string this rule adds when it fires
        """
        self.name = name
        self.conditions = conditions
        self.conclusion = conclusion

    def can_fire(self, known_facts):
        return all(cond(known_facts) if callable(cond) else cond in known_facts
                   for cond in self.conditions)


def build_default_rules():
    """A small illustrative rule base for role eligibility."""
    return [
        Rule(
            "R1: Developer eligibility",
            conditions=["has_skill:Python", "attendance:high"],
            conclusion="eligible_for:Developer",
        ),
        Rule(
            "R2: Designer eligibility",
            conditions=["has_skill:Design", "portfolio_submitted"],
            conclusion="eligible_for:Designer",
        ),
        Rule(
            "R3: Team Lead eligibility",
            conditions=["leadership_experience", "attendance:high"],
            conclusion="eligible_for:TeamLead",
        ),
        Rule(
            "R4: Writer eligibility",
            conditions=["has_skill:Writing", "attendance:medium_or_high"],
            conclusion="eligible_for:Writer",
        ),
        Rule(
            "R5: Medium-or-high attendance derived from high",
            conditions=["attendance:high"],
            conclusion="attendance:medium_or_high",
        ),
        Rule(
            "R6: Medium-or-high attendance derived from medium",
            conditions=["attendance:medium"],
            conclusion="attendance:medium_or_high",
        ),
        Rule(
            "R7: PM eligibility",
            conditions=["has_skill:PM", "eligible_for:TeamLead"],
            conclusion="eligible_for:ProjectManager",
        ),
    ]


def forward_chain(initial_facts, rules=None):
    """
    Run forward chaining until no more rules can fire (fixed point reached).
    Returns the final set of facts and a step-by-step trace of which rule
    fired and what it added.
    """
    rules = rules or build_default_rules()
    known_facts = set(initial_facts)
    trace = []

    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule.conclusion not in known_facts and rule.can_fire(known_facts):
                known_facts.add(rule.conclusion)
                trace.append({
                    "rule": rule.name,
                    "used_facts": list(rule.conditions),
                    "derived": rule.conclusion,
                })
                changed = True

    eligible_roles = sorted(
        f.split(":", 1)[1] for f in known_facts if f.startswith("eligible_for:")
    )
    return {
        "final_facts": sorted(known_facts),
        "eligible_roles": eligible_roles,
        "trace": trace,
    }


def facts_from_profile(skills, attendance_pct, portfolio_submitted, leadership_experience):
    """Convert a human-readable student profile into the fact strings the engine expects."""
    facts = set()
    for skill in skills:
        facts.add(f"has_skill:{skill}")

    if attendance_pct >= 85:
        facts.add("attendance:high")
    elif attendance_pct >= 60:
        facts.add("attendance:medium")
    else:
        facts.add("attendance:low")

    if portfolio_submitted:
        facts.add("portfolio_submitted")
    if leadership_experience:
        facts.add("leadership_experience")

    return facts
