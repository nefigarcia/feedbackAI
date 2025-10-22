import os
import json
import pymysql
from http.server import BaseHTTPRequestHandler

# Load .env locally (only for local testing)
if os.getenv("VERCEL") is None:
    from dotenv import load_dotenv
    load_dotenv()

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

# Vercel-compatible HTTP handler
ALLOWED_ORIGINS = [
    "http://localhost:9002",
    "https://surveyai.rosystems.net"
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

    def respond(self, status_code, body):
        origin = self.headers.get("Origin")
        self.send_response(status_code)

        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", "null")

        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps(body, default=str).encode("utf-8"))
