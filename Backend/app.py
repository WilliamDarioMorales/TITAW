import os
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from deepface import DeepFace
import psycopg2

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname="flaskdb",
        user="admin",
        password="admin",
        host="localhost",
        port="5432"
    )

# Obtener imagen del usuario desde la base de datos
def get_image_from_db(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT imagen FROM usuarios WHERE correo = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener la imagen: {e}")
        result = None
    finally:
        cursor.close()
        conn.close()
    if result:
        return np.frombuffer(result[0], dtype=np.uint8)
    return None

# Registrar asistencia y estado emocional en la base de datos
def register_attendance(email, emotion):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        query = """
            INSERT INTO registro (correo, fecha, emocion)
            VALUES (%s, %s, %s);
        """
        cursor.execute(query, (email, timestamp, emotion))
        conn.commit()
    except Exception as e:
        print(f"Error al registrar la asistencia: {e}")
    finally:
        cursor.close()
        conn.close()

# Ruta principal de autenticación
@app.route("/authenticate", methods=["POST"])
def authenticate():
    if 'image' not in request.files or 'email' not in request.form:
        return jsonify({"error": "Faltan parámetros"}), 400

    email = request.form['email']
    uploaded_image = request.files['image'].read()
    uploaded_image_np = np.frombuffer(uploaded_image, dtype=np.uint8)
    uploaded_image_cv2 = cv2.imdecode(uploaded_image_np, cv2.IMREAD_COLOR)

    # Obtener imagen del usuario desde la base de datos
    stored_image_data = get_image_from_db(email)
    if not stored_image_data:
        return jsonify({"error": "Usuario no encontrado"}), 404

    stored_image_cv2 = cv2.imdecode(stored_image_data, cv2.IMREAD_COLOR)

    # Comparar imágenes con DeepFace
    try:
        result = DeepFace.verify(
            uploaded_image_cv2,
            stored_image_cv2,
            enforce_detection=True,  # Forzar detección de rostro
            detector_backend="opencv"  # Opcional: puedes probar mtcnn, dlib, retinaface
        )
        print("DeepFace result:", result)  # Log para depuración
        
        # Ajuste de umbral relajado temporalmente
        if result['distance'] < 0.7:  # Umbral más alto para mayor tolerancia
            analysis = DeepFace.analyze(uploaded_image_cv2, actions=["emotion"], enforce_detection=False)
            dominant_emotion = analysis[0]['dominant_emotion']
            print("Emoción detectada:", dominant_emotion)  # Log para depuración
            register_attendance(email, dominant_emotion)
            return jsonify({"result": "Autenticación exitosa", "emotion": dominant_emotion}), 200
        else:
            print("Distancia alta:", result['distance'])  # Log para depuración
            return jsonify({"error": "No se reconoce al usuario"}), 401
    except Exception as e:
        print(f"Error en la comparación: {e}")
        return jsonify({"error": f"Error en la comparación: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
