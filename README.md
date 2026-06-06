# Smart AI Tutor

A comprehensive AI-powered tutoring application built with Flask, Google Gemini, and Supabase. The app provides a personalized learning experience with an interactive AI tutor, dynamic quiz generation, PDF summarization, and a dashboard to track your study progress.

## 🌟 Features

- **Interactive AI Tutor Chat:** Ask questions, get explanations, and converse with an expert AI tutor powered by Google Gemini 2.5 Flash. Includes session history and math equation support via LaTeX.
- **AI Quiz Generator:** Automatically generate multiple-choice quizzes on any topic to test your knowledge.
- **PDF Summarizer:** Upload PDF documents and have the AI extract key concepts and summarize the text.
- **Smart Dashboard:** Track your study streak, topics mastered, average quiz scores, and view dynamic weakness identification.
- **Task Management & Bookmarks:** Keep track of study tasks and bookmark important concepts or PDF summaries.
- **Secure Authentication:** User signup and login powered by Supabase Auth (or local mock mode for testing).
- **Mock Mode:** Can run entirely locally using an in-memory/JSON store (`mock_db.json`) if Supabase is not configured.

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Werkzeug
- **AI Integration:** Google Generative AI (Gemini API)
- **Database & Auth:** Supabase (PostgreSQL)
- **Frontend:** HTML, CSS, JavaScript (Jinja2 Templates)
- **Document Processing:** PyPDF2
- **Text Rendering:** Python-Markdown

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- A Google Gemini API Key
- (Optional) A Supabase project for database and authentication

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ns18122023-code/Smart-AI-Tutor.git
   cd Smart-AI-Tutor
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add the following:
   ```env
   # Required for AI Features
   GEMINI_API_KEY=your_gemini_api_key_here
   FLASK_SECRET_KEY=your_random_flask_secret_key

   # Optional: For Auth and Database (will fall back to Mock Mode if empty)
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

5. **Run the Application:**
   ```bash
   python app.py
   # Or using flask run:
   flask run
   ```

6. **Access the App:**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📂 Project Structure

- `app.py`: Main Flask application handling routes and API endpoints.
- `templates/`: HTML templates for the UI (Dashboard, Tutor, Quizzes, etc.).
- `static/`: Static assets (CSS, JS, Images).
- `supabase_schema.sql`: Database schema for setting up Supabase tables.
- `mock_db.json`: Local JSON storage for running the app without a database.
- `requirements.txt`: Python dependencies.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License

This project is open-source and available under the MIT License.
