# Technical Insight Tool

A full-stack web application that provides technical insights and analysis capabilities. This project consists of a React-based frontend and a Python-powered backend, working together to deliver a seamless user experience.

## Project Structure

```
technical_insight_tool/
├── frontend/          # React + TypeScript frontend application
└── backend/          # Python backend API server
```

## Prerequisites

Before running the project, ensure you have the following installed:
- Node.js (v16 or higher) and npm
- Python 3.10 or higher
- pip (Python package manager)

## Setup and Running Instructions

### Frontend Setup

1. Navigate to the frontend directory and install dependencies:
```bash
cd frontend && npm install
```
This command:
- Changes directory to the frontend folder
- Installs all required Node.js dependencies defined in package.json

2. Start the frontend development server:
```bash
npm run dev
```
This command:
- Launches the Vite development server
- Enables hot module replacement for real-time updates
- Makes the application available at http://localhost:5173

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```
This command:
- Changes directory to the backend folder

2. Create a Python virtual environment:
```bash
python3.10 -m venv backend_venv
```
This command:
- Creates an isolated Python environment named 'backend_venv'
- Ensures project dependencies don't conflict with system Python packages

3. Activate the virtual environment:
```bash
source backend_venv/bin/activate
```
This command:
- Activates the isolated Python environment
- Prepares the shell to use the project-specific Python installation

4. Install Python dependencies:
```bash
pip install -r requirement.txt
```
This command:
- Installs all required Python packages listed in requirement.txt
- Sets up the backend environment with necessary libraries

## Running the Application

1. Start the backend server first (from the backend directory):
```bash
python dummy.py  # or the appropriate entry point command
```

2. Start the frontend development server (from the frontend directory):
```bash
npm run dev
```

3. Open your browser and navigate to http://localhost:5173 to access the application

## Development Notes

- The frontend runs on port 5173 by default
- The backend API server typically runs on port 5000
- Make sure both frontend and backend are running simultaneously for full functionality
- Any changes to the frontend code will automatically trigger a hot reload 