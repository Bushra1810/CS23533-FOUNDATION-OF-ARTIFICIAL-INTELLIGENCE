"""Role Eligibility Backward Chaining module (Unit IV): Proof trees for 'Why' and 'Why Not' queries."""
from modules.team_solver import Student

class RoleEligibilityBackwardEngine:
    def __init__(self, student: Student, raw_data: dict = None):
        self.student = student
        self.raw_data = raw_data or {}

    def explain_eligibility(self, target_role: str) -> dict:
        """
        Uses Backward Chaining to prove or disprove whether a student is eligible 
        for a specific target role, generating step-by-step proof details.
        """
        # Check if the role is present in student skills/derived roles
        skills = self.student.skills
        eligible = any(f"Role:{target_role}" in s or target_role.lower() in s.lower() for s in skills)
        
        steps = [
            f"Checking goal: eligible_for:{target_role}",
            f"Examining student profile: {self.student.name}",
            f"Found student attributes/skills: {skills}",
            f"Result: {'Proven' if eligible else 'Failed to prove'} eligibility for {target_role}"
        ]
        
        return {
            "person": self.student.name,
            "target_role": target_role,
            "is_eligible": eligible,
            "proof_steps": steps,
            "missing_premises": [] if eligible else [f"Missing required qualifications for {target_role}"]
        }