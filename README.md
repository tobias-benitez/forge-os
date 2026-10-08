# ⚡ ForgeOS: Autonomous Habit & Life Management Engine

ForgeOS is an end-to-end productivity and academic management system built with FastAPI, WhatsApp Cloud API, and Google Gemini AI. It combines a gamified command deck with an autonomous WhatsApp copilot.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    User([User via WhatsApp]) <--> Meta[Meta Cloud API]
    Meta <--> Webhook[FastAPI Backend]
    Webhook <--> Gemini[Google Gemini AI]
    Webhook <--> DB[(SQLite Database)]
    Cron[cron-job.org] -->|Ping every 5 min| Webhook

---

### ✨Features
Gamified Command Deck:

Real-time XP progression, leveling, and attribute radar (Intellect, Vitality, Spirit, Leadership).

Habit tracking: prayer, reading, hydration, and nutrition logs.

Day-specific routine views and syllabus milestones.

Autonomous 24/7 WhatsApp Agent:

Morning Briefing (07:15): Daily scripture, stoic quote, and chronological mission schedule.

Smart Lunch Video (13:00): High-yield educational videos fetched dynamically from YouTube playlists.

Routine Radar: Proactive alerts dispatched 15 minutes before study blocks, workouts, or classes.

Night Audit (22:30): End-of-day review and gratitude journal with repetition prevention.

On-the-fly Updates: Change your lunch playlist instantly by texting playlist <youtube_url>.

Academic & Syllabus Planner:

PDF parser to extract exam dates, units, and weekly study plans.

DEFCON 1 exam countdown alert system.

Adaptive Rescheduling:

Dynamic schedule reorganization via voice note or text message upon unexpected delays.

🛠️ Tech Stack
Backend: Python 3.11+, FastAPI, Uvicorn

Database: SQLAlchemy, SQLite

Frontend: Jinja2 Templates, Tailwind CSS, Lucide Icons

APIs: Meta WhatsApp Cloud API, Google Generative AI (Gemini)

Scheduler: APScheduler, External Cron Heartbeat

⚙️ Environment Variables
Configure your .env file using the following schema:

PORT=8000
ENVIRONMENT=development
TIMEZONE=America/Argentina/Buenos_Aires
GEMINI_API_KEY=your_gemini_api_key_here
WHATSAPP_TOKEN=your_permanent_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verification_token
DATABASE_URL=sqlite:///./forge.db

🚀 Quick Start (Local)
Clone & enter repository:

Bash
git clone [https://github.com/tobias-benitez/forge-os.git](https://github.com/tobias-benitez/forge-os.git)
cd forge-os
Set up virtual environment:

Bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Run the server:

Bash
uvicorn app.main:app --reload
Open http://localhost:8000/dashboard in your browser.

🌐 Production Deployment (Render)
Connect your GitHub repository to a new Render Web Service.

Build Command: pip install -r requirements.txt

Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

Set your production environment variables in the Render dashboard.

Create a recurring 5-minute GET monitor on cron-job.org targeting:
https://<your-render-domain>/api/heartbeat-cron

📄 License
MIT License. Free for educational and personal use.
