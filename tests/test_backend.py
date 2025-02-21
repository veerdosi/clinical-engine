import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
from backend.config import MedicalSimConfig
from backend.case_generator import CaseParameters, CaseGenerator
from backend.virtual_patient import VirtualPatientAgent
from backend.simulation_session import SimulationSession
from backend.lab_system import LabSystem
from backend.imaging import generate_imaging_prompt, FluxImagingGenerator
from backend.performance import PerformanceEvaluator

class TestCaseGenerator(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_generate_case(self, mock_chat_completion):
        mock_response = MagicMock()
        case_json = json.dumps({
            "presenting_complaint": "chest pain",
            "history": {"allergies": "none"},
            "expected_diagnosis": "pneumonia"
        })
        mock_response.choices = [MagicMock(message=MagicMock(content=case_json))]
        mock_chat_completion.return_value = mock_response

        config = MedicalSimConfig(openai_key="dummy", elevenlabs_key="dummy", replicate_key="dummy")
        params = CaseParameters("Emergency Medicine", "moderate")
        generator = CaseGenerator(config)
        case = generator.generate_case(params)
        self.assertIn("presenting_complaint", case)
        self.assertEqual(case["specialty"], "Emergency Medicine")

class TestVirtualPatientAgent(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    @patch('requests.post')
    def test_process_interaction(self, mock_post, mock_chat_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="I feel fine."))]
        mock_chat_completion.return_value = mock_response

        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"audio bytes"

        config = MedicalSimConfig(openai_key="dummy", elevenlabs_key="dummy", replicate_key="dummy")
        case = {"presenting_complaint": "cough", "history": {}}
        agent = VirtualPatientAgent(case, config)
        result = agent.process_interaction("How are you?")
        self.assertIn("text", result)
        self.assertIn("audio", result)

class TestSimulationSession(unittest.TestCase):
    def test_simulation_session(self):
        config = MedicalSimConfig(openai_key="dummy", elevenlabs_key="dummy", replicate_key="dummy")
        case = {"id": "case123"}
        session = SimulationSession(case, config)
        session.add_interaction("Hello", "Hi")
        session.add_test_order("CBC")
        session.add_imaging_order("Chest X-ray")
        session.add_diagnosis("Pneumonia")
        session.add_critical_action("Started antibiotics")
        summary = session.get_summary()
        self.assertEqual(summary["interaction_count"], 1)
        self.assertIn("CBC", summary["tests_ordered"])

class TestLabSystem(unittest.TestCase):
    def test_validate_test_order(self):
        config = MedicalSimConfig(openai_key="dummy", elevenlabs_key="dummy", replicate_key="dummy")
        lab_system = LabSystem(config)
        session = SimulationSession({}, config)
        session.add_test_order("CXR")
        self.assertTrue(lab_system.validate_test_order(["ABG"], session))
    
    @patch('openai.ChatCompletion.create')
    def test_generate_report(self, mock_chat_completion):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mock lab report"))]
        mock_chat_completion.return_value = mock_response
        config = MedicalSimConfig(openai_key="dummy", elevenlabs_key="dummy", replicate_key="dummy")
        lab_system = LabSystem(config)
        case = {"name": "John", "dob": "1990-01-01"}
        report = lab_system.generate_report(case, ["CBC", "CMP"])
        self.assertIn("Mock lab report", report)

class TestFluxImagingGenerator(unittest.TestCase):
    @unittest.skip("Image Gen model not available :(")
    @patch('replicate.Client')
    def test_generate_image(self, mock_replicate_client):
        mock_client_instance = MagicMock()
        mock_client_instance.run.return_value = ["http://example.com/image.png"]
        mock_replicate_client.return_value = mock_client_instance

        config = MedicalSimConfig(openai_key="dummy", elevenlabs_key="dummy", replicate_key="dummy")
        generator = FluxImagingGenerator(config)
        parameters = {"findings_description": "normal chest x-ray", "width": 1024, "height": 1024}
        result = generator.generate_image(parameters)
        self.assertEqual(result["image_url"], "http://example.com/image.png")

class TestPerformanceEvaluator(unittest.TestCase):
    def test_assess_imaging_choices(self):
        case = {"expected_diagnosis": "pneumonia"}
        evaluator = PerformanceEvaluator(case)
        results = evaluator._assess_imaging_choices(["xray"])
        self.assertGreaterEqual(results["appropriateness_score"], 0)

if __name__ == '__main__':
    unittest.main()
