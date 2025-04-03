# 🏥 E-Hospital Chatbot

A FastAPI-based backend application for managing patient-doctor interactions in an electronic hospital system. It supports Persian and English input, voice-to-text interaction, and provides a user-friendly chat interface for retrieving medical information.

## 🚀 Features

- 🗣️ Speech recognition and text-to-speech integration
- 🌍 Language detection (English & Persian)
- 🔍 Fuzzy keyword matching for queries
- 📊 Patient & doctor management with SQLite
- 🔐 Session management using cookies
- 🔄 API routes for sending messages and retrieving data
- 💻 Improved chat interface with a modern design

## 🧱 Tech Stack

- Python
- FastAPI
- SQLite
- Pandas
- FuzzyWuzzy
- SpeechRecognition
- pyttsx3
- Uvicorn (ASGI server)

---

## 📂 Project Structure


healthcare_project/
├── main.py                   # Main FastAPI application
├── routes.py                 # API routes and chat logic
├── utils.py                  # Helper functions and database logic
├── database.db               # SQLite database file
├── data/                     # Patient-related CSV data
│   ├── patients_registration (1).csv
│   ├── patient_doctor (1).csv
│   ├── online_patients (1).csv
│   ├── patient_to_doctor_message (1).csv
│   └── patients_treatment (1).csv
└── templates/                # HTML templates
└── index.html            # Chat interface

---

## 🧪 API Documentation

After running the app, access the Swagger UI at:

👉 http://localhost:5000/apidocs

---


---

## 🛠️ How to Run

### Step 1: Install Dependencies

Make sure you have Python 3.11+ installed. Then, install the required packages:

```bash
pip install fastapi uvicorn pandas fuzzywuzzy speechrecognition pyttsx3 requests

Step 2: Prepare CSV Data
Ensure the following CSV files are placed in the data/ directory:

patients_registration (1).csv
patient_doctor (1).csv
online_patients (1).csv
patient_to_doctor_message (1).csv
patients_treatment (1).csv
These files contain patient, doctor, and treatment data used by the application.

Step 3: Run the App
Run the FastAPI application using the following command:

bash

Collapse

Wrap

Copy
python main.py
The server will start on http://localhost:8000. Open this URL in your browser to access the chat interface.

---

📤 API Endpoints
Method	Endpoint	Description
GET	/	Renders the chat interface
POST	/chat	Handles chat messages and voice input

---

📌 TODO / Suggestions
 Add user authentication (JWT or OAuth)
 Create POST /login and POST /register routes
 Add GET /doctors and GET /patients/<id> endpoints
 Protect chat routes with authentication
 Add email verification or OTP login
 Support uploading patient files or voice messages
 Integrate with a front-end framework (React or Vue)
 Add support for more languages
 Improve fuzzy matching accuracy

---

## 👨‍💻 Author

Yasaman Dolatpour | University of Ottawa  
🇮🇷 Originally from Iran | 🇨🇦 Living in Canada  
=======
# EHospitalchatbot
>>>>>>> e8d654702d4e4f3c19c0a0bef125dded93c60325
