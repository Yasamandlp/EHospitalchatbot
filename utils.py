import sqlite3
import pandas as pd
import speech_recognition as sr
import pyttsx3
import requests
import re
from fuzzywuzzy import fuzz

# Function to detect language (Persian or English)
def detect_language(text):
    persian_pattern = re.compile(r"[\u0600-\u06FF]")
    return "persian" if persian_pattern.search(text) else "english"

# Function to clean text (remove extra spaces, special characters, etc.)
def clean_text(text):
    text = re.sub(r"[^\w\s]", "", text)  # Remove special characters
    return text.lower().strip()

# Function to match text with keywords approximately
def match_keyword(text, keywords, threshold=60):  # Threshold set to 60
    text = clean_text(text)
    for keyword in keywords:
        keyword = clean_text(keyword)
        # Match on full text or individual words
        if fuzz.ratio(text, keyword) >= threshold or any(fuzz.ratio(word, keyword) >= threshold for word in text.split()):
            return True
    return False

# Function to initialize the database and load CSV data
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create tables if they don’t exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        uuid TEXT,
        age INTEGER,
        gender TEXT,
        FName TEXT,
        LName TEXT,
        EmailId TEXT,
        password TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS patient_doctor (
        id INTEGER PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        relationship_start_date TEXT,
        relationship_status TEXT,
        association_type TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS online_patients (
        online_patient_id TEXT PRIMARY KEY,
        Fname TEXT,
        email TEXT,
        session_status TEXT,
        start_time TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        patient_FName TEXT,
        patient_LName TEXT,
        message TEXT,
        time_stamp TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS patients_treatment (
        id INTEGER PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        treatment TEXT,
        RecordDate TEXT,
        disease_type TEXT,
        disease_id TEXT
    )""")

    # Load CSV data into tables
    patients_df = pd.read_csv("data/patients_registration (1).csv")
    patients_df[["id", "uuid", "Age", "Gender", "FName", "LName", "EmailId", "password"]].to_sql("patients", conn, if_exists="replace", index=False)

    patient_doctor_df = pd.read_csv("data/patient_doctor (1).csv")
    patient_doctor_df.to_sql("patient_doctor", conn, if_exists="replace", index=False)

    online_patients_df = pd.read_csv("data/online_patients (1).csv")
    online_patients_df.to_sql("online_patients", conn, if_exists="replace", index=False)

    messages_df = pd.read_csv("data/patient_to_doctor_message (1).csv")
    messages_df.to_sql("messages", conn, if_exists="replace", index=False)

    treatments_df = pd.read_csv("data/patients_treatment (1).csv")
    treatments_df.to_sql("patients_treatment", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

# Function to verify patient
def verify_patient(email, password):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, FName FROM patients WHERE EmailId = ? AND password = ?", (email, password))
    result = cursor.fetchone()
    conn.close()
    return result  # Returns (id, FName) or None

# Function to get treatment information
def get_treatment_info(patient_id, language="english"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT treatment, RecordDate, disease_type FROM patients_treatment WHERE patient_id = ? ORDER BY RecordDate DESC", (patient_id,))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        if language == "persian":
            response = "Your treatments:\n"
            for treatment, date, disease in results:
                if treatment and treatment.strip():
                    response += f"- Date: {date}, Treatment: {treatment}"
                    if disease and disease.strip():
                        response += f", Disease: {disease}"
                    response += "\n"
            return response.strip()
        else:
            response = "Your treatments:\n"
            for treatment, date, disease in results:
                if treatment and treatment.strip():
                    response += f"- Date: {date}, Treatment: {treatment}"
                    if disease and disease.strip():
                        response += f", Disease: {disease}"
                    response += "\n"
            return response.strip()
    return "No treatment records found." if language == "english" else "No treatment history found."

# Function to get test results
def get_test_results(patient_id, test_type, language="english"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT treatment, RecordDate FROM patients_treatment WHERE patient_id = ? AND treatment LIKE ? ORDER BY RecordDate DESC LIMIT 1", 
                   (patient_id, f"%{test_type}%"))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        treatment, date = result
        if language == "persian":
            return f"Latest {test_type} result: {treatment} (Date: {date})"
        else:
            return f"Latest {test_type} result: {treatment} (Date: {date})"
    return f"No {test_type} results found." if language == "english" else f"No {test_type} results found."

# Function to get the latest blood pressure
def get_blood_pressure(patient_id, language="english"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT treatment, RecordDate 
        FROM patients_treatment 
        WHERE patient_id = ? AND treatment LIKE '%Blood Pressure%' 
        ORDER BY RecordDate DESC 
        LIMIT 1
    """, (patient_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        treatment, date = result
        if language == "persian":
            return f"Latest blood pressure: {treatment} (Date: {date})"
        else:
            return f"Latest blood pressure: {treatment} (Date: {date})"
    return "No blood pressure records found." if language == "english" else "No blood pressure records found."

# Function to get the latest blood sugar from the API
def get_latest_blood_sugar(patient_id, language="english"):
    url = "https://e-react-node-backend-22ed6864d5f3.herokuapp.com/table/blood_sugar_analysis"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            patient_records = [record for record in data if record.get("patient_id") == patient_id]
            if patient_records:
                latest_record = patient_records[-1]
                blood_sugar = latest_record.get("blood_sugar", "No value recorded" if language == "english" else "No value recorded")
                date = latest_record.get("date", "Unknown date" if language == "english" else "Unknown date")
                if language == "persian":
                    return f"Latest blood sugar: {blood_sugar} (Date: {date})"
                else:
                    return f"Latest blood sugar: {blood_sugar} (Date: {date})"
            return "No blood sugar records found." if language == "english" else "No blood sugar records found."
        else:
            return f"Server connection error: {response.status_code}" if language == "english" else f"Server connection error: {response.status_code}"
    except Exception as e:
        return f"Error fetching data: {str(e)}" if language == "english" else f"Error fetching data: {str(e)}"

# Function to get data from heart_disease_test API
def get_heart_disease_data(patient_id, field, language="english"):
    url = "https://e-react-node-backend-22ed6864d5f3.herokuapp.com/table/heart_disease_test"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            patient_records = [record for record in data if record.get("patient_id") == patient_id]
            if patient_records:
                latest_record = patient_records[-1]
                value = latest_record.get(field, "No value recorded" if language == "english" else "No value recorded")
                field_names = {
                    "patient_id": ("Patient ID", "Patient ID"),
                    "education": ("Education", "Education"),
                    "currentSmoker": ("Current Smoker", "Current Smoker"),
                    "cigsPerDay": ("Cigarettes per Day", "Cigarettes per Day"),
                    "BPMeds": ("Blood Pressure Medication", "Blood Pressure Medication"),
                    "prevalentStroke": ("Prevalent Stroke", "Prevalent Stroke"),
                    "prevalentHyp": ("Prevalent Hypertension", "Prevalent Hypertension"),
                    "diabetes": ("Diabetes", "Diabetes"),
                    "BMI": ("BMI", "BMI"),
                    "totChol": ("Total Cholesterol", "Total Cholesterol"),
                    "sysBP": ("Systolic BP", "Systolic BP"),
                    "diaBP": ("Diastolic BP", "Diastolic BP"),
                    "heartRate": ("Heart Rate", "Heart Rate"),
                    "glucose": ("Glucose", "Glucose"),
                    "test_time": ("Test Time", "Test Time"),
                    "CHD": ("Coronary Heart Disease", "Coronary Heart Disease")
                }
                persian_name, english_name = field_names.get(field, (field, field))
                if language == "persian":
                    return f"{persian_name}: {value}"
                else:
                    return f"{english_name}: {value}"
            return "No records found." if language == "english" else "No records found."
        else:
            return f"Server connection error: {response.status_code}" if language == "english" else f"Server connection error: {response.status_code}"
    except Exception as e:
        return f"Error fetching data: {str(e)}" if language == "english" else f"Error fetching data: {str(e)}"

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Say something!")
        audio = recognizer.listen(source, timeout=5)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text.lower()
    except sr.WaitTimeoutError:
        print("No speech detected. Please try again.")
        return ""
    except sr.UnknownValueError:
        print("Could not understand audio. Please try again.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return ""

# Function to convert text to speech
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()