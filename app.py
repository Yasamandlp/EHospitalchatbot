import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, render_template, session
import speech_recognition as sr
import pyttsx3
from flask_session import Session
import requests
import re
from fuzzywuzzy import fuzz

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Function to detect language (Persian or English)
def detect_language(text):
    persian_pattern = re.compile(r'[\u0600-\u06FF]')
    if persian_pattern.search(text):
        return 'persian'
    return 'english'

# Function to clean text (remove extra spaces, special characters, etc.)
def clean_text(text):
    text = re.sub(r'[^\w\s]', '', text)  # حذف کاراکترهای خاص
    text = text.lower().strip()
    return text

# Function to match text with keywords approximately
def match_keyword(text, keywords, threshold=60):  # کاهش آستانه به 60
    text = clean_text(text)
    for keyword in keywords:
        keyword = clean_text(keyword)
        # تطبیق روی کل متن یا کلمات جداگانه
        if fuzz.ratio(text, keyword) >= threshold:
            return True
        for word in text.split():
            if fuzz.ratio(word, keyword) >= threshold:
                return True
    return False

# Function to initialize the database and load CSV data
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        uuid TEXT,
        age INTEGER,
        gender TEXT,
        FName TEXT,
        LName TEXT,
        EmailId TEXT,
        password TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS patient_doctor (
        id INTEGER PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        relationship_start_date TEXT,
        relationship_status TEXT,
        association_type TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS online_patients (
        online_patient_id TEXT PRIMARY KEY,
        Fname TEXT,
        email TEXT,
        session_status TEXT,
        start_time TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        patient_FName TEXT,
        patient_LName TEXT,
        message TEXT,
        time_stamp TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS patients_treatment (
        id INTEGER PRIMARY KEY,
        patient_id TEXT,
        doctor_id TEXT,
        treatment TEXT,
        RecordDate TEXT,
        disease_type TEXT,
        disease_id TEXT
    )''')

    patients_df = pd.read_csv('data/patients_registration (1).csv')
    patients_df[['id', 'uuid', 'Age', 'Gender', 'FName', 'LName', 'EmailId', 'password']].to_sql('patients', conn, if_exists='replace', index=False)

    patient_doctor_df = pd.read_csv('data/patient_doctor (1).csv')
    patient_doctor_df.to_sql('patient_doctor', conn, if_exists='replace', index=False)

    online_patients_df = pd.read_csv('data/online_patients (1).csv')
    online_patients_df.to_sql('online_patients', conn, if_exists='replace', index=False)

    messages_df = pd.read_csv('data/patient_to_doctor_message (1).csv')
    messages_df.to_sql('messages', conn, if_exists='replace', index=False)

    treatments_df = pd.read_csv('data/patients_treatment (1).csv')
    treatments_df.to_sql('patients_treatment', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

# Function to verify patient
def verify_patient(email, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, FName FROM patients WHERE EmailId = ? AND password = ?", (email, password))
    result = cursor.fetchone()
    conn.close()
    return result  # Returns (id, FName) or None

# Function to get treatment information
def get_treatment_info(patient_id, language='english'):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT treatment, RecordDate, disease_type FROM patients_treatment WHERE patient_id = ? ORDER BY RecordDate DESC", (patient_id,))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        if language == 'persian':
            response = "درمان‌های شما:\n"
            for treatment, date, disease in results:
                if treatment and treatment.strip():
                    response += f"- تاریخ: {date}، درمان: {treatment}"
                    if disease and disease.strip():
                        response += f"، بیماری: {disease}"
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
    return "هیچ سابقه درمانی پیدا نشد." if language == 'persian' else "No treatment records found."

# Function to get test results
def get_test_results(patient_id, test_type, language='english'):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT treatment, RecordDate FROM patients_treatment WHERE patient_id = ? AND treatment LIKE ? ORDER BY RecordDate DESC LIMIT 1", 
                   (patient_id, f"%{test_type}%"))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        treatment, date = result
        if language == 'persian':
            return f"آخرین نتیجه {test_type}: {treatment} (تاریخ: {date})"
        else:
            return f"Latest {test_type} result: {treatment} (Date: {date})"
    return f"هیچ نتیجه‌ای برای {test_type} پیدا نشد." if language == 'persian' else f"No {test_type} results found."

# Function to get the latest blood pressure
def get_blood_pressure(patient_id, language='english'):
    conn = sqlite3.connect('database.db')
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
        if language == 'persian':
            return f"آخرین فشار خون: {treatment} (تاریخ: {date})"
        else:
            return f"Latest blood pressure: {treatment} (Date: {date})"
    return "سابقه فشار خونی پیدا نشد." if language == 'persian' else "No blood pressure records found."

# Function to get the latest blood sugar from the API
def get_latest_blood_sugar(patient_id, language='english'):
    url = "https://e-react-node-backend-22ed6864d5f3.herokuapp.com/table/blood_sugar_analysis"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            patient_records = [record for record in data if record.get('patient_id') == patient_id]
            if patient_records:
                latest_record = patient_records[-1]
                blood_sugar = latest_record.get('blood_sugar', 'مقداری ثبت نشده' if language == 'persian' else 'No value recorded')
                date = latest_record.get('date', 'تاریخ نامشخص' if language == 'persian' else 'Unknown date')
                if language == 'persian':
                    return f"آخرین قند خون: {blood_sugar} (تاریخ: {date})"
                else:
                    return f"Latest blood sugar: {blood_sugar} (Date: {date})"
            return "هیچ سابقه قند خونی پیدا نشد." if language == 'persian' else "No blood sugar records found."
        else:
            return f"خطا در ارتباط با سرور: {response.status_code}" if language == 'persian' else f"Server connection error: {response.status_code}"
    except Exception as e:
        return f"خطا در گرفتن داده‌ها: {str(e)}" if language == 'persian' else f"Error fetching data: {str(e)}"

# Function to get data from heart_disease_test API
def get_heart_disease_data(patient_id, field, language='english'):
    url = "https://e-react-node-backend-22ed6864d5f3.herokuapp.com/table/heart_disease_test"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            patient_records = [record for record in data if record.get('patient_id') == patient_id]
            if patient_records:
                latest_record = patient_records[-1]
                value = latest_record.get(field, 'مقداری ثبت نشده' if language == 'persian' else 'No value recorded')
                field_names = {
                    'patient_id': ('شناسه بیمار', 'Patient ID'),
                    'education': ('تحصیلات', 'Education'),
                    'currentSmoker': ('سیگاری فعلی', 'Current Smoker'),
                    'cigsPerDay': ('سیگار در روز', 'Cigarettes per Day'),
                    'BPMeds': ('داروی فشار خون', 'Blood Pressure Medication'),
                    'prevalentStroke': ('سکته قبلی', 'Prevalent Stroke'),
                    'prevalentHyp': ('فشار خون بالا', 'Prevalent Hypertension'),
                    'diabetes': ('دیابت', 'Diabetes'),
                    'BMI': ('شاخص توده بدنی', 'BMI'),
                    'totChol': ('کلسترول کل', 'Total Cholesterol'),
                    'sysBP': ('فشار سیستولیک', 'Systolic BP'),
                    'diaBP': ('فشار دیاستولیک', 'Diastolic BP'),
                    'heartRate': ('ضربان قلب', 'Heart Rate'),
                    'glucose': ('گلوکز', 'Glucose'),
                    'test_time': ('زمان تست', 'Test Time'),
                    'CHD': ('بیماری قلبی', 'Coronary Heart Disease')
                }
                persian_name, english_name = field_names.get(field, (field, field))
                if language == 'persian':
                    return f"{persian_name}: {value}"
                else:
                    return f"{english_name}: {value}"
            return "هیچ سابقه‌ای پیدا نشد." if language == 'persian' else "No records found."
        else:
            return f"خطا در ارتباط با سرور: {response.status_code}" if language == 'persian' else f"Server connection error: {response.status_code}"
    except Exception as e:
        return f"خطا در گرفتن داده‌ها: {str(e)}" if language == 'persian' else f"Error fetching data: {str(e)}"

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

# Homepage
@app.route('/')
def home():
    session.pop('chat_state', None)
    return render_template('index.html')

# Chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').lower()
    email = data.get('email', '')
    password = data.get('password', '')

    patient = verify_patient(email, password)
    if not patient:
        return jsonify({'response': 'ایمیل یا رمز عبور اشتباه است.' if detect_language(message) == 'persian' else 'Invalid email or password.'})
    
    patient_id, patient_name = patient

    if 'chat_state' not in session:
        session['chat_state'] = 'initial'

    if not message or message.strip() == "":
        message = recognize_speech()
        if not message:
            return jsonify({'response': 'صدا تشخیص داده نشد. لطفاً دوباره صحبت کنید یا تایپ کنید.' if detect_language(message) == 'persian' else 'No speech detected. Please try typing or speaking again.'})

    language = detect_language(message)
    print(f"Received message: '{message}' (Language: {language})")  # لاگ برای دیباگ

    # Handle specific field requests from heart_disease_test with fuzzy matching
    field_keywords = {
        'patient_id': ['patient id', 'شناسه بیمار'],
        'education': ['education', 'تحصیلات'],
        'currentSmoker': ['current smoker', 'سیگاری فعلی'],
        'cigsPerDay': ['cigs per day', 'سیگار در روز'],
        'BPMeds': ['bp meds', 'داروی فشار خون'],
        'prevalentStroke': ['prevalent stroke', 'سکته قبلی'],
        'prevalentHyp': ['prevalent hyp', 'فشار خون بالا'],
        'diabetes': ['diabetes', 'دیابت'],
        'BMI': ['bmi', 'شاخص توده بدنی'],
        'totChol': ['total cholesterol', 'کلسترول کل'],
        'sysBP': ['systolic bp', 'فشار سیستولیک'],
        'diaBP': ['diastolic bp', 'فشار دیاستولیک'],
        'heartRate': ['heart rate', 'ضربان قلب'],
        'glucose': ['glucose', 'گلوکز'],
        'test_time': ['test time', 'زمان تست'],
        'CHD': ['chd', 'بیماری قلبی']
    }

    for field, keywords in field_keywords.items():
        message_words = clean_text(message).split()
        print(f"Checking field: {field}, Keywords: {keywords}, Message words: {message_words}")  # لاگ برای دیباگ
        for word in message_words:
            if match_keyword(word, keywords):
                print(f"Matched field: {field} with word: {word}")  # لاگ برای دیباگ
                response = get_heart_disease_data(patient_id, field, language)
                text_to_speech(response)
                session['chat_state'] = 'initial'
                return jsonify({'response': response})

    # Handle other requests with fuzzy matching
    if match_keyword(message, ['blood test', 'آزمایش خون']):
        print("Matched: blood test")  # لاگ برای دیباگ
        response = get_test_results(patient_id, 'blood test', language)
        text_to_speech(response)
        session['chat_state'] = 'initial'
        return jsonify({'response': response})
    elif match_keyword(message, ['blood pressure', 'فشار خون']):
        print("Matched: blood pressure")  # لاگ برای دیباگ
        response = get_blood_pressure(patient_id, language)
        text_to_speech(response)
        session['chat_state'] = 'initial'
        return jsonify({'response': response})
    elif match_keyword(message, ['blood sugar', 'قند خون']):
        print("Matched: blood sugar")  # لاگ برای دیباگ
        response = get_latest_blood_sugar(patient_id, language)
        text_to_speech(response)
        session['chat_state'] = 'initial'
        return jsonify({'response': response})
    elif match_keyword(message, ['treatment', 'درمان']):
        print("Matched: treatment")  # لاگ برای دیباگ
        response = get_treatment_info(patient_id, language)
        text_to_speech(response)
        session['chat_state'] = 'initial'
        return jsonify({'response': response})
    elif match_keyword(message, ['other test', 'تست دیگر']):
        print("Matched: other test")  # لاگ برای دیباگ
        response = "تست حسام" if language == 'persian' else "test hesam"
        text_to_speech(response)
        return jsonify({'response': response})

    if session['chat_state'] == 'initial' and match_keyword(message, ['hello', 'hi', 'سلام']):
        print("Matched: hello/hi/سلام")  # لاگ برای دیباگ
        session['chat_state'] = 'asked_how_are_you'
        response = f"سلام {patient_name}، امروز چطور هستید؟" if language == 'persian' else f"Hi {patient_name}, how are you today?"
        text_to_speech(response)
        return jsonify({'response': response})

    elif session['chat_state'] == 'asked_how_are_you':
        if any(match_keyword(message, [keyword]) for keyword in ['good', 'fine', 'great', 'okay', 'bad', 'خوب', 'بد']):
            print("Matched: response to how are you")  # لاگ برای دیباگ
            session['chat_state'] = 'ready_to_assist'
            response = f"عالیه {patient_name}! چطور می‌تونم بهتون کمک کنم؟" if language == 'persian' else f"Great {patient_name}! How can I assist you today?"
            text_to_speech(response)
            return jsonify({'response': response})
        else:
            response = f"متاسفم {patient_name}، متوجه نشدم. امروز چطور هستید؟" if language == 'persian' else f"Sorry {patient_name}, I didn’t understand. How are you today?"
            text_to_speech(response)
            return jsonify({'response': response})

    if session['chat_state'] == 'ready_to_assist' or match_keyword(message, ['hello', 'hi', 'سلام']):
        if match_keyword(message, ['hello', 'hi', 'سلام']):
            print("Matched: hello/hi/سلام in ready_to_assist state")  # لاگ برای دیباگ
            for field, keywords in field_keywords.items():
                message_words = clean_text(message).split()
                for word in message_words:
                    if match_keyword(word, keywords):
                        print(f"Matched field: {field} with word: {word} in ready_to_assist")  # لاگ برای دیباگ
                        response = get_heart_disease_data(patient_id, field, language)
                        text_to_speech(response)
                        session['chat_state'] = 'initial'
                        return jsonify({'response': response})
            if match_keyword(message, ['blood test', 'آزمایش خون']):
                print("Matched: blood test in ready_to_assist")  # لاگ برای دیباگ
                response = get_test_results(patient_id, 'blood test', language)
                text_to_speech(response)
            elif match_keyword(message, ['blood pressure', 'فشار خون']):
                print("Matched: blood pressure in ready_to_assist")  # لاگ برای دیباگ
                response = get_blood_pressure(patient_id, language)
                text_to_speech(response)
            elif match_keyword(message, ['blood sugar', 'قند خون']):
                print("Matched: blood sugar in ready_to_assist")  # لاگ برای دیباگ
                response = get_latest_blood_sugar(patient_id, language)
                text_to_speech(response)
            elif match_keyword(message, ['treatment', 'درمان']):
                print("Matched: treatment in ready_to_assist")  # لاگ برای دیباگ
                response = get_treatment_info(patient_id, language)
                text_to_speech(response)
            else:
                response = f"چطور می‌تونم بهتون کمک کنم؟" if language == 'persian' else f"How can I assist you today?"
                text_to_speech(response)
            session['chat_state'] = 'initial'
            return jsonify({'response': response})
        else:
            response = "لطفاً بگید چی نیاز دارید، مثلاً 'ضربان قلب'، 'فشار خون'، 'قند خون'، 'دیابت' یا 'درمان'." if language == 'persian' else "Please specify what you need, e.g., 'heart rate', 'blood pressure', 'blood sugar', 'diabetes', or 'treatment'."
            text_to_speech(response)
            return jsonify({'response': response})

    response = "لطفاً بگید چی نیاز دارید، مثلاً 'ضربان قلب'، 'فشار خون'، 'قند خون'، 'دیابت' یا 'درمان'." if language == 'persian' else "Please specify what you need, e.g., 'heart rate', 'blood pressure', 'blood sugar', 'diabetes', or 'treatment'."
    print("No match found, returning default response.")  # لاگ برای دیباگ
    text_to_speech(response)
    return jsonify({'response': response})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)