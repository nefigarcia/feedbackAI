import os
import json
import pymysql
from openai import OpenAI

# Load .env locally
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

print("API survey.py loaded.")
# ✅ Correct Vercel entry point
def handler(event, context):
    print("survey handler invoked.")
    try:
        if request.method != "POST":
            return {
                "statusCode": 405,
                "body": "Method Not Allowed"
            }

        body = request.json()
        message = body.get("message", "").strip()

        if not message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'message' field"})
            }

        analysis = analyze_feedback_message(message)

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO analyzed_feedback (message, doctor_score, nurse_score, hospital_score, notes_analysis)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                message,
                analysis.get("doctor", 5),
                analysis.get("nurse", 5),
                analysis.get("hospital", 5),
                analysis.get("notes", "")
            ))
            conn.commit()
        conn.close()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "success",
                "data": analysis
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
