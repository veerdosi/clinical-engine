from datetime import datetime

class SimulationSession:
    def __init__(self, case: dict, config):
        self.case = case
        self.config = config
        self.start_time = datetime.now()
        self.interactions = []
        self.ordered_tests = []
        self.ordered_imaging = []
        self.diagnoses = []
        self.critical_actions = []
        self.elapsed_time = 0

    def add_interaction(self, user_input: str, patient_response: str):
        self.interactions.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "patient_response": patient_response
        })
        self.elapsed_time += 1

    def add_test_order(self, test: str):
        if test not in self.ordered_tests:
            self.ordered_tests.append(test)
            self.elapsed_time += 5

    def add_imaging_order(self, imaging_study: str):
        if imaging_study not in self.ordered_imaging:
            self.ordered_imaging.append(imaging_study)
            self.elapsed_time += 10

    def add_diagnosis(self, diagnosis: str):
        if diagnosis not in self.diagnoses:
            self.diagnoses.append(diagnosis)

    def add_critical_action(self, action: str):
        if action not in self.critical_actions:
            self.critical_actions.append(action)

    def get_summary(self) -> dict:
        return {
            "case_id": self.case.get("id", "unknown"),
            "start_time": self.start_time.isoformat(),
            "elapsed_time": self.elapsed_time,
            "interaction_count": len(self.interactions),
            "tests_ordered": self.ordered_tests,
            "imaging_ordered": self.ordered_imaging,
            "diagnoses_made": self.diagnoses,
            "critical_actions": self.critical_actions
        }