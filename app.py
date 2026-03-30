# ============================================================
# CLIMATE INFRASTRUCTURE & ANOMALY DETECTION COMMAND CENTER
# ============================================================

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Climate Infrastructure & Anomaly Detection",
    page_icon="🏙️",
    layout="wide"
)

# ─────────────────────────────────────────────
# OPTIONAL CSS
# ─────────────────────────────────────────────
def load_css(path="styles.css"):
    try:
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2942/2942206.png", width=90)
st.sidebar.title("⚙️ System Override")

border_locations = {
    "None": None,
    "Leh (Ladakh)": "Leh",
    "Kargil (Ladakh)": "Kargil",
    "Tawang (Arunachal)": "Tawang",
    "Nathu La (Sikkim)": "Nathu La",
    "Kupwara (Kashmir)": "Kupwara",
    "Poonch (J&K)": "Poonch",
    "Amritsar (Punjab)": "Amritsar",
    "Jaisalmer (Rajasthan)": "Jaisalmer",
    "Bhuj (Gujarat)": "Bhuj",
    "Agartala (Tripura)": "Agartala",
    "Moreh (Manipur)": "Moreh",
    "Kavaratti (Lakshadweep)": "Kavaratti"
}

preset = st.sidebar.selectbox("🗺️ Quick Border Location", list(border_locations.keys()))
default_city = border_locations[preset] if border_locations[preset] else ""
city = st.sidebar.text_input("📍 Enter City", default_city)

st.sidebar.markdown("---")
st.sidebar.success("🟢 Systems Online")

if st.sidebar.button("🔄 Reboot Telemetry"):
    st.cache_data.clear()
    st.rerun()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🏙️ Climate Infrastructure & Anomaly Detection Center")
st.caption("Real-time environmental stress monitoring")

# ─────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=600)
def search_location(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "climate-app"}

    params = {
        "q": city_name,
        "format": "json",
        "limit": 5
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10).json()
        return res
    except:
        return []

@st.cache_data(ttl=600)
def get_data(lat, lon):
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,surface_pressure"
    aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm2_5"

    try:
        weather = requests.get(weather_url).json()
        aqi = requests.get(aqi_url).json()
        return weather, aqi
    except:
        st.error("API Error")
        st.stop()

# ─────────────────────────────────────────────
# LOCATION
# ─────────────────────────────────────────────
if not city:
    st.stop()

locations = search_location(city)

if not locations:
    st.error("City not found")
    st.stop()

options = [l["display_name"] for l in locations]
choice = st.selectbox("Select Location", options)

selected = locations[options.index(choice)]
lat = float(selected["lat"])
lon = float(selected["lon"])

st.success(f"Connected to {choice}")

# ─────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────
weather, aqi = get_data(lat, lon)

current = weather.get("current", {})
temp = current.get("temperature_2m", 0)
humidity = current.get("relative_humidity_2m", 0)
wind = current.get("wind_speed_10m", 0)
rain = current.get("precipitation", 0)
pressure = current.get("surface_pressure", 1013)

aqi_score = aqi.get("current", {}).get("us_aqi", 0)

# ─────────────────────────────────────────────
# RISK SCORE
# ─────────────────────────────────────────────
risk_score = min(
    (temp/45)*0.3 +
    (humidity/100)*0.2 +
    (wind/40)*0.2,
    1.0
) * 100

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📊 Metrics", "⚡ Risk"])

# ─────────────────────────────────────────────
# MAP
# ─────────────────────────────────────────────
with tab1:
    st.subheader("3D Risk Map")

    layer = pdk.Layer(
        "ColumnLayer",
        data=[{"lat": lat, "lon": lon, "risk": risk_score}],
        get_position=["lon", "lat"],
        get_elevation="risk * 100",
        radius=2000,
        get_fill_color=[255, 0, 0],
    )

    view = pdk.ViewState(latitude=lat, longitude=lon, zoom=10, pitch=40)

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view))

# ─────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────
with tab2:
    st.metric("Temperature", f"{temp} °C")
    st.metric("Humidity", f"{humidity}%")
    st.metric("Wind", f"{wind} km/h")
    st.metric("Pressure", f"{pressure} hPa")
    st.metric("AQI", aqi_score)

# ─────────────────────────────────────────────
# RISK
# ─────────────────────────────────────────────
with tab3:
    st.subheader("Risk Gauge")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        gauge={"axis": {"range": [0, 100]}}
    ))

    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
