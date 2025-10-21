import os
import json
import pymysql
from http.server import BaseHTTPRequestHandler
from openai import OpenAI

# Load .env locally (only for local testing)
if os.getenv("VERCEL") is None:
    from dotenv import load_dotenv
    load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# DB credentials
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


def analyze_feedback_message(message):
    prompt = (
        "You are a helpful assistant analyzing patient feedback. "
        "Give each of the following a score from 1 (very bad) to 10 (excellent): doctor, nurse, hospital. "
        "If not mentioned, give a score of 5. Explain why you gave those scores in a 'Notes Analysis'. "
        "Respond ONLY in JSON format like this:\n"
        "{ \"doctor\": 8, \"nurse\": 5, \"hospital\": 9, \"notes\": \"...\" }"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )

    return json.loads(completion.choices[0].message.content.strip())


# ✅ Vercel-compatible HTTP handler
ALLOWED_ORIGINS = [
    "http://localhost:9002",
    "https://surveyai.im"
]

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_response(403)
            self.send_header("Access-Control-Allow-Origin", "null")

        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

   

        def do_GET(self):
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, message, doctor_score, nurse_score, hospital_score, notes_analysis, created_at FROM analyzed_feedback ORDER BY created_at DESC")
                result = cursor.fetchall()
            conn.close()

            # Convert datetime objects to string
            for row in result:
                if 'created_at' in row and row['created_at'] is not None:
                    row['created_at'] = row['created_at'].isoformat()

            self.respond(200, {
                "status": "success",
                "data": result
            })

        except Exception as e:
            self.respond(500, {"error": str(e)})