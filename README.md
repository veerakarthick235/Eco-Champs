
# EcoChamps - Gamified Environmental Education Platform

EcoChamps is an interactive, gamified web platform designed for schools and colleges in India to foster environmental literacy and promote sustainable habits. Moving beyond theoretical textbook knowledge, EcoChamps provides a hands-on, engaging experience that aligns with India's SDG goals and the National Education Policy (NEP) 2020's emphasis on experiential learning.

The platform encourages students to participate in real-world environmental activities, test their knowledge with AI-generated quizzes, and compete with peers, turning environmental education into a rewarding and impactful journey.

## Problem Statement

Despite the rising urgency of climate change, environmental education remains largely theoretical in many Indian schools and colleges. There is a lack of engaging tools that motivate students to adopt eco-friendly practices or understand the direct consequences of their lifestyle choices. Traditional methods often fail to instill sustainable habits or inspire youth participation in local environmental efforts.

## Key Features

### For Students

- **User Authentication**: Secure registration and login system for students and teachers.
- **Personalized Dashboard**: Displays user's name, Eco-Points, earned badges, and daily login streak.
- **Real-World Challenges**: A list of actionable tasks (e.g., planting a sapling, waste segregation) that students can complete.
- **Task Verification**: Students can upload photo proof for challenges, which can be reviewed by teachers.
- **Dynamic AI Quizzes**: An advanced quiz interface powered by the **Google Gemini API**.
  - Generates 25 unique questions for 10 different environmental topics.
  - Features a question palette to track attended, unanswered, and "marked for review" questions.
- **Points & Badges System**: Earn "Eco-Points" for completing challenges and quizzes to unlock digital badges.
- **Leaderboards**: School-wise and city-wise leaderboards to foster healthy competition.

### For Teachers / Admins

- **Admin Panel**: A dedicated dashboard for teachers to manage the platform.
- **Submission Verification**: Teachers can review, approve, or reject challenge submissions from students.
- **Challenge Management**: Teachers have the ability to add new challenges to the platform.

## Technology Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: MongoDB (managed via MongoDB Atlas)
- **APIs**: Google Gemini API for dynamic quiz generation
- **Libraries**:
  - `Flask-Login`: User session management and authentication.
  - `Flask-Bcrypt`: Password hashing for security.
  - `PyMongo`: Python driver for MongoDB.
  - `python-dotenv`: For managing environment variables.
  - `Pillow`, `Werkzeug`: For handling file uploads.

## Project Structure

```
EcoChamps/
├── app.py                 # Main Flask application logic
├── modules/
│   └── gemini_handler.py    # Handles Gemini API calls and provides fallback quizzes
├── static/
│   ├── css/
│   │   └── style.css      # All CSS styles
│   ├── js/
│   │   └── script.js      # Client-side logic for the quiz and other interactions
│   └── uploads/           # Stores images uploaded for challenge verification
├── templates/
│   ├── admin/             # HTML templates for the teacher/admin panel
│   │   ├── add_challenge.html
│   │   └── dashboard.html
│   ├── challenges.html
│   ├── dashboard.html
│   ├── layout.html
│   ├── leaderboard.html
│   ├── login.html
│   ├── quiz.html
│   ├── register.html
│   └── submit_challenge.html
├── .env                     # File for environment variables (API keys, etc.)
├── requirements.txt         # List of Python dependencies
└── README.md                # This file
```

## Setup and Installation

Follow these steps to get the project running on your local machine.

**1. Clone the Repository**

```bash
git clone <your-repository-url>
cd EcoChamps
```

**2. Create a Python Virtual Environment**

- **Windows:**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Set up Environment Variables**  
Create a `.env` file in the root directory:

```
# Google AI Studio API Key
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"

# MongoDB Atlas Connection String
MONGO_URI="YOUR_MONGODB_CONNECTION_STRING_HERE"

# Flask secret key
FLASK_SECRET_KEY="YOUR_SUPER_SECRET_FLASK_KEY"
```

**5. Create Uploads Folder**

```bash
mkdir static/uploads
```

## How to Run the Application

1. Activate your virtual environment.
2. Run the Flask application:

```bash
python app.py
```

3. The server pre-loads quizzes from the Gemini API (takes ~40-60 seconds).
4. Open your browser at: `http://127.0.0.1:5000`

## Future Enhancements

- **Mobile Application**: Develop a native or cross-platform mobile app for better accessibility.
- **Social Sharing**: Allow users to share their badges and achievements on social media.
- **Community Feed**: A section where users can post about their environmental activities.
- **Advanced Analytics**: Detailed dashboards for teacher insights.
- **More Gamification**: Weekly missions, special badges, and team challenges.