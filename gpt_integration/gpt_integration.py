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

# Global persistent connection variable.
db_connection = None

# Get persistent database connection (fetch credentials from .env)
def get_db_connection():
    global db_connection
    if db_connection is None or not db_connection.is_connected():
        db_connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        print("Successfully Connected to the Database")
    return db_connection


# Fetch responses to survey from MySQL database.
def fetch_feedback():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT entryID, comment1, comment2, comment3 
        FROM feedback 
        WHERE gpt_answer_1 IS NULL OR gpt_answer_2 IS NULL OR gpt_answer_3 IS NULL
    """)
    results = cursor.fetchall()
    cursor.close()
    return results


# Generate refined feedback from OpenAI(ChatGPT) for a given feedback.
def refine_feedback(feedback):
    if not feedback:
        return "No feedback provided."
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Most cost effective model currently 2/7/25
        messages=[
            {"role": "system", "content": "You are a helpful assistant that is going to take user feedback and refine it to make it easier to analyze it or to create actionable insights.If the feedback is gibberish, nonsensical, too short, or otherwise invalid, respond with 'Invalid Feedback'."},
            {"role": "user", "content": f"Refine the feedback: {feedback} to keep things simple keep your resonses strictly to text as they will be stored in a database."}
        ]
    )
    return response.choices[0].message.content


# Store insights back into MySQL
def store_insights(entryID, gpt_answers):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        UPDATE feedback
        SET gpt_answer_1 = %s, gpt_answer_2 = %s, gpt_answer_3 = %s
        WHERE entryID = %s
    """
    cursor.execute(query, (gpt_answers[0], gpt_answers[1], gpt_answers[2], entryID))
    connection.commit()
    cursor.close()


# Main function to process feedback and generate insights
def process_feedback():
    feedback_entries = fetch_feedback()
    if feedback_entries:
        for entryID, comment1, comment2, comment3 in feedback_entries:
            gpt_answers = [refine_feedback(comment) for comment in [comment1, comment2, comment3]]
            store_insights(entryID, gpt_answers)
    print("Feedback processed successfully.")
    categorize_existing_feedback()
    generate_cards()

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
      - Invalid (for feedback that is gibberish, nonsensical, or not relevant.)
    
    Returns the category name as a string.
    """
    prompt = (
        f"Given the following feedback: \"{combined_text}\", "
        "please choose the best category from the following options: "
        "'Work Environment', 'Job Satisfaction', 'Management/Leadership', "
        "'Tools/Technology', 'Training/Development', 'Processes/Procedures', 'Invalid'. "
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
    connection = get_db_connection()
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
    cursor.close()
    print("Survey categories updated successfully.")


##categorize_existing_feedback()


def fetch_category_counts():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT survey_category, COUNT(*) FROM feedback GROUP BY survey_category")
    results = cursor.fetchall()
    cursor.close()
    return results


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


def generate_top_level_summary():
    """
    Fetches GPT-generated answers and their associated survey categories,
    combines them into a summary prompt, and uses GPT to produce a concise,
    bullet-point top-level view of the most prevalent issues (fit for one page).
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    # Retrieve the relevant columns from the feedback table.
    cursor.execute("SELECT survey_category, gpt_answer_1, gpt_answer_2, gpt_answer_3 FROM feedback")
    rows = cursor.fetchall()
    cursor.close()
    # Do not close persistent connection here.
    # connection.close()
    
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


def generate_cards():
    """
    Aggregates all GPT answers from the feedback table,
    asks GPT to identify 3-7 top-level issues or trends,
    and stores each trend as (response_text, insight_text, survey_category) in the responses table.
    
    Security measures:
      1. Only analyzes feedback that has a survey_category not equal to "Invalid"
         and where none of the GPT answers are "Invalid Feedback".
      2. Only analyzes feedback that has not already been processed (cards_generated is NULL or 0).
         
    The Category must be one of the following:
      - Work Environment
      - Job Satisfaction
      - Management/Leadership
      - Tools/Technology
      - Training/Development
      - Processes/Procedures
      - Invalid
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 0) Count all new (unprocessed) feedback rows.
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE cards_generated IS NULL OR cards_generated = 0")
        total_new_rows = cursor.fetchone()[0]

        # 1) Retrieve valid, unprocessed feedback entries.
        cursor.execute("""
            SELECT entryID, gpt_answer_1, gpt_answer_2, gpt_answer_3, survey_category 
            FROM feedback 
            WHERE survey_category != 'Invalid'
              AND gpt_answer_1 != 'Invalid Feedback'
              AND gpt_answer_2 != 'Invalid Feedback'
              AND gpt_answer_3 != 'Invalid Feedback'
              AND (cards_generated IS NULL OR cards_generated = 0)
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("No valid new feedback available to analyze.")
            print(f"Skipped {total_new_rows} feedback rows.")
            cursor.close()
            return

        all_feedback = []
        processed_ids = []  # To track feedback rows that are processed.
        for entryID, ans1, ans2, ans3, survey_category in rows:
            # Only keep non-empty strings.
            feedback_parts = [ans for ans in (ans1, ans2, ans3) if ans]
            if feedback_parts:
                # Merge them into one line per row.
                all_feedback.append(" ".join(feedback_parts))
                processed_ids.append(entryID)
        
        if not all_feedback:
            print("No valid feedback available to analyze.")
            print(f"Skipped {total_new_rows} feedback rows.")
            cursor.close()
            return

        # 2) Create one big chunk of text representing all valid feedback.
        combined_feedback = "\n".join(all_feedback)

        # 3) Build prompt for GPT.
        num_feedback_rows = len(rows)

        if num_feedback_rows <= 3:
            trend_range = "1-2"
        elif num_feedback_rows <= 8:
            trend_range = "2-5"
        else:
            trend_range = "3-7"

        prompt = (
            f"Identify up to {trend_range} critical or repeating issues, depending on how many distinct themes emerge. If there are fewer clear issues, return fewer."
            "For each issue, provide:\n"
            "- Title: A concise, one-sentence summary of the problem.\n"
            "- Insight: Exactly three sentences of actionable recommendations.\n"
            "- Category: One category from the following list:\n"
            "  'Work Environment', 'Job Satisfaction', 'Management/Leadership', 'Tools/Technology',\n"
            "  'Training/Development', 'Processes/Procedures', 'Invalid'.\n\n"
            "Return each issue in the exact format:\n"
            "Title: <Problem Statement>\n"
            "Insight: <Three-sentence Recommendation>\n"
            "Category: <One Category from the list above>\n\n"
            "No additional text or formatting.\n\n"
            f"All Feedback:\n{combined_feedback}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or your preferred model
            messages=[
                {
                    "role": "system",
                    "content": "You analyze aggregated employee feedback and provide concise, actionable trends."
                },
                {"role": "user", "content": prompt}
            ]
        )

        response_text = response.choices[0].message.content.strip()

        # 4) Parse GPT output.
        lines = [line.strip() for line in response_text.split("\n") if line.strip()]

        card_data = []
        current_title = None
        current_insight = None
        current_category = None

        for line in lines:
            if line.lower().startswith("title:"):
                # If a full set has been built, store it.
                if current_title and current_insight and current_category:
                    card_data.append((current_title, current_insight, current_category))
                current_title = line.split(":", 1)[1].strip()
                current_insight = None
                current_category = None
            elif line.lower().startswith("insight:"):
                current_insight = line.split(":", 1)[1].strip()
            elif line.lower().startswith("category:"):
                current_category = line.split(":", 1)[1].strip()

        # Add the last parsed entry.
        if current_title and current_insight and current_category:
            card_data.append((current_title, current_insight, current_category))

        # 5) Insert the cards into the responses table.
        cursor.executemany(
            "INSERT INTO responses (response_text, insight_text, survey_category) VALUES (%s, %s, %s)",
            card_data
        )
        connection.commit()
        print(f"{len(card_data)} trends inserted into responses table.")

        # 6) Mark the processed feedback entries as analyzed to avoid reprocessing.
        if processed_ids:
            format_strings = ','.join(['%s'] * len(processed_ids))
            update_query = f"UPDATE feedback SET cards_generated = 1 WHERE entryID IN ({format_strings})"
            cursor.execute(update_query, processed_ids)
            connection.commit()
            print(f"Marked {len(processed_ids)} feedback entries as analyzed.")

        # 7) Print analyzed and skipped counts.
        analyzed_count = len(rows)
        skipped_count = total_new_rows - analyzed_count
        print(f"Skipped {skipped_count} feedback rows. ")

    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        cursor.close()
        # Do not close the persistent connection here.
        # connection.close()


process_feedback()