from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from utils import (
    verify_patient, get_treatment_info, get_test_results, get_blood_pressure,
    get_latest_blood_sugar, get_heart_disease_data, recognize_speech, text_to_speech,
    detect_language, clean_text, match_keyword
)
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Simple in-memory session storage
sessions = {}

# Dependency to get or create a session
def get_session(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {}
    return session_id

# Homepage route
@router.get("/")
async def home(request: Request, session_id: str = Depends(get_session)):
    response = templates.TemplateResponse("index.html", {"request": request})
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=3600)
    sessions[session_id]["chat_state"] = None
    return response

# Chat endpoint
@router.post("/chat")
async def chat(request: Request, session_id: str = Depends(get_session)):
    data = await request.json()
    message = data.get("message", "").lower()
    email = data.get("email", "")
    password = data.get("password", "")

    patient = verify_patient(email, password)
    if not patient:
        language = detect_language(message)
        response = "Invalid email or password." if language == "english" else "Email or password is incorrect."
        return JSONResponse(content={"response": response})

    patient_id, patient_name = patient

    session_data = sessions.get(session_id, {})
    if "chat_state" not in session_data:
        session_data["chat_state"] = "initial"
        sessions[session_id] = session_data

    if not message or message.strip() == "":
        message = recognize_speech()
        if not message:
            language = detect_language(message)
            response = "No speech detected. Please try typing or speaking again." if language == "english" else "Speech not detected. Please speak or type again."
            return JSONResponse(content={"response": response})

    language = detect_language(message)
    print(f"Received message: '{message}' (Language: {language})")  # Debug log

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
        print(f"Checking field: {field}, Keywords: {keywords}, Message words: {message_words}")  # Debug log
        for word in message_words:
            if match_keyword(word, keywords):
                print(f"Matched field: {field} with word: {word}")  # Debug log
                response = get_heart_disease_data(patient_id, field, language)
                text_to_speech(response)
                session_data["chat_state"] = "initial"
                sessions[session_id] = session_data
                return JSONResponse(content={"response": response})

    # Handle other requests with fuzzy matching
    if match_keyword(message, ['blood test', 'آزمایش خون']):
        print("Matched: blood test")  # Debug log
        response = get_test_results(patient_id, 'blood test', language)
        text_to_speech(response)
        session_data["chat_state"] = "initial"
        sessions[session_id] = session_data
        return JSONResponse(content={"response": response})
    elif match_keyword(message, ['blood pressure', 'فشار خون']):
        print("Matched: blood pressure")  # Debug log
        response = get_blood_pressure(patient_id, language)
        text_to_speech(response)
        session_data["chat_state"] = "initial"
        sessions[session_id] = session_data
        return JSONResponse(content={"response": response})
    elif match_keyword(message, ['blood sugar', 'قند خون']):
        print("Matched: blood sugar")  # Debug log
        response = get_latest_blood_sugar(patient_id, language)
        text_to_speech(response)
        session_data["chat_state"] = "initial"
        sessions[session_id] = session_data
        return JSONResponse(content={"response": response})
    elif match_keyword(message, ['treatment', 'درمان']):
        print("Matched: treatment")  # Debug log
        response = get_treatment_info(patient_id, language)
        text_to_speech(response)
        session_data["chat_state"] = "initial"
        sessions[session_id] = session_data
        return JSONResponse(content={"response": response})
    elif match_keyword(message, ['other test', 'تست دیگر']):
        print("Matched: other test")  # Debug log
        response = "test hesam" if language == "english" else "تست حسام"
        text_to_speech(response)
        session_data["chat_state"] = "initial"
        sessions[session_id] = session_data
        return JSONResponse(content={"response": response})

    chat_state = session_data["chat_state"]
    if chat_state == "initial" and match_keyword(message, ['hello', 'hi', 'سلام']):
        print("Matched: hello/hi/سلام")  # Debug log
        session_data["chat_state"] = "asked_how_are_you"
        response = f"Hi {patient_name}, how are you today?" if language == "english" else f"سلام {patient_name}، امروز چطور هستید؟"
        text_to_speech(response)
        sessions[session_id] = session_data
        return JSONResponse(content={"response": response})

    elif chat_state == "asked_how_are_you":
        if any(match_keyword(message, [keyword]) for keyword in ['good', 'fine', 'great', 'okay', 'bad', 'خوب', 'بد']):
            print("Matched: response to how are you")  # Debug log
            session_data["chat_state"] = "ready_to_assist"
            response = f"Great {patient_name}! How can I assist you today?" if language == "english" else f"عالیه {patient_name}! چطور می‌تونم بهتون کمک کنم؟"
            text_to_speech(response)
            sessions[session_id] = session_data
            return JSONResponse(content={"response": response})
        else:
            response = f"Sorry {patient_name}, I didn’t understand. How are you today?" if language == "english" else f"متاسفم {patient_name}، متوجه نشدم. امروز چطور هستید؟"
            text_to_speech(response)
            return JSONResponse(content={"response": response})

    if chat_state == "ready_to_assist" or match_keyword(message, ['hello', 'hi', 'سلام']):
        if match_keyword(message, ['hello', 'hi', 'سلام']):
            print("Matched: hello/hi/سلام in ready_to_assist state")  # Debug log
            for field, keywords in field_keywords.items():
                message_words = clean_text(message).split()
                for word in message_words:
                    if match_keyword(word, keywords):
                        print(f"Matched field: {field} with word: {word} in ready_to_assist")  # Debug log
                        response = get_heart_disease_data(patient_id, field, language)
                        text_to_speech(response)
                        session_data["chat_state"] = "initial"
                        sessions[session_id] = session_data
                        return JSONResponse(content={"response": response})
            if match_keyword(message, ['blood test', 'آزمایش خون']):
                print("Matched: blood test in ready_to_assist")  # Debug log
                response = get_test_results(patient_id, 'blood test', language)
                text_to_speech(response)
            elif match_keyword(message, ['blood pressure', 'فشار خون']):
                print("Matched: blood pressure in ready_to_assist")  # Debug log
                response = get_blood_pressure(patient_id, language)
                text_to_speech(response)
            elif match_keyword(message, ['blood sugar', 'قند خون']):
                print("Matched: blood sugar in ready_to_assist")  # Debug log
                response = get_latest_blood_sugar(patient_id, language)
                text_to_speech(response)
            elif match_keyword(message, ['treatment', 'درمان']):
                print("Matched: treatment in ready_to_assist")  # Debug log
                response = get_treatment_info(patient_id, language)
                text_to_speech(response)
            else:
                response = f"How can I assist you today?" if language == "english" else f"چطور می‌تونم بهتون کمک کنم؟"
                text_to_speech(response)
            session_data["chat_state"] = "initial"
            sessions[session_id] = session_data
            return JSONResponse(content={"response": response})
        else:
            response = "Please specify what you need, e.g., 'heart rate', 'blood pressure', 'blood sugar', 'diabetes', or 'treatment'." if language == "english" else "لطفاً بگید چی نیاز دارید، مثلاً 'ضربان قلب'، 'فشار خون'، 'قند خون'، 'دیابت' یا 'درمان'."
            text_to_speech(response)
            return JSONResponse(content={"response": response})

    response = "Please specify what you need, e.g., 'heart rate', 'blood pressure', 'blood sugar', 'diabetes', or 'treatment'." if language == "english" else "لطفاً بگید چی نیاز دارید، مثلاً 'ضربان قلب'، 'فشار خون'، 'قند خون'، 'دیابت' یا 'درمان'."
    print("No match found, returning default response.")  # Debug log
    text_to_speech(response)
    return JSONResponse(content={"response": response})