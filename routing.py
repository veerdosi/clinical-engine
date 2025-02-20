from flask import Flask, request, jsonify
from pipeline import (
    MedicalSimConfig, CaseGenerator, CaseParameters,
    SimulationSession, VirtualPatientAgent, LabSystem,
    FluxImagingGenerator, generate_imaging_prompt
)

app = Flask(_name_)

# Initialize global configuration instance.
config = MedicalSimConfig(
    openai_key="your-openai-key",
    elevenlabs_key="your-elevenlabs-key",
    replicate_key="your-replicate-key"
)

# For demonstration, we use a global simulation session.
simulation_session = None

@app.route('/generate_case', methods=['POST'])
def generate_case():
    """
    Endpoint to generate a new patient case.
    Expects a JSON payload with 'specialty' and 'difficulty'.
    """
    data = request.get_json()
    specialty = data.get('specialty', 'General')
    difficulty = data.get('difficulty', 'moderate')
    
    params = CaseParameters(specialty, difficulty)
    case_generator = CaseGenerator(config)
    case = case_generator.generate_case(params)
    
    # Create a new simulation session using the generated case.
    global simulation_session
    simulation_session = SimulationSession(case=case, config=config)
    
    return jsonify(case)

@app.route('/process_interaction', methods=['POST'])
def process_interaction():
    """
    Endpoint for processing an interaction with the virtual patient.
    Expects a JSON payload with 'user_input'.
    """
    data = request.get_json()
    user_input = data.get('user_input')
    
    if simulation_session is None:
        return jsonify({"error": "No active simulation session. Generate a case first."}), 400
    
    # Create a patient agent using the current case.
    patient_agent = VirtualPatientAgent(simulation_session.case, config)
    response = patient_agent.process_interaction(user_input)
    simulation_session.add_interaction(user_input, response["text"])
    
    return jsonify(response)

@app.route('/lab_report', methods=['GET'])
def lab_report():
    """
    Endpoint to generate a lab report based on the ordered tests.
    """
    if simulation_session is None:
        return jsonify({"error": "No active simulation session. Generate a case first."}), 400
    
    lab_system = LabSystem(config)
    report = lab_system.generate_report(simulation_session.case, simulation_session.ordered_tests)
    
    return jsonify({"lab_report": report})

@app.route('/order_imaging', methods=['POST'])
def order_imaging():
    """
    Endpoint to order an imaging study.
    Expects a JSON payload with an optional 'imaging_type' (defaults to 'Chest X-ray').
    """
    data = request.get_json()
    imaging_type = data.get('imaging_type', 'Chest X-ray')
    
    if simulation_session is None:
        return jsonify({"error": "No active simulation session. Generate a case first."}), 400
    
    simulation_session.add_imaging_order(imaging_type)
    imaging_prompt = generate_imaging_prompt(simulation_session.case, imaging_type, config)
    imaging_generator = FluxImagingGenerator(config)
    imaging_result = imaging_generator.generate_image(imaging_prompt["replicate_parameters"])
    
    return jsonify(imaging_result)

@app.route('/session_summary', methods=['GET'])
def session_summary():
    """
    Endpoint to retrieve a summary of the current simulation session.
    """
    if simulation_session is None:
        return jsonify({"error": "No active simulation session. Generate a case first."}), 400
    
    return jsonify(simulation_session.get_summary())

if _name_ == '_main_':
    app.run(debug=True)