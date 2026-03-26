# 🏙️ Climate Infrastructure & Anomaly Detection Center

A real-time environmental monitoring dashboard for Indian border regions and cities. Tracks climate stress conditions, infrastructure risk, air quality, energy grid load, and weather anomalies — all from a single interface with no API keys required.

---

## 📸 Features

### 🗺️ Tab 1 — 3D Map & AI Mayor
- Live 3D urban radar (pydeck) — column height and colour encode city risk score
- AI Mayor action briefing — translates sensor thresholds into plain operational decisions (labor halts, crane groundings, irrigation scheduling, grid standby)

### 📊 Tab 2 — Core Metrics & Anomaly Detection
- City risk gauge (0–100%) aggregating temperature, humidity, wind, and gusts
- Anomaly detection comparing current readings against the 24-hour rolling average
- Live sensor panel: air temp, heat index, humidity, wind speed, pressure

### 📉 Tab 3 — Infrastructure Stress Index
- Composite stress score (0–1) using a 6-factor normalized weighted formula
- Stress driver breakdown bar chart showing which environmental factor is the root cause

### ⚡ Tab 4 — Energy Grid
- Solar irradiance tracking
- Cooling Degree Days (CDD) — proxy for AC grid load
- 7-day CDD area chart for sustained load forecasting
- Grid status: Base / Moderate / Critical

### 🏗️ Tab 5 — Infrastructure Risk
- Wet-bulb temperature (labor safety, threshold: 29 °C)
- Wind gust tracking (crane safety, threshold: 50 km/h)
- Estimated asphalt surface temperature (road deformation, threshold: 60 °C)
- Border infrastructure risk grid: Roads, Airstrip, Power Grid, Logistics
- Operational interpretation advisory

### 💧 Tab 6 — Environment & AQI
- US AQI + PM2.5 (fine particulate / sandstorm tracking)
- Evapotranspiration (soil subsidence risk indicator)
- 7-day hourly trend lines: temperature, humidity, wind speed

### 📅 Tab 7 — Forecast & Export
- 7-day max temperature and rainfall forecast charts
- Last 24-hour raw telemetry table
- CSV export with auto-stamped filename

---

## 🗺️ Border Location Quick-Select

35 pre-loaded Indian border locations across 8 categories:

| Border | Locations |
|--------|-----------|
| India–China (LAC) | Leh, Kargil, Tawang, Nathu La, Daulat Beg Oldie, Kibber, Walong |
| India–Pakistan (LoC/IB) | Kupwara, Uri, Poonch, Rajouri, Amritsar, Barmer, Jaisalmer, Bhuj |
| India–Nepal | Pithoragarh, Banbasa, Raxaul, Nautanwa, Siliguri |
| India–Bangladesh | Bongaon, Agartala, Dawki, Karimganj |
| India–Myanmar | Moreh, Champhai, Zokhawthar |
| India–Bhutan | Jaigaon, Dewangiri |
| Coastal / Maritime | Campbell Bay, Kavaratti, Dwarka |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Charts | Plotly (Express + Graph Objects) |
| 3D Map | pydeck |
| Geocoding | Nominatim / OpenStreetMap |
| Weather & AQI | Open-Meteo API |
| Language | Python 3.9+ |

---

## 📁 Project Structure

```
.
├── app.py              # Main Streamlit application
├── styles.css          # Dashboard theme (Orbitron + Inter, cyan dark mode)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## 🚀 Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Deploy — no environment variables or API keys needed

---

## 📡 Data Sources

| Data | Provider | API Key Required |
|------|----------|-----------------|
| Weather & forecast | [Open-Meteo](https://open-meteo.com/) | ❌ No |
| Air quality / AQI | [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api) | ❌ No |
| Geocoding | [Nominatim / OpenStreetMap](https://nominatim.openstreetmap.org/) | ❌ No |

---

## 📝 Notes

- All API responses are cached for 10 minutes (`@st.cache_data(ttl=600)`) to avoid redundant requests
- Geocoding is restricted to India (`countrycodes=in`) — remove that parameter in `search_location()` to enable global search
- The app is mobile-responsive: columns stack vertically on screens under 768px
- If Open-Meteo times out (can happen for very remote coordinates), use the **Reboot Telemetry** button in the sidebar to retry
