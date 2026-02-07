import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from services.analytics.geospatial import analyze

st.set_page_config(page_title="RadioRCA | Manual Confirm", layout="wide")

# 1. Initialize Session State if empty
if 'lat' not in st.session_state:
    st.session_state.lat = 35.837097
if 'lon' not in st.session_state:
    st.session_state.lon = 10.624853

st.title("📡 RadioRCA: Location Confirmation")

# 2. Sidebar with Immediate Sync
with st.sidebar:
    st.header("📍 Current Target")
    # Link inputs to session state keys
    u_lat = st.number_input("Latitude", value=st.session_state.lat, format="%.6f", key="lat_input")
    u_lon = st.number_input("Longitude", value=st.session_state.lon, format="%.6f", key="lon_input")
    
    # Update state variables manually to ensure sync
    st.session_state.lat = u_lat
    st.session_state.lon = u_lon
    
    site_limit = st.slider("Nearby Sites", 1, 5, 1)
    st.divider()
    
    # Trigger for the RCA Engine
    run_btn = st.button("🚀 Confirm & Run Analysis", use_container_width=True)

# 3. Interactive Map (Selection Phase)
st.subheader("🌍 1. Click Map to Select Location")
m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=15)

# Show a marker where the user is currently pointing
folium.Marker(
    [st.session_state.lat, st.session_state.lon], 
    icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa')
).add_to(m)

# IMPORTANT: returned_objects=["last_clicked"] makes the component responsive
map_data = st_folium(m, width='stretch', height=450, returned_objects=["last_clicked"])

# 4. Immediate Sync Logic
if map_data and map_data.get("last_clicked"):
    click_lat = map_data["last_clicked"]["lat"]
    click_lon = map_data["last_clicked"]["lng"]
    
    # Detect if the click is different from current state
    if click_lat != st.session_state.lat or click_lon != st.session_state.lon:
        st.session_state.lat = click_lat
        st.session_state.lon = click_lon
        # This forces the sidebar to update instantly
        st.rerun()

# 5. Analysis Phase (Only runs on Button Press)
if run_btn:
    st.subheader("📊 2. RCA Diagnostic Results")
    ctx = {
        'latitude': st.session_state.lat, 
        'longitude': st.session_state.lon, 
        'site_limit': site_limit, 
        'is_web': True
    }
    
    results = analyze(ctx)
    
    if "cells" in results and results["cells"]:
        df_display = pd.DataFrame(results["cells"])
        
        # Color coding for better visibility
        def color_status(val):
            if "✅" in str(val): return 'background-color: #d4edda'
            if "❌" in str(val): return 'background-color: #f8d7da'
            return ''

        st.dataframe(
            df_display.style.map(color_status, subset=['h_status', 'v_status']),
            width='stretch'
        )
    else:
        st.warning("No cell data found. Check if database is loaded.")