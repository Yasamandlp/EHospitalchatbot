<<<<<<< HEAD

# 🏥 e-Hospital Voice Assistant API

A Flask-based backend application for managing patients, doctors, treatments, and communication within an electronic hospital system. It supports Persian and English input, voice-to-text interaction, and includes a Swagger-documented RESTful API.

## 🚀 Features

- 🗣️ Speech recognition and text-to-speech integration
- 🌍 Language detection (English & Persian)
- 🔍 Fuzzy keyword matching for queries
- 📊 Patient & doctor management with SQLite
- 🔐 Session management
- 🔄 API routes for sending messages and retrieving data
- 📄 Swagger UI documentation for all endpoints

## 🧱 Tech Stack

- Python
- Flask
- SQLite
- Pandas
- FuzzyWuzzy
- SpeechRecognition
- pyttsx3
- Flasgger (Swagger for Flask)

---

## 📂 Project Structure

```
yasi_project/
├── app_with_swagger.py       # Main API backend with Swagger docs
├── database.db               # SQLite database file
├── data/                     # Patient-related CSV data
├── templates/                # HTML templates
├── flask_session/            # Flask session storage
└── New folder (2)/           # Image assets
```

---

## 🧪 API Documentation

After running the app, access the Swagger UI at:

👉 http://localhost:5000/apidocs

---

## 🛠️ How to Run

### Step 1: Install Dependencies

```bash
pip install flask flask-session flasgger pandas fuzzywuzzy SpeechRecognition pyttsx3
```

### Step 2: Run the App

```bash
python app_with_swagger.py
```

---

## 📤 API Endpoints

| Method | Endpoint                  | Description                       |
|--------|---------------------------|-----------------------------------|
| GET    | `/patients`               | Retrieve all patients             |
| POST   | `/message`                | Send a message to a doctor        |
| GET    | `/messages/<patient_id>`  | Get messages for a patient        |
| GET    | `/treatments/<patient_id>`| Get treatments for a patient      |

---

## 📌 TODO / Suggestions

- [ ] Add user authentication (JWT or session login)
- [ ] Create `POST /login` and `POST /register` routes
- [ ] Add `GET /doctors` and `GET /patients/<id>`
- [ ] Protect message routes with patient login
- [ ] Add email verification or OTP login
- [ ] Upload patient files / voice messages
- [ ] Integrate with front-end (React or Vue)

---

## 👨‍💻 Author

Hesam | M.Sc. CS Student | University of Ottawa  
🇮🇷 Originally from Iran | 🇨🇦 Living in Canada  
=======
# EHospitalchatbot
>>>>>>> e8d654702d4e4f3c19c0a0bef125dded93c60325
