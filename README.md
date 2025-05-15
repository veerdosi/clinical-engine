# Clinical Engine

**Clinical Engine** is an advanced medical simulation platform designed for medical education. It allows users (medical students) to interact with a virtual patient, perform physical examinations, order lab tests and imaging studies, and receive comprehensive feedback on their clinical decision-making.

## Table of Contents

- [Features](#features)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- **Realistic Case Generation:** Generate patient cases across multiple specialties (e.g., Cardiology, Neurology) and difficulty levels.
- **Interactive Virtual Patient:** Engage in natural language (text or voice) conversations with a virtual patient.
- **Physical Examination Simulation:** Input step-by-step examination procedures with verification and receive detailed findings.
- **Diagnostic Decision Making:** Order lab tests, imaging studies, and procedures; submit your final diagnosis and receive performance feedback.
- **Comprehensive Evaluation:** The system evaluates student-patient interactions, clinical reasoning, and procedural skills.

## Repository Structure

- **backend/**  
  Contains the Flask API server, case generation and management, evaluation modules, integrations with OpenAI, ElevenLabs, Replicate, and Perplexity APIs, and more.

  - Key files include:
    - `main.py` – Application entry point
    - `api_routes.py` – API endpoint definitions
    - `case_manager.py`, `case_generator.py`, `enhanced_case_generator.py` – Patient case generation
    - `evaluation.py` – Modules for evaluating interactions and clinical decisions
    - `lab_system.py`, `imaging.py`, `physical_exam.py` – Simulation of tests, imaging, and examinations
    - `session_manager.py` – Tracks session details and test orders
    - `speech_to_text.py` – Transcribes audio input
    - `virtual_patient.py` – Virtual patient agent

- **frontend/**  
  Contains the React application for the user interface.
  - `public/` – Static assets and HTML templates
  - `src/` – React components (e.g., `ChatWindow.js`, `DiagnosisPanel.js`, `PhysicalExamPanel.js`, `TestOrderingPanel.js`, `VitalSigns.js`), CSS styles, and utility files
  - `package.json` – Node dependencies and scripts

## Prerequisites

- **Backend:**
  - Python 3.8+
- **Frontend:**
  - Node.js (v14+ recommended)
  - npm (comes with Node.js)

## Installation

### Backend Setup

1. **Clone the repository and navigate to the `backend/` directory:**

   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install the required Python packages:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the `backend/` directory and add your API keys. For example:

   ```
   OPENAI_API_KEY=your_openai_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   REPLICATE_API_KEY=your_replicate_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   ```

5. **Run the Backend Server:**
   ```bash
   python -m backend.main
   ```
   The backend server will run on http://127.0.0.1:5000.

## Frontend Setup

1. **Navigate to the frontend/ directory:**

   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

3. **Start the React Development Server:**
   ```bash
   npm start
   ```
   The frontend will be available on http://localhost:3000 and is configured to proxy API requests to the backend.

## Usage

1. **Case Selection:**
   On launching the application, you will be presented with a case selection screen. Choose a medical specialty and difficulty level (or use the random options) to generate a new patient case.

2. **Patient Interaction:**
   Use the chat interface to interact with the virtual patient via text or voice. You can ask questions to gather information about symptoms, medical history, and more.

3. **Physical Examination:**
   In the Physical Exam panel, enter the examination name and step-by-step procedure. Once verified, the system simulates an examination and displays findings.

4. **Diagnostic Decision Making:**
   Order lab tests, imaging studies, or procedures in the Test Ordering panel. When ready, submit your final diagnosis in the Diagnosis panel to receive detailed feedback and evaluation.

5. **Evaluation:**
   The system evaluates your performance across various domains (communication, clinical reasoning, procedural skills) and provides actionable feedback.

## API Endpoints

The backend API provides multiple endpoints to support the simulation:

- **Health Check:** `/api/health`
- **Current Case:** `/api/current-case`
- **Generate New Case:** `/api/new-case`
- **Submit Diagnosis:** `/api/submit-diagnosis`
- **Order Lab Test:** `/api/order-lab`
- **Order Imaging:** `/api/order-imaging`
- **Perform Physical Exam:** `/api/physical-exam`
- **Verify Physical Exam Procedure:** `/api/verify-physical-exam`
- **Evaluate Interactions:** `/api/evaluate-interactions`
- **Chat (Text):** `/api/chat`
- **Chat (Voice):** `/api/voice-chat`
- **Session Summary:** `/api/session-summary`

## Contributing

Contributions, issues, and feature requests are welcome! Please open an issue or submit a pull request to contribute to this project.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgements
