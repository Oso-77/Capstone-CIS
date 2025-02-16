import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
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

# Fetch responses to survey from MySQL database.
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

## Prompt for Categorization of the feedback in gpt_answer_1, gpt_answer_2, gpt_answer_3
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


## Iterates through database and updates the survey_category column with the appropriate category.
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


##categorize_existing_feedback()


def fetch_category_counts():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT survey_category, COUNT(*) FROM feedback GROUP BY survey_category")
        return cursor.fetchall()
    return []

def generate_visuals():
    category_counts = fetch_category_counts()

    if category_counts:
        # Data for charts
        categories = [row[0] for row in category_counts]
        counts = [row[1] for row in category_counts]

        # Create a figure with 1 row and 2 columns for side-by-side plots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Pie chart
        ax1.pie(counts, labels=categories, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax1.set_title('Category Distribution (Pie Chart)')
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Histogram (Bar chart)
        ax2.bar(categories, counts, color=plt.cm.Paired.colors)
        ax2.set_xlabel('Categories')
        ax2.set_ylabel('Count')
        ax2.set_title('Category Distribution (Bar Chart)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.set_yticks(range(0, max(counts) + 1))

        plt.tight_layout()  # Adjust layout to avoid clipping labels
        plt.savefig('category_side_by_side.png')  # Save the side-by-side chart as an image file
        plt.show()  # Display the charts side by side

        print("Side-by-side charts saved and displayed successfully.")
    else:
        print("No category data available.")


##generate_visuals()

def generate_top_level_summary():
    """
    Fetches GPT-generated answers and their associated survey categories,
    combines them into a summary prompt, and uses GPT to produce a concise,
    bullet-point top-level view of the most prevalent issues (fit for one page).
    """
    connection = connect_db()
    if not connection:
        print("Database connection error.")
        return

    cursor = connection.cursor()
    # Retrieve the relevant columns from the feedback table.
    cursor.execute("SELECT survey_category, gpt_answer_1, gpt_answer_2, gpt_answer_3 FROM feedback")
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    
    if not rows:
        print("No feedback data found.")
        return

    # Combine data from each row into one aggregated text block.
    combined_text = ""
    for row in rows:
        category, ans1, ans2, ans3 = row
        combined_text += f"Category: {category}\n"
        combined_text += f"- {ans1}\n"
        combined_text += f"- {ans2}\n"
        combined_text += f"- {ans3}\n\n"

    # Construct the prompt for GPT.
    prompt = (
        "You are a business consultant summarizing employee feedback. "
        "Based on the aggregated GPT-generated insights and their categories provided below, "
        "please provide a concise, bullet-point summary of the most prevalent issues or those that should be addressed first. "
        "Ensure the summary fits on one page. Return only bullet points.\n\n"
        f"Feedback Data:\n{combined_text}"
    )

    # Query GPT to generate the summary.
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Adjust to your preferred model if necessary
        messages=[
            {"role": "system", "content": "You are a business consultant that provides concise summaries."},
            {"role": "user", "content": prompt}
        ]
    )
    summary = response.choices[0].message.content.strip()
    print("Top-Level Summary:")
    print(summary)







generate_top_level_summary()
