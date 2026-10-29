# 🏋️ AI Real-Time Gym Trainer

A Streamlit web app that watches your workout through your webcam, counts reps, checks your form using pose detection, and coaches you with live AI voice feedback.

## Features

- **Real-time pose detection** using MediaPipe, streamed over WebRTC
- **Supported exercises:** squats, lunges, push-ups, bicep curls, shoulder press
- **Live form metrics** per exercise (knee, elbow, back and torso angles, depth, balance, alignment, swing detection)
- **Workout planner:** choose exercise, sets and reps, and the app tracks your progress set by set
- **Proactive AI voice coaching** using an LLM (Groq) and text-to-speech
- **User login** with per-user **workout history** stored in SQLite (`data.db`)

## Tech Stack

Python · Streamlit · streamlit-webrtc · MediaPipe · OpenCV · Groq API · SQLite · Pandas

## Project Structure

```
├── main.py          # Streamlit entry point (UI, sidebar, session flow)
├── core/            # Core logic
├── detectors/       # Exercise-specific pose/angle detectors
├── ml_models/       # ML models
├── services/        # Auth, config, coaching (LLM + TTS), persistence, tracking, UI, vision
├── static/          # CSS and fonts
├── .streamlit/      # Streamlit config
├── requirements.txt # Python dependencies
└── packages.txt     # System packages (for deployment)
```

## Getting Started

### Prerequisites
- Python 3.9+
- A webcam
- A [Groq API key](https://console.groq.com/) (for AI voice coaching)

### Installation

```bash
git clone https://github.com/Gopal090/Real_Time_Video_AI_Gym_Trainer_Mediapipe.git
cd Real_Time_Video_AI_Gym_Trainer_Mediapipe
pip install -r requirements.txt
```

### Configure the API key

Set it as an environment variable:

```bash
export GROQ_API_KEY="your_key_here"      # Windows: set GROQ_API_KEY=your_key_here
```

or add it to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your_key_here"
```

### Run

```bash
streamlit run main.py
```

## How to Use

1. Log in or sign up.
2. In the sidebar, pick an exercise, number of sets and reps per set.
3. Click **Start Workout** and allow camera access.
4. Exercise in view of the camera. Reps, angles and form status update live, and the AI coach speaks feedback.
5. Click **End Session** to finish. Your history appears at the bottom of the page.

## Notes

- Without a Groq API key, the app still runs but without LLM voice coaching.
- Stand far enough back that your full body is visible, with good lighting.

## License

<!-- TODO: add a license -->
