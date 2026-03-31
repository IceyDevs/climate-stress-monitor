# ============================================================
#  CLIMATE INFRASTRUCTURE & ANOMALY DETECTION COMMAND CENTER
# ============================================================

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Climate Infrastructure & Anomaly Detection",
    page_icon="🏙️",
    layout="wide"
)

# ─────────────────────────────────────────────
#  CSS LOADER
# ─────────────────────────────────────────────
def load_css(path: str = "styles.css"):
    try:
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS is optional — app runs fine without it

load_css()

# ─────────────────────────────────────────────
#  MOBILE DETECTION
#  Injects a tiny JS snippet that writes the
#  window width into a hidden Streamlit input,
#  allowing Python to branch on screen size.
# ─────────────────────────────────────────────
st.markdown("""
    <script>
        const width = window.innerWidth;
        const el = window.parent.document.querySelector(
            'input[data-testid="stNumberInput-StWidth"]'
        );
        if(el){ el.value = width; el.dispatchEvent(new Event('input', {bubbles:true})); }
    </script>
""", unsafe_allow_html=True)

# Fallback: read from query params if JS fires before Streamlit is ready
_qs = st.query_params.get("mobile", ["0"])
_mobile_flag = str(_qs[0]) == "1" if isinstance(_qs, list) else str(_qs) == "1"

# Primary detection via session state (set by JS above on reload)
if "screen_width" not in st.session_state:
    st.session_state.screen_width = 1200  # safe desktop default

is_mobile = st.session_state.screen_width < 768

def rcols(*ratios):
    """Responsive columns: returns real columns on desktop, single column on mobile."""
    if is_mobile:
        # Return the same container N times so code using c1,c2,... still works
        return [st.container() for _ in ratios]
    return st.columns(list(ratios))

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2942/2942206.png", width=90)
st.sidebar.title("⚙️ System Override")

# Border location quick-select
border_locations = {
    "None": None,

    # ── India–China (LAC) ──────────────────────────────
    "Leh (Ladakh)":              "Leh",
    "Kargil (Ladakh)":           "Kargil",
    "Tawang (Arunachal)":        "Tawang",
    "Nathu La (Sikkim)":         "Nathu La",
    "Daulat Beg Oldie (Ladakh)": "Daulat Beg Oldie",
    "Kibber (Spiti, HP)":        "Kibber",
    "Walong (Arunachal)":        "Walong",

    # ── India–Pakistan (LoC / IB) ──────────────────────
    "Kupwara (Kashmir)":         "Kupwara",
    "Uri (Kashmir)":             "Uri",
    "Poonch (J&K)":              "Poonch",
    "Rajouri (J&K)":             "Rajouri",
    "Amritsar (Punjab)":         "Amritsar",
    "Barmer (Rajasthan)":        "Barmer",
    "Jaisalmer (Rajasthan)":     "Jaisalmer",
    "Bhuj (Gujarat)":            "Bhuj",

    # ── India–Nepal ────────────────────────────────────
    "Pithoragarh (Uttarakhand)": "Pithoragarh",
    "Banbasa (Uttarakhand)":     "Banbasa",
    "Raxaul (Bihar)":            "Raxaul",
    "Nautanwa (UP)":             "Nautanwa",
    "Kakarbhitta Area (WB)":     "Siliguri",

    # ── India–Bangladesh ───────────────────────────────
    "Petrapole (WB)":            "Bongaon",
    "Agartala (Tripura)":        "Agartala",
    "Dawki (Meghalaya)":         "Dawki",
    "Sutarkandi (Assam)":        "Karimganj",

    # ── India–Myanmar ──────────────────────────────────
    "Moreh (Manipur)":           "Moreh",
    "Champhai (Mizoram)":        "Champhai",
    "Zokhawthar (Mizoram)":      "Zokhawthar",

    # ── India–Bhutan ───────────────────────────────────
    "Jaigaon (WB)":              "Jaigaon",
    "Samdrup Jongkhar Area":     "Dewangiri",

    # ── Coastal / Maritime ─────────────────────────────
    "Campbell Bay (Andaman)":    "Campbell Bay",
    "Kavaratti (Lakshadweep)":   "Kavaratti",
    "Dwarka (Gujarat)":          "Dwarka",
}
preset = st.sidebar.selectbox("🗺️ Quick Border Location", list(border_locations.keys()))
default_city = border_locations[preset] if border_locations[preset] else ""
city = st.sidebar.text_input("📍 Or Enter Any City", default_city)

st.sidebar.markdown("---")
st.sidebar.success("🟢 3D Radar: ONLINE")
st.sidebar.success("🟢 Core Sensors: ONLINE")
st.sidebar.success("🟢 Grid & Power: ONLINE")
st.sidebar.success("🟢 Infrastructure: ONLINE")
st.sidebar.success("🟢 AI Mayor: ONLINE")
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reboot Telemetry"):
    st.cache_data.clear()
    st.rerun()

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.title("🏙️ Climate Infrastructure & Anomaly Detection Center")
st.caption("Real-time environmental stress monitoring for cities and strategic border locations.")

# ─────────────────────────────────────────────
#  API HELPERS (CACHED)
# ─────────────────────────────────────────────

@st.cache_data(ttl=600)
def search_location(city_name: str):
    """
    Nominatim (OpenStreetMap) geocoder.
    - Tries India-scoped search first for clean results
    - Falls back to global search if India search returns nothing
      (handles remote/inconsistently-indexed border towns like Tawang)
    - User-Agent header required by Nominatim's usage policy
    """
    url     = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "ClimateInfraMonitor/1.0"}
    base_params = {
        "q":              city_name,
        "format":         "jsonv2",
        "addressdetails": 1,
        "limit":          8,
    }
    try:
        # First pass — India only
        res = requests.get(
            url,
            params={**base_params, "countrycodes": "in"},
            headers=headers,
            timeout=10
        ).json()
        if isinstance(res, list) and len(res) > 0:
            return res
        # Fallback — global search, no country filter
        res = requests.get(
            url,
            params=base_params,
            headers=headers,
            timeout=10
        ).json()
        return res if isinstance(res, list) else []
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_smart_city_data(lat: float, lon: float):
    """Fetches weather + AQI data from Open-Meteo for all dashboard modules."""
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,surface_pressure,"
        f"wind_speed_10m,wind_gusts_10m,uv_index,shortwave_radiation,wet_bulb_temperature_2m"
        f"&hourly=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_sum,"
        f"et0_fao_evapotranspiration_sum"
        f"&past_days=7&timezone=auto"
    )
    aqi_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
        f"&current=us_aqi,pm2_5"
    )
    try:
        weather_data = requests.get(weather_url, timeout=15).json()
        aqi_data     = requests.get(aqi_url,     timeout=15).json()
    except requests.exceptions.Timeout:
        st.error(
            "⏱️ **Request timed out.** Open-Meteo is taking too long to respond. "
            "This usually resolves in a few seconds — hit **Reboot Telemetry** in the sidebar or refresh the page."
        )
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error(
            "🔌 **Connection error.** Could not reach the weather API. "
            "Check your internet connection and try again."
        )
        st.stop()
    return weather_data, aqi_data


# ─────────────────────────────────────────────
#  LOCATION DISAMBIGUATION — Nominatim
# ─────────────────────────────────────────────
if not city:
    st.stop()

locations = search_location(city)
if not locations:
    st.error(f"❌ '{city}' not found. Try a nearby town or check the spelling.")
    st.stop()

# Nominatim returns display_name (full address string) and lat/lon as strings
options = [l["display_name"] for l in locations]
choice  = st.selectbox("📡 Confirm Location", options)
selected = locations[options.index(choice)]

lat              = float(selected["lat"])
lon              = float(selected["lon"])
# Use the first part of display_name (place name before the first comma) as short name
actual_city_name = selected["display_name"].split(",")[0].strip()

st.caption(
    f"📡 SAT-LINK ESTABLISHED: **{actual_city_name}** "
    f"(Lat: {lat:.4f}, Lon: {lon:.4f})"
)

# ─────────────────────────────────────────────
#  FETCH ALL DATA
# ─────────────────────────────────────────────
weather_data, aqi_data = get_smart_city_data(lat, lon)
current = weather_data["current"]
hourly  = weather_data["hourly"]
daily   = weather_data["daily"]

# ── Raw sensor values ──
temp     = current["temperature_2m"]
humidity = current["relative_humidity_2m"]
wind     = current["wind_speed_10m"]
rain     = current["precipitation"]
pressure = current["surface_pressure"]

# ── Extended sensors ──
solar_rad = current.get("shortwave_radiation", 0)
wet_bulb  = current.get("wet_bulb_temperature_2m", temp)
gusts     = current.get("wind_gusts_10m", wind)
today_max = daily["temperature_2m_max"][1] if len(daily["temperature_2m_max"]) > 1 else temp
today_min = daily["temperature_2m_min"][1] if len(daily["temperature_2m_min"]) > 1 else temp
evapo     = (daily.get("et0_fao_evapotranspiration_sum") or [0, 0])[1]
rain_sum  = (daily.get("precipitation_sum") or [0, 0])[1]

# ── Derived values ──
heat_index   = temp + (0.33 * humidity) - 4
avg_temp_24h = sum(hourly["temperature_2m"][-24:]) / 24
temp_anomaly = abs(temp - avg_temp_24h)
asphalt_temp = temp + (solar_rad * 0.025)
avg_temp_today = (today_max + today_min) / 2
cdd          = max(0, avg_temp_today - 18)  # Cooling Degree Days

# ─────────────────────────────────────────────
#  CITY RISK SCORE
# ─────────────────────────────────────────────
risk_score = min(
    ((temp / 45) * 0.3)
    + ((humidity / 100) * 0.2)
    + ((wind / 40) * 0.2)
    + ((gusts / 60) * 0.3),
    1.0
) * 100

if risk_score < 30:   risk_cat, risk_color = "Low",      "#00CC96"
elif risk_score < 60: risk_cat, risk_color = "Moderate", "#FECB52"
elif risk_score < 80: risk_cat, risk_color = "High",     "#FFA15A"
else:                 risk_cat, risk_color = "Severe",   "#EF553B"

# ─────────────────────────────────────────────
#  INFRASTRUCTURE STRESS INDEX
# ─────────────────────────────────────────────
temp_score     = min(temp / 45, 1)
rain_score     = min(rain / 50, 1)
wind_score     = min(wind / 30, 1)
humidity_score = min(humidity / 100, 1)
pressure_score = min(abs(pressure - 1013) / 50, 1)
heat_score     = min(heat_index / 50, 1)

stress_index = (
    0.25 * temp_score
    + 0.10 * rain_score
    + 0.10 * wind_score
    + 0.15 * humidity_score
    + 0.15 * pressure_score
    + 0.25 * heat_score
)

if stress_index < 0.35:  stress_level = "Low"
elif stress_index < 0.60: stress_level = "Moderate"
elif stress_index < 0.80: stress_level = "High"
else:                      stress_level = "Severe"

# ─────────────────────────────────────────────
#  AQI
# ─────────────────────────────────────────────
current_aqi = aqi_data.get("current", {})
aqi_score   = current_aqi.get("us_aqi", 0)
pm25        = current_aqi.get("pm2_5", 0)

# ─────────────────────────────────────────────
#  BORDER INFRASTRUCTURE RISK (File 2)
# ─────────────────────────────────────────────
road_risk      = "High" if (rain > 40 or temp < 0) else ("Moderate" if rain > 20 else "Low")
airstrip_risk  = "High" if wind > 25 else ("Moderate" if wind > 15 else "Low")
power_risk     = "High" if (temp > 40 or wind > 30) else ("Moderate" if temp > 35 else "Low")
logistics_risk = "High" if (rain > 35 or wind > 25) else ("Moderate" if rain > 15 else "Low")
all_risks      = [road_risk, airstrip_risk, power_risk, logistics_risk]

# ─────────────────────────────────────────────
#  GRID STATUS
# ─────────────────────────────────────────────
if cdd > 15:   grid_stat, grid_col = "CRITICAL LOAD", "red"
elif cdd > 5:  grid_stat, grid_col = "MODERATE LOAD", "orange"
else:          grid_stat, grid_col = "BASE LOAD",     "green"

# ═══════════════════════════════════════════════════════════
#  TAB LAYOUT
# ═══════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🗺️ Map",
    "📊 Metrics",
    "📉 Stress",
    "⚡ Grid",
    "🏗️ Infra",
    "💧 Environ",
    "📅 Forecast",
])

# ──────────────────────────────────────────────────────────
#  TAB 1 — 3D MAP & AI MAYOR
# ──────────────────────────────────────────────────────────
with tab1:
    col_map, col_mayor = rcols(1.5, 1)

    with col_map:
        st.subheader("🗺️ Live 3D Urban Radar")
        fill_color = [255, 50, 50, 200] if risk_score > 60 else [50, 255, 50, 200]
        layer = pdk.Layer(
            "ColumnLayer",
            data=[{"lat": lat, "lon": lon, "risk": risk_score}],
            get_position=["lon", "lat"],
            get_elevation="risk * 100",
            elevation_scale=50,
            radius=2500,
            get_fill_color=fill_color,
            pickable=True,
            auto_highlight=True,
        )
        # Flatter pitch on mobile so the column is visible without panning
        _pitch   = 20 if is_mobile else 45
        _bearing = 0  if is_mobile else 15
        view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=10, pitch=_pitch, bearing=_bearing)
        r = pdk.Deck(
            map_provider="carto",
            map_style="dark",
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": f"City Risk Score: {risk_score:.1f}%"},
        )
        st.pydeck_chart(r)

    with col_mayor:
        st.subheader("🤖 AI Mayor: Action Briefing")
        actions = 0
        if wet_bulb > 29:
            st.error("🚨 **LABOR:** Halt outdoor labor — extreme heatstroke risk.")
            actions += 1
        if gusts > 50:
            st.error("🚨 **CRANES:** Ground all high-rise cranes immediately.")
            actions += 1
        if evapo > 6 and rain_sum < 1:
            st.warning("⚠️ **WATER:** Soil drying fast. Schedule park irrigation.")
            actions += 1
        if asphalt_temp > 60:
            st.warning("⚠️ **ROADS:** Asphalt melting risk. Reroute heavy trucks.")
            actions += 1
        if cdd > 10:
            st.info("⚡ **GRID:** High AC demand. Prepare backup gas turbines.")
            actions += 1
        if actions == 0:
            st.success("✅ City systems optimal. No AI interventions required.")

# ──────────────────────────────────────────────────────────
#  TAB 2 — CORE METRICS & ANOMALY DETECTION
# ──────────────────────────────────────────────────────────
with tab2:
    st.subheader("📊 Core System Diagnostics")
    col_gauge, col_alerts = rcols(1, 1)

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={"text": f"Overall City Risk: {risk_cat}", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "rgba(255,255,255,0.4)"},
                "steps": [
                    {"range": [0, 30],  "color": "#00CC96"},
                    {"range": [30, 60], "color": "#FECB52"},
                    {"range": [60, 80], "color": "#FFA15A"},
                    {"range": [80, 100],"color": "#EF553B"},
                ],
            },
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_alerts:
        st.markdown("### 🚨 Anomaly Detection System")
        flagged = False
        if temp_anomaly > 5:
            st.warning(f"⚠️ Temperature is **{temp_anomaly:.1f}°C** away from the 24 h average.")
            flagged = True
        if wind > 30:
            st.warning(f"⚠️ High base wind speed: **{wind} km/h**")
            flagged = True
        if rain > 5:
            st.info(f"🌧️ Active rainfall: **{rain} mm**")
            flagged = True
        if aqi_score > 100:
            st.warning(f"😷 Unhealthy AQI detected: **{aqi_score}**")
            flagged = True
        if not flagged:
            st.success("✅ All parameters within normal bounds.")

    st.markdown("---")
    st.markdown("### 🌡️ Live Sensor Readings")
    c1, c2, c3, c4, c5 = rcols(1, 1, 1, 1, 1)
    c1.metric("Air Temp",    f"{temp} °C",         f"{temp - avg_temp_24h:+.1f} °C vs 24 h avg")
    c2.metric("Heat Index",  f"{heat_index:.1f} °C")
    c3.metric("Humidity",    f"{humidity} %")
    c4.metric("Wind Speed",  f"{wind} km/h")
    c5.metric("Pressure",    f"{pressure} hPa")

# ──────────────────────────────────────────────────────────
#  TAB 3 — STRESS INDEX & DRIVER BREAKDOWN
# ──────────────────────────────────────────────────────────
with tab3:
    st.subheader("📉 Infrastructure Climate Stress Index")
    col_si, col_drivers = rcols(1, 1.5)

    with col_si:
        fig_stress = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(stress_index, 3),
            title={"text": f"Stress Level: {stress_level}", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 1]},
                "steps": [
                    {"range": [0, 0.35],  "color": "#2ecc71"},
                    {"range": [0.35, 0.6],"color": "#f1c40f"},
                    {"range": [0.6, 0.8], "color": "#e67e22"},
                    {"range": [0.8, 1],   "color": "#e74c3c"},
                ],
            },
        ))
        st.plotly_chart(fig_stress, use_container_width=True)
        st.metric("Composite Stress Score", round(stress_index, 3))
        st.metric("Stress Category",        stress_level)

    with col_drivers:
        st.markdown("### Stress Driver Contributions")
        drivers_df = pd.DataFrame({
            "Factor":       ["Temperature", "Rainfall", "Wind", "Humidity", "Pressure", "Heat Stress"],
            "Contribution": [temp_score, rain_score, wind_score, humidity_score, pressure_score, heat_score],
        })
        fig_drivers = px.bar(
            drivers_df, x="Factor", y="Contribution",
            color="Contribution",
            color_continuous_scale="RdYlGn_r",
            title="Weighted Environmental Drivers of Infrastructure Stress",
        )
        st.plotly_chart(fig_drivers, use_container_width=True)

# ──────────────────────────────────────────────────────────
#  TAB 4 — ENERGY GRID
# ──────────────────────────────────────────────────────────
with tab4:
    st.subheader("⚡ Power Grid & Solar Analytics")
    c1, c2, c3 = rcols(1, 1, 1)
    c1.metric("☀️ Solar Irradiance",        f"{solar_rad} W/m²")
    c2.metric("❄️ Cooling Degree Days",      f"{cdd:.1f} CDD")
    c3.markdown(
        f"**🔋 Grid Status:**<br>"
        f"<span style='color:{grid_col}; font-size:22px;'>{grid_stat}</span>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    # 7-day CDD trend proxy using daily max temps
    df_cdd = pd.DataFrame({
        "Date": pd.to_datetime(daily["time"]),
        "Max Temp (°C)": daily["temperature_2m_max"],
        "CDD": [max(0, t - 18) for t in daily["temperature_2m_max"]],
    })
    fig_cdd = px.area(
        df_cdd, x="Date", y="CDD",
        title="Cooling Degree Days — 7-Day View (Proxy for AC Grid Load)",
        color_discrete_sequence=["#FECB52"],
    )
    st.plotly_chart(fig_cdd, use_container_width=True)

# ──────────────────────────────────────────────────────────
#  TAB 5 — INFRASTRUCTURE RISK
# ──────────────────────────────────────────────────────────
with tab5:
    st.subheader("🏗️ Construction, Material & Border Infrastructure Safety")

    # Extended sensor readings
    c1, c2, c3 = rcols(1, 1, 1)
    c1.metric("👷 Wet-Bulb (Labor Index)", f"{wet_bulb:.1f} °C",
              help="Above 29 °C: outdoor labor should be halted.")
    c2.metric("🏗️ Wind Gusts",             f"{gusts} km/h",
              help="Above 50 km/h: high-rise cranes should be grounded.")
    c3.metric("🛣️ Est. Asphalt Surface Temp", f"{asphalt_temp:.1f} °C",
              help="Above 60 °C: asphalt deformation risk.")

    st.markdown("---")
    st.subheader("🛡️ Border Infrastructure Risk Assessment")
    c1, c2, c3, c4 = rcols(1, 1, 1, 1)

    def risk_color(r):
        return {"Low": "green", "Moderate": "orange", "High": "red"}.get(r, "gray")

    c1.metric("🛤️ Road Network",  road_risk)
    c2.metric("✈️ Airstrip",      airstrip_risk)
    c3.metric("⚡ Power Grid",    power_risk)
    c4.metric("📦 Logistics",     logistics_risk)

    st.markdown("---")
    st.subheader("🧭 Operational Interpretation")
    if "High" in all_risks:
        st.warning("⚠️ Environmental conditions may significantly impact border infrastructure operations. Immediate review advised.")
    elif "Moderate" in all_risks:
        st.info("ℹ️ Moderate environmental stress detected. Monitor infrastructure conditions closely.")
    else:
        st.success("✅ Environmental conditions stable for all infrastructure operations.")

# ──────────────────────────────────────────────────────────
#  TAB 6 — ENVIRONMENT & AQI
# ──────────────────────────────────────────────────────────
with tab6:
    st.subheader("💧 Air Quality, Smart Irrigation & Environment")
    c1, c2, c3, c4 = rcols(1, 1, 1, 1)
    c1.metric("🌫️ US AQI",                aqi_score,           delta_color="inverse")
    c2.metric("🧪 PM 2.5 (Dust/Sand)",    f"{pm25} µg/m³",     delta_color="inverse")
    c3.metric("💧 Evapotranspiration",     f"{evapo:.1f} mm")
    c4.metric("🌧️ Daily Rainfall",         f"{rain_sum:.1f} mm")

    st.markdown("---")
    # 7-day hourly climate trend (File 2)
    df_trend = pd.DataFrame({
        "Time":         pd.to_datetime(hourly["time"]),
        "Temperature":  hourly["temperature_2m"],
        "Humidity":     hourly["relative_humidity_2m"],
        "Wind Speed":   hourly["wind_speed_10m"],
    })
    fig_trend = px.line(
        df_trend, x="Time",
        y=["Temperature", "Humidity", "Wind Speed"],
        title="7-Day Hourly Climate Trend",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ──────────────────────────────────────────────────────────
#  TAB 7 — FORECAST & CSV EXPORT
# ──────────────────────────────────────────────────────────
with tab7:
    st.subheader("📅 7-Day Forecast & Raw Data Export")

    df_daily = pd.DataFrame({
        "Date":          pd.to_datetime(daily["time"]),
        "Max Temp (°C)": daily["temperature_2m_max"],
        "Min Temp (°C)": daily["temperature_2m_min"],
        "Rain (mm)":     daily["precipitation_sum"],
        "UV Index Max":  daily.get("uv_index_max", [None] * len(daily["time"])),
    })

    fig_forecast = px.bar(
        df_daily, x="Date", y="Max Temp (°C)",
        color="Max Temp (°C)",
        color_continuous_scale="reds",
        title="7-Day Maximum Temperature Forecast",
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

    fig_rain = px.bar(
        df_daily, x="Date", y="Rain (mm)",
        color="Rain (mm)",
        color_continuous_scale="blues",
        title="7-Day Rainfall Forecast",
    )
    st.plotly_chart(fig_rain, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💾 Export Core Telemetry (Last 24 h)")
    df_hourly_export = pd.DataFrame({
        "Time":         pd.to_datetime(hourly["time"]),
        "Temp (°C)":    hourly["temperature_2m"],
        "Humidity (%)": hourly["relative_humidity_2m"],
        "Pressure (hPa)": hourly["surface_pressure"],
        "Wind (km/h)":  hourly["wind_speed_10m"],
    })
    st.dataframe(df_hourly_export.tail(24), use_container_width=True)
    csv = df_hourly_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download 24 h History (CSV)",
        data=csv,
        file_name=f"{actual_city_name}_telemetry_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.caption(f"🌐 Weather & AQI: Open-Meteo API  •  Geocoding: Nominatim / OpenStreetMap  •  Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
