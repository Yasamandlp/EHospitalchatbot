
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_session import Session
from flasgger import Swagger

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Swagger config
app.config['SWAGGER'] = {
    'title': 'e-Hospital API',
    'uiversion': 3
}
swagger = Swagger(app)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/patients', methods=['GET'])
def get_patients():
    """Retrieve all patients
    ---
    responses:
      200:
        description: A list of patients
    """
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    conn.close()
    return jsonify([dict(p) for p in patients])

@app.route('/message', methods=['POST'])
def send_message():
    """Send a message from a patient to a doctor
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: Message
          required:
            - patient_id
            - doctor_id
            - message
          properties:
            patient_id:
              type: string
            doctor_id:
              type: string
            patient_FName:
              type: string
            patient_LName:
              type: string
            message:
              type: string
    responses:
      200:
        description: Message stored successfully
    """
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (patient_id, doctor_id, patient_FName, patient_LName, message, time_stamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (data['patient_id'], data['doctor_id'], data['patient_FName'], data['patient_LName'], data['message'])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Message stored successfully"}), 200

@app.route('/messages/<patient_id>', methods=['GET'])
def get_messages(patient_id):
    """Retrieve all messages for a patient
    ---
    parameters:
      - name: patient_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: A list of messages for the given patient
    """
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages WHERE patient_id = ?', (patient_id,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in messages])

@app.route('/treatments/<patient_id>', methods=['GET'])
def get_treatments(patient_id):
    """Retrieve treatment history for a patient
    ---
    parameters:
      - name: patient_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: A list of treatments
    """
    conn = get_db_connection()
    treatments = conn.execute('SELECT * FROM patients_treatment WHERE patient_id = ?', (patient_id,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in treatments])

if __name__ == '__main__':
    app.run(debug=True)
