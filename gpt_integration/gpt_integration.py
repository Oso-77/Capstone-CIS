import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta
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

##process_feedback()

def categorize_with_gpt(combined_text):
    """
    Uses GPT to categorize the combined text into one of the six predefined categories.
    
    The categories are:
      - Work Environment: Refers to the physical, social, and cultural conditions in which employees perform their jobs. This includes workplace safety, cleanliness, noise levels, company culture, and overall employee morale.
      - Job Satisfaction: Measures how content employees are with their roles, responsibilities, compensation, recognition, and overall work experience. It reflects whether employees feel valued, motivated, and fulfilled in their jobs.
      - Management/Leadership: Encompasses the effectiveness of supervisors, managers, and executives in guiding teams, making decisions, providing support, and fostering a positive work culture. This includes communication, leadership style, and responsiveness to employee concerns.
      - Tools/Technology: Covers the availability, quality, and efficiency of the tools, software, hardware, and resources employees use to perform their jobs. Issues in this category may include outdated systems, lack of automation, or inadequate support.
      - Training/Development: Focuses on opportunities for employees to enhance their skills, knowledge, and career growth through training programs, mentorship, and professional development initiatives. It also includes access to learning resources and career advancement paths.
      - Processes/Procedures: Involves the effectiveness and efficiency of company workflows, policies, and standard operating procedures (SOPs). This includes how tasks are structured, communication flows, and whether processes support productivity or create unnecessary bottlenecks.
    
    Returns the category name as a string.
    """
    prompt = (
        f"Given the following feedback: \"{combined_text}\", "
        "please choose the best category from the following options: "
        "'Work Environment', 'Job Satisfaction', 'Management/Leadership', "
        "'Tools/Technology', 'Training/Development', 'Processes/Procedures'. "
        "Return only the category name exactly as written."
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use your desired model
        messages=[
            {
                "role": "system", 
                "content": "You are an assistant that categorizes employee feedback into one of six predefined categories."
            },
            {"role": "user", "content": prompt}
        ]
    )
    # Strip any extra whitespace from the response.
    return response.choices[0].message.content.strip()

def categorize_existing_feedback():
    """
    Reads GPT-generated answers (gpt_answer_1, gpt_answer_2, gpt_answer_3) from each row,
    combines them into a single text block, sends that text to GPT for categorization,
    and then updates the survey_category column for that row.
    
    This function can be triggered independently (e.g., via a button in an admin interface).
    """
    connection = connect_db()
    if not connection:
        print("Database connection error.")
        return

    cursor = connection.cursor()
    # Retrieve entryID and GPT answers from the feedback table.
    cursor.execute("SELECT entryID, gpt_answer_1, gpt_answer_2, gpt_answer_3 FROM feedback")
    rows = cursor.fetchall()

    for entryID, ans1, ans2, ans3 in rows:
        # Combine the three GPT answers (ignoring any None values)
        answers = [ans for ans in (ans1, ans2, ans3) if ans]
        combined_text = " ".join(answers)
        # Use GPT to determine the appropriate category.
        category = categorize_with_gpt(combined_text)
        
        # Update the survey_category column for this feedback entry.
        update_query = "UPDATE feedback SET survey_category = %s WHERE entryID = %s"
        cursor.execute(update_query, (category, entryID))
    
    connection.commit()
    print("Survey categories updated successfully.")

categorize_existing_feedback()