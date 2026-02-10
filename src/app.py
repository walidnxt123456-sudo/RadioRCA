"""
RadioRCA - Manual Confirmation Interface
Interactive geospatial analysis tool for radio network troubleshooting
"""
import math
import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from services.analytics.geospatial import analyze
from collections import deque
from infrastructure.logger import log, LOG_FILE


# ----------------------------------
# CONSTANTS
# ----------------------------------
DEFAULT_LAT = 35.837097
DEFAULT_LON = 10.624853
DEFAULT_ZOOM = 15
VALID_LAT_RANGE = (-90, 90)
VALID_LON_RANGE = (-180, 180)

def add_map_legend(m):
    """Adds a visual legend to the Folium map using HTML/CSS."""
    legend_html = '''
     <div style="
     position: fixed; 
     bottom: 50px; left: 50px; width: 160px; height: 120px; 
     background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
     padding: 10px;
     border-radius: 5px;
     box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
     ">
     <b>Legend</b><br>
     <i style="background: rgba(65, 105, 225, 0.3); border: 1px solid royalblue; width: 12px; height: 12px; display: inline-block;"></i> Ant. Sector (60°)<br>
     <i style="background: #28a745; width: 20px; height: 3px; display: inline-block; margin-bottom: 3px;"></i> Direct Path (✅)<br>
     <i style="background: #dc3545; width: 20px; height: 3px; display: inline-block; margin-bottom: 3px;"></i> Side/Back Path (❌)<br>
     <i style="background: white; border: 2px solid black; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Cell Site
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
def get_wedge_points(center_lat, center_lon, azimuth, distance_km=0.3, beamwidth=60):
    """Calculates coordinates for the sector wedge polygon."""
    points = [[center_lat, center_lon]]
    start_angle = azimuth - (beamwidth / 2)
    end_angle = azimuth + (beamwidth / 2)
    
    # Create smooth arc
    for angle in range(int(start_angle), int(end_angle) + 5, 5):
        rad = math.radians(angle)
        # Approximate meters to lat/lon degrees
        lat = center_lat + (distance_km / 111.32) * math.cos(rad)
        lon = center_lon + (distance_km / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(rad)
        points.append([lat, lon])
        
    points.append([center_lat, center_lon])
    return points

#displays the last 20 lines of the log file
def get_last_logs(filename=LOG_FILE, n=20):
    """Efficiently read the last N lines of the log file."""
    if not os.path.exists(filename):
        return [f"Log file not found: {filename}"]
    try:
        with open(filename, "r") as f:
            # deque with maxlen=n automatically keeps only the last n elements
            return list(deque(f, n))
    except Exception as e:
        return [f"Error reading logs: {str(e)}"]

# ----------------------------------
# HELPER FUNCTIONS
# ----------------------------------
def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude ranges."""
    if not (VALID_LAT_RANGE[0] <= lat <= VALID_LAT_RANGE[1]):
        return False
    if not (VALID_LON_RANGE[0] <= lon <= VALID_LON_RANGE[1]):
        return False
    return True

def update_coordinates(lat: float, lon: float) -> None:
    """Update session state coordinates with validation."""
    log.debug(f"Attempting coordinate update: {lat}, {lon}")
    if validate_coordinates(lat, lon):
        st.session_state.lat = lat
        st.session_state.lon = lon
        log.info(f"Target synchronized to: {lat:.6f}, {lon:.6f}")
    else:
        log.error(f"Validation failed for Lat: {lat}, Lon: {lon}")
        st.error(f"Invalid coordinates: Lat({lat}), Lon({lon})")

def create_map(lat: float, lon: float, zoom: int = DEFAULT_ZOOM) -> folium.Map:
    """Create a Folium map with marker at specified coordinates."""
    m = folium.Map(location=[lat, lon], zoom_start=zoom)
    
    folium.Marker(
        [lat, lon],
        icon=folium.Icon(color='blue', icon='crosshairs', prefix='fa'),
        tooltip=f"Target Location: {lat:.6f}, {lon:.6f}"
    ).add_to(m)
    
    return m

def color_status(val: str) -> str:
    """Apply color coding based on status values."""
    val_str = str(val)
    if "✅" in val_str:
        return 'background-color: #d4edda; color: #155724'  # Green for success
    elif "❌" in val_str:
        return 'background-color: #f8d7da; color: #721c24'  # Red for failure
    elif "⚠️" in val_str:
        return 'background-color: #fff3cd; color: #856404'  # Yellow for warning
    return ''

def analyze_location(lat: float, lon: float, site_limit: int) -> dict:
    """Wrapper function for location analysis."""
    log.debug(f"🚀 Starting RCA Engine | Lat: {lat}, Lon: {lon}, Limit: {site_limit}")
    ctx = {
        'latitude': lat,
        'longitude': lon,
        'site_limit': site_limit,
        'is_web': True
    }
    results = analyze(ctx)
    log.debug(f"Engine returned {len(results.get('cells', []))} cells for analysis.")
    return results


def get_wedge_tip(center_lat, center_lon, azimuth, distance_km=0.3):
    """Calculates the center-point of the wedge arc (the tip)."""
    rad = math.radians(azimuth)
    # Convert km to lat/lon degrees
    lat_tip = center_lat + (distance_km / 111.32) * math.cos(rad)
    lon_tip = center_lon + (distance_km / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(rad)
    return [lat_tip, lon_tip]
  
# ----------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------
def init_session_state():
    """Initialize all session state variables."""
    if 'lat' not in st.session_state:
        st.session_state.lat = DEFAULT_LAT
    if 'lon' not in st.session_state:
        st.session_state.lon = DEFAULT_LON
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'map_key' not in st.session_state:
        st.session_state.map_key = 0  # For forcing map rerenders
  
# ----------------------------------
# UI COMPONENTS
# ----------------------------------
def render_sidebar():
    """Render the sidebar controls."""
    with st.sidebar:
        st.header("📍 Current Target")
        
        # Current coordinates display
        st.metric("Latitude", f"{st.session_state.lat:.6f}")
        st.metric("Longitude", f"{st.session_state.lon:.6f}")
        
        st.divider()
        
        # Coordinate inputs
        st.subheader("Manual Adjustment")
        col1, col2 = st.columns(2)
        with col1:
            new_lat = st.number_input(
                "Latitude",
                value=st.session_state.lat,
                format="%.6f",
                key="lat_input",
                help="Enter latitude between -90 and 90"
            )
        with col2:
            new_lon = st.number_input(
                "Longitude",
                value=st.session_state.lon,
                format="%.6f",
                key="lon_input",
                help="Enter longitude between -180 and 180"
            )
        
        # Update button for manual input
        if st.button("Update Coordinates", width='stretch'):
            update_coordinates(new_lat, new_lon)
            st.session_state.map_key += 1  # Force map refresh
            st.rerun()
        
        st.divider()
        
        # Analysis settings
        st.subheader("Analysis Settings")
        site_limit = st.slider(
            "Nearby Sites to Analyze",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of nearest sites to include in analysis"
        )
        
        st.divider()
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            analyze_btn = st.button(
                "🚀 Run Analysis",
                width='stretch',
                type="primary",
                help="Analyze selected location"
            )
        with col2:
            if st.button("🔄 Reset", width='stretch'):
                st.session_state.lat = DEFAULT_LAT
                st.session_state.lon = DEFAULT_LON
                st.session_state.analysis_results = None
                st.session_state.map_key += 1
                st.rerun()
        
        st.divider()
        
        # FUTURE: if st.session_state.get("is_admin"):
        with st.sidebar.expander("🛠️ Admin / Debug Tools"):
            st.info("Log Viewer (Last 20 lines)")
            if st.button("📋 Refresh Logs", width='stretch'):
                # This triggers a rerun, and the logs will update below
                pass 
            
            logs = get_last_logs()
            # Join lines into a single string for the code block
            log_text = "".join(logs)
            st.code(log_text, language="log")        
        
        return site_limit, analyze_btn

def render_map():
    """Render the interactive map."""
    st.subheader("🌍 1. Click Map to Select Location")
    
    # Create map with current coordinates
    m = create_map(st.session_state.lat, st.session_state.lon)
    
    # DRAW SERVING PATHS
    if st.session_state.analysis_results and "cells" in st.session_state.analysis_results:
        for cell in st.session_state.analysis_results["cells"]:
            site_coords = [cell["site_lat"], cell["site_lon"]]
            user_coords = [st.session_state.lat, st.session_state.lon]
            azimuth = cell.get("azimuth")
            offset = cell.get("offset")
            
            # Define the Wedge Tip (where the line will now start)
            # We use the same distance as the wedge radius (e.g., 0.3km)
            if azimuth is not None:
                start_point = get_wedge_tip(cell["site_lat"], cell["site_lon"], azimuth, distance_km=0.3)
            else:
                start_point = site_coords # Fallback if no azimuth
            
            # Draw the Sector Wedge
            if cell.get("azimuth") is not None:
                wedge_points = get_wedge_points(
                    cell["site_lat"], 
                    cell["site_lon"], 
                    cell["azimuth"],
                    distance_km=0.3  # Length of the wedge on map
                )
                
                folium.Polygon(
                    locations=wedge_points,
                    color="royalblue",
                    fill=True,
                    fill_opacity=0.3,
                    weight=1,
                    tooltip=f"Sector Azimuth: {cell['azimuth']}°"
                ).add_to(m)
            
            # Determine color based on Horizontal Status
            # ✅ [DIRECT] -> green | Others -> red
            line_color = "#28a745" if "✅" in cell["h_status"] else "#dc3545"
            
            # Draw the Path Line (Starting from the TIP)(ONLY if offset <= 100°)
            # This keeps the map clean from extreme backlobe connections
            if offset is not None and offset <= 100:
                folium.PolyLine(
                    locations=[start_point, user_coords],
                    color=line_color,
                    weight=3,
                    opacity=0.8,
                    tooltip=f"Cell: {cell['cell_name']} | Distance: {cell['distance']}km"
                ).add_to(m)
            else:
                # Optional: Log that a line was skipped for clarity during debugging
                log.info(f"Skipping path line for {cell['cell_name']} - Offset ({offset}°) > 100°")
            
            # Add a small marker for the Site itself
            folium.CircleMarker(
                location=site_coords,
                radius=4,
                color="black",
                fill=True,
                fill_color="white",
                fill_opacity=1,
                popup=f"Site: {cell['site_id']}"
            ).add_to(m)
        # ADD THE LEGEND HERE
        add_map_legend(m)
    
    # Render map and capture clicks
    map_data = st_folium(
        m,
        width='stretch',
        height=500,
        returned_objects=["last_clicked"],
        key=f"main_map_{st.session_state.map_key}"
    )
    
    # Handle map clicks
    if map_data and map_data.get("last_clicked"):
        click_lat = map_data["last_clicked"]["lat"]
        click_lon = map_data["last_clicked"]["lng"]
        
        # Update if click is different
        if (abs(click_lat - st.session_state.lat) > 0.000001 or 
            abs(click_lon - st.session_state.lon) > 0.000001):
            
            update_coordinates(click_lat, click_lon)
            st.success(f"Location updated: {click_lat:.6f}, {click_lon:.6f}")
            st.session_state.map_key += 1
            st.rerun()

def render_analysis_results(results: dict):
    """Render the analysis results in a formatted way."""
    st.subheader("📊 2. RCA Diagnostic Results")
    
    if "cells" in results and results["cells"]:
        df_display = pd.DataFrame(results["cells"])
        
        # Display metrics if available
        if "summary" in results:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Cells", len(results["cells"]))
            with col2:
                healthy = sum(1 for cell in results["cells"] 
                            if "✅" in str(cell.get('h_status', '')) 
                            and "✅" in str(cell.get('v_status', '')))
                st.metric("Healthy Cells", healthy)
            with col3:
                st.metric("Sites Analyzed", results.get("sites_analyzed", "N/A"))
        
        # Display data with styling
        styled_df = df_display.style.map(
            color_status,
            subset=[col for col in ['h_status', 'v_status'] if col in df_display.columns]
        )
        
        st.dataframe(
            styled_df,
            width='stretch',
            hide_index=True
        )
        
        # Add download option
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="radiorca_analysis.csv",
            mime="text/csv",
            width='stretch'
        )
    else:
        st.warning("No cell data found. Check if database is loaded.")
        
        # Show debug info if available
        if "error" in results:
            st.error(f"Error: {results['error']}")
        if "message" in results:
            st.info(results["message"])

# ----------------------------------
# MAIN APPLICATION
# ----------------------------------
def main():
    """Main application function."""
    # Page configuration
    st.set_page_config(
        page_title="RadioRCA | Manual Confirm",
        layout="wide",
        page_icon="📡"
    )
    
    # Initialize session state
    init_session_state()
    
    # Application header
    st.title("📡 RadioRCA: Location Confirmation")
    st.markdown("""
    Interactive tool for radio network analysis and troubleshooting. 
    Select a location on the map or enter coordinates manually, then run the RCA analysis.
    """)
    
    # Render UI components
    site_limit, analyze_btn = render_sidebar()
    render_map()
    
    # ----------------------------------
    # EVENT HANDLERS
    # ----------------------------------
    # Handle analysis button click
    if analyze_btn:
        with st.spinner("Running RCA Analysis..."):
            try:
                # Validate coordinates before analysis
                if not validate_coordinates(st.session_state.lat, st.session_state.lon):
                    st.error("Invalid coordinates. Please select a valid location.")
                    st.stop()
                
                # Run analysis
                results = analyze_location(
                    st.session_state.lat,
                    st.session_state.lon,
                    site_limit
                )
                
                # Store results in session state
                st.session_state.analysis_results = results
                
                # Show success message
                st.success("Analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.session_state.analysis_results = None
                st.stop()
    
    # Display previous results if available
    if st.session_state.analysis_results:
        st.divider()
        render_analysis_results(st.session_state.analysis_results)

# ----------------------------------
# APPLICATION ENTRY POINT
# ----------------------------------
if __name__ == "__main__":
    main()
