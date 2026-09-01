import os
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import time
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from services.vision.exercise_video_processor import VideoProcessor as VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_user_exercises
from services.coaching.voiceepipeline import VoicePipeline
import pandas as pd


def main():
    st.set_page_config(
        page_icon="🏋️",
        page_title="AI Real-Time Gym Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    init_db()

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    if not render_login_wall():
        return

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                from groq import Groq
                from services.coaching.llm import LLMCoach
                from services.coaching.tts import TextToSpeech
                client = Groq(api_key=groq_api_key)
                llm = LLMCoach(client)
                tts = TextToSpeech()
                st.session_state.voice_pipeline = VoicePipeline(llm, tts)
            except Exception as e:
                pass

    workout_started = st.session_state.get("workout_started", False)

    with st.sidebar:
        st.title("AI REAL-TIME GYM COACH")

        username = st.session_state.get("username")
        if username:
            st.caption(f" Login as {username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:

            plan_exercise=st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")
            plan_sets=st.number_input("Sets", min_value=1, max_value=50, key="plan_sets", step=1)
            plan_reps=st.number_input("Reps Per Set", min_value=1, max_value=100, key="plan_reps", step=1)
            st.markdown("")

            start_session_button = st.button("Start Workout", use_container_width=True, key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed =0
                st.session_state.last_notified_sets_completed=0
                st.session_state.last_notified_workout_complete= False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** : -- {sets} sets / {reps} reps")

            end_session_button = st.button("End Session", key="end_session_button", use_container_width=True)

            if end_session_button:
                st.session_state.workout_started = False
                st.rerun()

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            total_sets = st.session_state.get("target_sets")

            st.subheader("Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {total_sets}")

            st.divider()

            if exercise == "squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.get('knee_angle', 0)}°")
                st.metric("Back Angle", f"{st.session_state.get('back_angle', 0)}°")
                st.metric("Depth Status", st.session_state.get('depth_status', 'N/A'))

            elif exercise == "lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.get('front_knee_angle', 0)}°")
                st.metric("Torso Angle", f"{st.session_state.get('torso_angle', 0)}°")
                st.metric("Balance Status", f"{st.session_state.get('balance_status', 'N/A')}")

            elif exercise == "pushups":
                st.subheader("Pushup Metrics")
                st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                st.metric("Body Alignment", st.session_state.get('body_alignment', 'N/A'))
                st.metric("Hip Status", f"{st.session_state.get('hip_status', 'N/A')}")

            elif exercise == "bicep_curls":
                st.subheader("Bicep Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                st.metric("Shoulder Stability", st.session_state.get('shoulder_status', 'N/A'))
                st.metric("Swing Detection", st.session_state.get('swing_status', 'N/A'))

            elif exercise == "shoulder_press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                st.metric("Arm Extension", st.session_state.get('extension_status', 'N/A'))
                st.metric("Back Arch", st.session_state.get('back_arc_status', 'N/A'))

    st.title("AI REAL-TIME GYM TRAINER")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")

    if not workout_started:
        st.markdown(
            """
            <div style="
                border:10px dashed #444;
                border-radius:0px;
                padding:48px 32px;
                text-align:center;
                color:#888;
                margin-top:32px;
            ">
                <h2 style="color: #ccc; margin-bottom:8px;">Set Your Workout Plan</h2>
                <p style="font-size:1.05rem;">
                   Select an exercise, sets and reps in the sidebar,<br>
                   then click <strong>Start Session</strong> to activate the camera and AI coach
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        exercise = st.session_state.get("exercise_type", "squats")
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]},
                    {"urls": ["stun:stun1.l.google.com:19302"]},
                    {"urls": ["stun:stun2.l.google.com:19302"]},
                    {"urls": ["stun:global.stun.twilio.com:3478"]},
                    {
                        "urls": [
                            "turn:openrelay.metered.ca:80",
                            "turn:openrelay.metered.ca:443",
                            "turn:openrelay.metered.ca:443?transport=tcp"
                        ],
                        "username": "openrelay",
                        "credential": "openrelay"
                    }
                ]
            },
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )

        if context.video_processor:
            context.video_processor.set_exercise(exercise)

        sync_metrics_update(context)

        if st.session_state.get("audio_to_play"):
            VoicePipeline.autoplay_audio(st.session_state.audio_to_play)
            st.session_state.audio_to_play = None

        inject_webrtc_styles()
    
    st.divider()

    st.markdown("#### Workout History")
    user_id = st.session_state.get("user_id")

    if isinstance(user_id, int):
        history_rows = get_user_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": int(row['time']),
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": 'sum',
                "Time (sec)": 'sum'
            }).reset_index()
            agg_df.index += 1

            st.table(agg_df, border="horizontal")
        else:
            st.info("No workout history found")


if __name__ == "__main__":
    main()
