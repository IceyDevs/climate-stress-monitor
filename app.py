import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Climate Stress Infrastructure Monitor", layout="wide")

# ---------- LOAD CSS ----------

def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ---------- HEADER ----------

st.markdown('<div class="title">Border Infrastructure Climate Stress Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Environmental Stress Monitoring for Strategic Locations</div>', unsafe_allow_html=True)

# ---------- REFRESH ----------

if st.button("Refresh Data"):
    st.rerun()

# ---------- BORDER TOWN QUICK SELECT ----------

border_locations = {
    "Leh (Ladakh)": "Leh",
    "Tawang (Arunachal)": "Tawang",
    "Kargil (Ladakh)": "Kargil",
    "Kupwara (Kashmir)": "Kupwara",
    "Nathu La (Sikkim)": "Nathu La"
}

preset = st.selectbox("Quick Border Location", ["None"] + list(border_locations.keys()))

if preset != "None":
    city = border_locations[preset]
else:
    city = st.text_input("Enter City / Region")

if not city:
    st.stop()

# ---------- HEAT INDEX ----------

def heat_index(temp, humidity):
    return temp + (0.33 * humidity) - 4

# ---------- GEO SEARCH ----------

@st.cache_data(ttl=600)
def search_location(city):

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    res = requests.get(url).json()

    if "results" in res:
        return res["results"]

    return None

locations = search_location(city)

if not locations:
    st.error("Location not found")
    st.stop()

options = [
    f"{l['name']}, {l.get('admin1','')}, {l['country']}"
    for l in locations
]

choice = st.selectbox("Select Correct Location", options)

selected = locations[options.index(choice)]

lat = selected["latitude"]
lon = selected["longitude"]

# ---------- WEATHER DATA ----------

@st.cache_data(ttl=600)
def weather(lat, lon):

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,"
        f"precipitation,wind_speed_10m,surface_pressure"
        f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
        f"&past_days=7"
    )

    return requests.get(url).json()

data = weather(lat, lon)

current = data["current"]

temp = current["temperature_2m"]
humidity = current["relative_humidity_2m"]
wind = current["wind_speed_10m"]
rain = current["precipitation"]
pressure = current["surface_pressure"]

hi = heat_index(temp, humidity)

# ---------- NORMALIZATION ----------

temp_score = min(temp/45,1)
rain_score = min(rain/50,1)
wind_score = min(wind/30,1)
humidity_score = min(humidity/100,1)
pressure_score = min(abs(pressure-1013)/50,1)
heat_score = min(hi/50,1)

stress_index = (
0.25*temp_score +
0.10*rain_score +
0.10*wind_score +
0.15*humidity_score +
0.15*pressure_score +
0.25*heat_score
)

# ---------- STRESS LEVEL ----------

if stress_index < .35:
    level="Low"
elif stress_index < .6:
    level="Moderate"
elif stress_index < .8:
    level="High"
else:
    level="Severe"

# ---------- MAIN LAYOUT ----------

left, right = st.columns([1,2])

# ---------- LEFT PANEL ----------

with left:

    st.subheader("Environmental Drivers")

    st.metric("Temperature (°C)", temp)
    st.metric("Humidity (%)", humidity)
    st.metric("Wind Speed (km/h)", wind)
    st.metric("Precipitation (mm)", rain)
    st.metric("Pressure (hPa)", pressure)
    st.metric("Heat Index", round(hi,2))

    st.subheader("Stress Level")

    st.metric("Climate Stress Index", round(stress_index,2))
    st.metric("Stress Category", level)

# ---------- RIGHT PANEL ----------

with right:

    st.subheader("Climate Stress Index")

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stress_index,
        title={'text':"Infrastructure Stress Index"},
        gauge={
            'axis':{'range':[0,1]},
            'steps':[
                {'range':[0,.35],'color':'#2ecc71'},
                {'range':[.35,.6],'color':'#f1c40f'},
                {'range':[.6,.8],'color':'#e67e22'},
                {'range':[.8,1],'color':'#e74c3c'}
            ]
        }
    ))

    st.plotly_chart(gauge, use_container_width=True)

    # ---------- CLIMATE TREND ----------

    st.subheader("Climate Trend")

    hourly = data["hourly"]

    df = pd.DataFrame({
        "Time":pd.to_datetime(hourly["time"]),
        "Temperature":hourly["temperature_2m"],
        "Humidity":hourly["relative_humidity_2m"],
        "Wind":hourly["wind_speed_10m"]
    })

    trend = px.line(df, x="Time", y=["Temperature","Humidity","Wind"])

    st.plotly_chart(trend, use_container_width=True)

# ---------- STRESS DRIVER BREAKDOWN ----------

st.subheader("Stress Driver Contribution")

drivers = pd.DataFrame({
    "Factor":[
        "Temperature",
        "Rainfall",
        "Wind",
        "Humidity",
        "Pressure",
        "Heat Stress"
    ],
    "Contribution":[
        temp_score,
        rain_score,
        wind_score,
        humidity_score,
        pressure_score,
        heat_score
    ]
})

driver_chart = px.bar(
    drivers,
    x="Factor",
    y="Contribution",
    title="Environmental Drivers of Infrastructure Stress"
)

st.plotly_chart(driver_chart,use_container_width=True)

# ---------- MAP ----------

st.subheader("Monitoring Location")

map_df = pd.DataFrame({"lat":[lat],"lon":[lon]})

st.map(map_df)

# ---------- BORDER INFRASTRUCTURE RISK ----------

st.divider()
st.subheader("Border Infrastructure Risk Assessment")

road_risk = "Low"
airstrip_risk = "Low"
power_risk = "Low"
logistics_risk = "Low"

if rain > 40 or temp < 0:
    road_risk = "High"
elif rain > 20:
    road_risk = "Moderate"

if wind > 25:
    airstrip_risk = "High"
elif wind > 15:
    airstrip_risk = "Moderate"

if temp > 40 or wind > 30:
    power_risk = "High"
elif temp > 35:
    power_risk = "Moderate"

if rain > 35 or wind > 25:
    logistics_risk = "High"
elif rain > 15:
    logistics_risk = "Moderate"

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.metric("Road Network Risk", road_risk)

with c2:
    st.metric("Airstrip Risk", airstrip_risk)

with c3:
    st.metric("Power Grid Risk", power_risk)

with c4:
    st.metric("Logistics Risk", logistics_risk)

st.subheader("Operational Interpretation")

if "High" in [road_risk,airstrip_risk,power_risk,logistics_risk]:
    st.warning("Environmental conditions may impact border infrastructure operations.")

elif "Moderate" in [road_risk,airstrip_risk,power_risk,logistics_risk]:
    st.info("Moderate environmental stress detected. Monitor infrastructure conditions.")

else:
    st.success("Environmental conditions stable for infrastructure operations.")

# ---------- FOOTER ----------

st.markdown("---")

st.caption("Climate Stress Infrastructure Monitoring System")

st.caption("Data Source: Open-Meteo Weather API")

st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")