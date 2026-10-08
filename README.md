# ⚡ ForgeOS: Autonomous Habit & Life Management Engine

ForgeOS is an end-to-end productivity and academic management system built with **FastAPI**, the **WhatsApp Cloud API**, and **Google Gemini AI**. It pairs an interactive, gamified command deck with an autonomous 24/7 WhatsApp copilot.

## 🏗️ Architecture

```
flowchart TD
    User([User via WhatsApp]) <--> Meta[Meta Cloud API]
    Meta <--> Webhook[FastAPI Backend]
    Webhook <--> Gemini[Google Gemini AI]
    Webhook <--> DB[(SQLite Database)]
    Cron[cron-job.org] -->|Ping every 5 min| Webhook

```

## ✨ Features

### 🎮 Gamified Command Deck

* **Attribute System:** Real-time XP progression, leveling, and an attribute radar covering *Intellect*, *Vitality*, *Spirit*, and *Leadership*.

* **Habit Tracking:** Dedicated logs for prayer, reading, hydration, and nutrition.

* **Academic Milestones:** Day-specific routine views and syllabus deadline monitoring.

### 🤖 Autonomous 24/7 WhatsApp Agent

* **Morning Briefing (07:15):** Daily scripture, stoic reflection, and a chronological agenda for the day.

* **Smart Lunch Video (13:00):** High-yield educational videos fetched dynamically from curated YouTube playlists.

* **Routine Radar:** Proactive reminders dispatched 15 minutes before study blocks, workouts, or classes.

* **Night Audit (22:30):** End-of-day review and gratitude journal featuring repetition prevention.

* **On-the-fly Updates:** Update your lunch playlist instantly by texting `playlist <youtube_url>`.

### 📚 Academic & Syllabus Planner

* **Automated Ingestion:** PDF parser that extracts exam dates, units, and weekly study plans.

* **DEFCON 1 Countdown:** Escalating alert system for approaching high-stakes exams.

### 🔄 Adaptive Rescheduling

* **Dynamic Restructuring:** Automatically recalculates your daily schedule via voice note or text message whenever unexpected delays occur.

## 🛠️ Tech Stack

| **Domain** | **Technologies** | 
| **Backend** | Python 3.11+, FastAPI, Uvicorn | 
| **Database** | SQLAlchemy, SQLite | 
| **Frontend** | Jinja2 Templates, Tailwind CSS, Lucide Icons | 
| **AI & APIs** | Meta WhatsApp Cloud API, Google Generative AI (Gemini) | 
| **Automation** | APScheduler, External Cron Heartbeat | 

## ⚙️ Environment Variables

Create a `.env` file in the root directory and populate it with the following configuration:

```
PORT=8000
ENVIRONMENT=development
TIMEZONE=America/Argentina/Buenos_Aires

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# WhatsApp Cloud API
WHATSAPP_TOKEN=your_permanent_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verification_token

# Persistence
DATABASE_URL=sqlite:///./forge.db

```

## 🚀 Quick Start (Local Setup)

### 1. Clone the repository

```
git clone https://github.com/tobias-benitez/forge-os.git
cd forge-os

```

### 2. Set up a virtual environment

```
# Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/macOS:
source venv/bin/activate

```

### 3. Install dependencies

```
pip install -r requirements.txt

```

### 4. Run the development server

```
uvicorn app.main:app --reload

```

Access the command deck at <http://localhost:8000/dashboard>.

## 🌐 Production Deployment (Render)

1. Connect your GitHub repository to a new **Web Service** on Render.

2. Configure service parameters:

   * **Build Command:** `pip install -r requirements.txt`

   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. Add your production environment variables in the Render dashboard.

4. Set up an external heartbeat to prevent cold starts:

   * Create a recurring 5-minute `GET` task on [cron-job.org](https://cron-job.org) targeting:

     ```
     https://<your-render-domain>/api/heartbeat-cron
     
     ```

## 📄 License

Distributed under the MIT License. Free for educational and personal use.