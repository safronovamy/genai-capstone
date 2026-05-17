import os
import time

import streamlit as st
from dotenv import load_dotenv

from travelmate.orchestrator.travel_orchestrator import TravelOrchestrator
from travelmate.services.audit_service import save_audit_event
from travelmate.services.feedback_service import save_feedback
from travelmate.services.metrics_service import MetricsService
from travelmate.services.rag_service import collection


@st.cache_resource
def get_orchestrator():
    return TravelOrchestrator()


load_dotenv()
APP_PASSWORD = os.getenv("APP_PASSWORD")


def check_access() -> bool:
    if not APP_PASSWORD:
        st.warning("Access control is not configured. Set APP_PASSWORD in .env.")
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("TravelMate Access")
    password = st.text_input("Enter password", type="password")

    if st.button("Login"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("Access granted")
            st.rerun()
        else:
            st.error("Invalid password")

    return False


def is_rate_limited() -> bool:
    now = time.time()

    st.session_state.request_timestamps = [
        ts
        for ts in st.session_state.request_timestamps
        if now - ts < RATE_LIMIT_WINDOW_SECONDS
    ]

    return len(st.session_state.request_timestamps) >= RATE_LIMIT


def register_request():
    st.session_state.request_timestamps.append(time.time())


st.set_page_config(page_title="TravelMate", layout="wide")

if not check_access():
    st.stop()

with st.expander("System Information"):
    st.info(
        "RAG index is loaded from local persistent Chroma storage.\n\n"
        "Rebuild it with:\n"
        "`python -m travelmate.scripts.build_index`"
    )

if collection.count() == 0:
    st.error(
        "Vector index is empty. Run this command first: "
        "`python -m travelmate.scripts.build_index`"
    )
    st.stop()


RATE_LIMIT = 10
RATE_LIMIT_WINDOW_SECONDS = 5 * 60

if "request_timestamps" not in st.session_state:
    st.session_state.request_timestamps = []

if "travel_state" not in st.session_state:
    st.session_state.travel_state = None

if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = ""

if "processed_requests" not in st.session_state:
    st.session_state.processed_requests = 0

if "total_processing_time_ms" not in st.session_state:
    st.session_state.total_processing_time_ms = 0


st.markdown(
    """
# ✈️ TravelMate

### Personalized family-friendly travel planning with weather-aware itineraries
"""
)

with st.container():
    st.subheader("Plan Your Trip")

    user_message = st.text_area(
        "Describe your ideal trip",
        value=(
            ""
        ),
        height=120,
    )

    col1, col2 = st.columns([4, 1])

    with col1:
        consent = st.checkbox(
            "I consent to processing this request for itinerary generation."
        )

    with col2:
        generate_clicked = st.button(
            "✨ Generate Plan",
            key="plan_trip_button",
            use_container_width=True,
        )


if generate_clicked:
    if not consent:
        st.warning("Please provide consent before generating an itinerary.")
        st.stop()

    if is_rate_limited():
        st.error("Rate limit reached. Please wait before sending another request.")
        st.stop()

    register_request()

    orchestrator = get_orchestrator()

    with st.spinner("Planning your trip..."):
        st.session_state.travel_state = orchestrator.plan_trip(user_message)
        st.session_state.last_user_message = user_message

        save_audit_event(st.session_state.travel_state)

        trace = st.session_state.travel_state.agent_trace
        total_latency_ms = sum(item.get("latency_ms", 0) for item in trace)

        st.session_state.processed_requests += 1
        st.session_state.total_processing_time_ms += total_latency_ms


state = st.session_state.travel_state

if state:
    trace = state.agent_trace

    successful_steps = len(
        [item for item in trace if item.get("status") == "success"]
    )

    total_steps = len(
        [item for item in trace if item.get("status") in ["success", "error"]]
    )

    success_rate = successful_steps / total_steps if total_steps else 0
    total_latency_ms = sum(item.get("latency_ms", 0) for item in trace)

    avg_latency_ms = (
        st.session_state.total_processing_time_ms
        / st.session_state.processed_requests
        if st.session_state.processed_requests
        else 0
    )

    # ---------------- USER-FACING OUTPUT ----------------

    st.markdown("---")
    st.subheader("🧭 Trip Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Destination", state.preferences.get("city", "Unknown"))
    col2.metric(
        "Duration",
        f"{state.preferences.get('duration_days', 'N/A')} days",
    )
    col3.metric("Budget", state.preferences.get("budget", "N/A"))
    col4.metric("Pace", state.preferences.get("pace", "N/A"))

    st.subheader("🌦️ Weather Impact")

    weather = state.weather or {}
    daily_forecast = weather.get("daily_forecast", [])

    rainy_days = sum(
        1 for day in daily_forecast
        if day.get("rain_expected")
    )

    total_forecast_days = len(daily_forecast)

    if total_forecast_days == 0:
        weather_summary = weather.get("classification", "unknown")
    elif rainy_days == 0:
        weather_summary = "mostly good"
    elif rainy_days == total_forecast_days:
        weather_summary = "rainy"
    else:
        weather_summary = f"mixed ({rainy_days}/{total_forecast_days} rainy days)"

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Trip weather",
        weather_summary,
    )
    col2.metric(
        "Season",
        weather.get("season", "unknown"),
    )
    col3.metric(
        "Source",
        weather.get("source", "unknown"),
    )

    if daily_forecast:
        with st.container(border=True):
            st.markdown("#### Daily Forecast")
            forecast_cols = st.columns(len(daily_forecast))

            for idx, day_weather in enumerate(daily_forecast):
                with forecast_cols[idx]:
                    st.markdown(f"**{day_weather.get('date')}**")
                    st.write(f"🌡️ {day_weather.get('temperature_max_c')}°C")
                    st.write(
                        "🌧️ Rain"
                        if day_weather.get("rain_expected")
                        else "☀️ No rain"
                    )

    st.subheader("✨ AI Trip Overview")
    st.markdown(state.final_answer)

    st.subheader("🗺️ Day-by-Day Plan")

    poi_lookup = {
        poi.get("name"): poi
        for poi in state.retrieved_pois
        if poi.get("name")
    }


    def render_activity(activity):
        if isinstance(activity, dict):
            activity_name = activity.get("name", "Free time")
        else:
            activity_name = activity or "Free time"

        st.markdown(f"**{activity_name}**")

        poi = poi_lookup.get(activity_name)

        if poi:
            description = poi.get("description")
            area = poi.get("area")
            poi_type = poi.get("type")
            budget = poi.get("budget_level")

            if description:
                st.caption(description)

            meta = []
            if poi_type:
                meta.append(f"Type: {poi_type}")
            if area:
                meta.append(f"Area: {area}")
            if budget:
                meta.append(f"Budget: {budget}")

            if meta:
                st.caption(" · ".join(meta))

    days = state.validated_itinerary.get("days", [])

    if days:
        for day in days:
            with st.container(border=True):
                day_title = f"Day {day.get('day')}"
                date = day.get("weather", {}).get("date")

                if date:
                    day_title += f" — {date}"

                st.markdown(f"### {day_title}")

                day_weather = day.get("weather", {})
                if day_weather:
                    rain_note = (
                        "Rain expected"
                        if day_weather.get("rain_expected")
                        else "No rain expected"
                    )
                    st.caption(
                        f"{rain_note}, max temperature "
                        f"{day_weather.get('temperature_max_c')}°C"
                    )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("#### 🌅 Morning")
                    render_activity(day.get("morning"))

                with col2:
                    st.markdown("#### 🏙️ Afternoon")
                    render_activity(day.get("afternoon"))

                with col3:
                    st.markdown("#### 🌙 Evening")
                    render_activity(day.get("evening"))
    else:
        st.markdown(state.final_answer)

    st.subheader("💬 Rate This Itinerary")

    with st.container(border=True):
        st.markdown("Help us evaluate the itinerary quality for the demo.")

        rating = st.radio(
            "How useful is this itinerary?",
            options=[1, 2, 3, 4, 5],
            index=3,
            horizontal=True,
            key="response_rating",
        )

        col1, col2 = st.columns([1, 4])

        with col1:
            submit_feedback = st.button(
                "Submit",
                use_container_width=True,
            )

        with col2:
            st.caption(
                "1 = not useful, 5 = very useful. "
                "Feedback is saved for response quality evaluation."
            )

        if submit_feedback:
            state.user_feedback = {"rating": rating}
            save_feedback(state, rating)
            st.success("Feedback saved")

        state.user_feedback = {"rating": rating}

    st.subheader("🧠 Why This Plan?")

    st.markdown(
        """
This itinerary was generated using:

- destination and POI information from the local RAG knowledge base;
- city guide and travel pattern retrieval;
- live weather data from the MCP/Open-Meteo integration;
- family-friendly pacing rules;
- budget, pace, seasonality, and user interests.
"""
    )

    if state.warnings:
        st.subheader("⚠️ Planning Notes")
        for warning in state.warnings:
            st.warning(warning)

    if state.sources:
        st.subheader("📚 Sources Used")

        for source in state.sources:
            with st.container(border=True):
                st.markdown(f"**{source.get('source', 'Source')}**")

                if source.get("city"):
                    st.write(f"City: {source.get('city')}")

                if source.get("items") is not None:
                    st.write(f"Items: {source.get('items')}")

                if source.get("poi_names"):
                    st.write(", ".join(source.get("poi_names")))

                if source.get("rule_files"):
                    st.write(", ".join(source.get("rule_files")))

    

    # ---------------- TECHNICAL DETAILS ----------------

    st.markdown("---")
    st.subheader("⚙️ Technical Details")
    st.caption("Debug, observability, RAG evidence, and LLM tracing information.")

    with st.expander("Performance Metrics"):
        col1, col2, col3 = st.columns(3)

        col1.metric("Total latency", f"{total_latency_ms} ms")
        col2.metric("Agent success rate", f"{success_rate:.0%}")
        col3.metric(
            "Requests this session",
            st.session_state.processed_requests,
        )

        st.caption(
            f"Average request latency in this session: "
            f"{avg_latency_ms:.0f} ms"
        )

    with st.expander("Technical Agent Trace"):
        for trace_item in state.agent_trace:
            st.write(trace_item)

    with st.expander("Parsed Preferences"):
        st.json(state.preferences)

    with st.expander("Retrieved POIs"):
        st.json(state.retrieved_pois)

    with st.expander("RAG Evidence / Retrieved Rules"):
        st.json(state.retrieved_context)

    with st.expander("Raw Weather Data"):
        st.json(state.weather)

    with st.expander("Planning Constraints Applied"):
        st.json(state.warnings)

    with st.expander("Sources Used"):
        st.json(state.sources)

    with st.expander("Resource Usage Metrics"):
        st.json(MetricsService.get_metrics())

    with st.expander("LLM Token Usage"):
        st.json(state.llm_usage)

    with st.expander("LLM Debug Prompts"):
        st.json(state.llm_debug)

    with st.expander("User Feedback"):
        st.json(state.user_feedback)

    if state.errors:
        with st.expander("Errors"):
            st.json(state.errors)

else:
    st.info("Enter a trip request and click 'Generate Plan' to create an itinerary.")