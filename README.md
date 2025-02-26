# The Employee Feedback & Engagement Platform 
A comprehensive employee feedback platform that enables organizations to securely collect, analyze, and respond to feedback using AI-driven insights, engagement metrics, and a user-friendly dashboard.

## Features
- Word-limited responses encourages employees to get down to the root of their feedback, eliminating pressure of needing to write at length
- Interactive employee feedback board for discussions
- AI-powered feedback categorization and insights (Requires access to OpenAI API)

## Installation
1. Clone repository: git clone https://github.com/Oso-77/Capstone-CIS
2. Navigate to directory: Capstone-CIS\Backend
3. Install dependencies:
   - npm install
       - In the event the following are not installed: bcryptjs, jsonwebtoken; install manually
       - npm install bcryptjs
       - npm install jsonwebtoken
   - pip install mysql-connector-python 
   - pip install openai 
   - pip install python-dotenv
4. Create a .env file in Backend root and project root with the following:
   - OPENAI_API_KEY
   - JWT_SECRET
   - DB_HOST
   - DB_USER
   - DB_PASSWORD
   - DB_NAME
   - API_KEY
6. Run "npm run start" within Backend in terminal to start server
7. Navigate to http://localhost:3000/api/login to access the platform

## Functionality
The following pages provide functionality for the platform with integrated role-based access:
- Login - http://localhost:3000/api/login
![login](/Assets/login.png)
- Survey - http://localhost:3000/api/form
![survey](/Assets/survey.png)
- Feedback Dashboard - http://localhost:3000/api/board
![dashboard](/Assets/feedback.png)
- Admin Home - http://localhost:3000/api/admin-home
![ad_home](/Assets/ad_home.png)
- Admin Response Dashboard - http://localhost:3000/api/admin-post
![ad_resp_dash](/Assets/ad_response.png)
- Engagement Metrics - http://localhost:3000/api/engagement-metrics
![metrics](/Assets/metrics.png)

All accounts will have to provide credentials before being granted to the platform.
- Employees can only access the survey page; Admins have access to the entirety of the platform
- Admins will have access to additional dashboards to view employee-submitted feedback, view engagement metrics, respond to feedback, and generate AI-powered responses
