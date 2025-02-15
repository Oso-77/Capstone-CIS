import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# OpenAI connection (fetch API key from .env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to MySQL database (fetch credentials from .env)
def connect_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        print("Successfully Extracted Data")
        return connection
    except mysql.connector.Error as err:
        print(f"Database Connection Failure: {err}")
        return None

# Fetch responses from MySQL
def fetch_feedback():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT entryID, comment1, comment2, comment3 FROM feedback")
        return cursor.fetchall()

# Generate actionable insights from OpenAI(ChatGPT) for a given feedback.
def generate_insights(feedback):
    if not feedback:
        return "No feedback provided."
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Most cost effective model currently 2/7/25
        messages=[
            {"role": "system", "content": "You are helpful assistant that is goingt to take user feedback and provide actionable insights based on employee feedback."},
            {"role": "user", "content": f"Provide 1 actionable insight for: {feedback} to keep things simple keep your resonses strictly to text as they will be stored in a database."}
        ]
    )
    return response.choices[0].message.content

# Store insights back into MySQL
def store_insights(entryID, gpt_answers):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        query = """
            UPDATE feedback
            SET gpt_answer_1 = %s, gpt_answer_2 = %s, gpt_answer_3 = %s
            WHERE entryID = %s
        """
        cursor.execute(query, (gpt_answers[0], gpt_answers[1], gpt_answers[2], entryID))
        connection.commit()

# Main function to process feedback and generate insights
def process_feedback():
    feedback_entries = fetch_feedback()
    if feedback_entries:
        for entryID, comment1, comment2, comment3 in feedback_entries:
            gpt_answers = [generate_insights(comment) for comment in [comment1, comment2, comment3]]
            store_insights(entryID, gpt_answers)

process_feedback()
