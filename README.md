# Clinical Engine

**Clinical Engine** is an advanced medical simulation platform designed for medical education. It allows users (medical students) to interact with a virtual patient, perform physical examinations, order lab tests and imaging studies, and receive comprehensive feedback on their clinical decision-making.

## Table of Contents

- [Features](#features)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Authentication and Database Setup](#authentication-and-database-setup)
  - [MongoDB Setup](#mongodb-setup)
  - [Google OAuth Setup](#google-oauth-setup)
  - [Environment Variables](#environment-variables)
  - [User Roles and Permissions](#user-roles-and-permissions)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- **Virtual Patient Interaction**: Lifelike patient interaction with advanced language model responses.
- **Physical Examination**: Simulated physical examinations with detailed findings.
- **Diagnostic Testing**: Order and review lab tests and imaging studies.
- **Clinical Evaluation**: Comprehensive assessment of diagnostic accuracy, test selection, and clinical reasoning.
- **Natural Voice Interaction**: Support for voice-based patient interaction with speech-to-text conversion.
- **Realistic Medical Imaging**: AI-generated medical images based on case findings.
- **Integrated Notes System**: SOAP note-taking interface with evaluation functionality.
- **Performance Analytics**: Timing and efficiency metrics for student performance tracking.
- **User Authentication**: Google Sign-In authentication for secure access.
- **Evaluation History**: Track progress and review past case evaluations.
- **MongoDB Integration**: Persistent storage of user data and evaluation results.

## Repository Structure

The repository is organized as follows:

```
clinical-engine/
├── backend/              # Flask-based backend
│   ├── api_routes.py     # API routing and endpoint definitions
│   ├── auth.py           # Authentication services and middleware
│   ├── case_generator.py # Medical case generation
│   ├── chat_handler.py   # Virtual patient conversation handling
│   ├── config.py         # Configuration management
│   ├── db.py             # MongoDB database connection
│   ├── evaluation.py     # Clinical performance evaluation
│   ├── main.py           # Main application entry point
│   ├── session_manager.py # User session management
│   └── user.py           # User model and data management
├── frontend/             # React-based frontend
│   ├── public/           # Static assets
│   └── src/              # React components and logic
│       ├── App.js         # Main app component
│       ├── auth.js        # Authentication utilities
│       ├── LoginScreen.js # Login interface
│       └── api.js         # API service functions
├── requirements.txt      # Python dependencies
└── .env.sample           # Sample environment variables file
```

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- MongoDB 5.0 or higher
- Google Cloud Platform account (for OAuth)

## Installation

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/clinical-engine.git
   cd clinical-engine
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables (see Environment Variables section below).

5. Start the backend server:
   ```
   python -m backend.main
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

## Authentication and Database Setup

### MongoDB Setup
1. Install MongoDB on your system if you haven't already. You can download it from [MongoDB's official website](https://www.mongodb.com/try/download/community).
2. Start the MongoDB server with:
   ```
   mongod --dbpath /path/to/your/data/directory
   ```
3. The application will automatically connect to MongoDB using the connection string in your environment variables.

### Google OAuth Setup
1. Create a Google Cloud Platform project:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google OAuth API
2. Create OAuth credentials:
   - In the Google Cloud Console, go to API & Services > Credentials
   - Create an OAuth client ID (Web application type)
   - Add authorized JavaScript origins (e.g., `http://localhost:3000` for development)
   - Add authorized redirect URIs (e.g., `http://localhost:3000` for development)
3. Copy the Client ID to your environment variables.

### Environment Variables
1. Copy the `.env.sample` file to a new file named `.env` in the project root directory.
2. Update the values in the `.env` file with your actual credentials:
   ```
   # MongoDB Connection String
   MONGODB_URI=mongodb://localhost:27017/clinical_engine

   # Google OAuth Client ID
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

   # Secret key for JWT tokens (for authentication)
   SECRET_KEY=your-secret-key-for-jwt-tokens
   ```
3. For the frontend, create a `.env` file in the `frontend` directory with:
   ```
   REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   ```

### User Roles and Permissions
The application supports the following user roles:
- **Student**: Regular users who can participate in clinical simulations
- **Instructor**: Can view student evaluations and performance metrics
- **Admin**: Has full access to all features and can manage users

By default, new users are assigned the "student" role.

## Usage

1. Navigate to the application in your web browser (default: http://localhost:3000)
2. Sign in with your Google account
3. Select a case to begin a clinical simulation
4. Interact with the virtual patient through text or voice
5. Order tests, perform examinations, and take notes as needed
6. Submit a diagnosis when ready to receive an evaluation
7. Review your performance and clinical reasoning assessment

## API Endpoints

The backend exposes the following key API endpoints:

- **Authentication**
  - `POST /api/auth/google` - Authenticate with Google
  - `GET /api/auth/validate` - Validate authentication token

- **User Management**
  - `GET /api/user/profile` - Get user profile information

- **Case Management**
  - `GET /api/current-case` - Get the current case
  - `POST /api/new-case` - Generate a new case

- **Patient Interaction**
  - `POST /api/chat` - Send message to virtual patient
  - `POST /api/voice-chat` - Send voice message to virtual patient

- **Clinical Tools**
  - `POST /api/order-lab` - Order laboratory tests
  - `POST /api/order-imaging` - Order imaging studies
  - `POST /api/physical-exam` - Perform physical examination

- **Evaluation**
  - `POST /api/submit-diagnosis` - Submit diagnosis for evaluation
  - `GET /api/evaluations/history` - View evaluation history
  - `GET /api/evaluations/:id` - View specific evaluation details

- **Session Management**
  - `GET /api/sessions/history` - View session history
  - `GET /api/session-summary` - Get current session summary

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for GPT models
- ElevenLabs for voice synthesis
- Replicate for image generation
- MongoDB for database services
- Google for authentication
