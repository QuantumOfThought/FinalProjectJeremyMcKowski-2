import streamlit as st
import pandas as pd
import time
import plotly.express as px  # Plotly for interactive maps and charts
import plotly.graph_objects as go  # Plotly for custom graphs
from datetime import datetime, timedelta
from data_generator import NetworkTrafficGenerator
from weather import WeatherFetcher

# ============================================================================
# STEP 1: PAGE CONFIGURATION
# ============================================================================
# This must be the first Streamlit command called
# Sets up the page title, icon, and layout before any content is rendered
st.set_page_config(
    page_title="Ubiquiti Network Dashboard",  # Browser tab title
    page_icon="📡",                            # Browser tab icon (emoji)
    layout="wide"                              # Use full width of browser
)

# ============================================================================
# STEP 2: INITIALIZE DATA GENERATOR AND WEATHER FETCHER
# ============================================================================
# Streamlit reruns the entire script on every interaction (button click, slider move, etc.)
# To preserve data between reruns, we use st.session_state
# This is like a dictionary that persists across reruns
# We check if 'traffic_generator' already exists; if not, create it ONCE
if 'traffic_generator' not in st.session_state:
    # Create a new instance of our NetworkTrafficGenerator class
    # This will only happen on the first run or after clearing cache
    st.session_state.traffic_generator = NetworkTrafficGenerator()

# Initialize weather fetcher
if 'weather_fetcher' not in st.session_state:
    st.session_state.weather_fetcher = WeatherFetcher()

# Initialize traffic history for 30-minute graph
if 'traffic_history' not in st.session_state:
    st.session_state.traffic_history = {
        'timestamps': [],
        'download_speeds': [],
        'upload_speeds': []
    }

# ============================================================================
# STEP 3: SIDEBAR CONTROLS
# ============================================================================
# The sidebar is the collapsible panel on the left side of the dashboard
# It's used for controls, settings, and information that doesn't need to be
# in the main viewing area

st.sidebar.title("Controls")

# AUTO-REFRESH TOGGLE
# Checkbox widget - returns True when checked, False when unchecked
# This controls whether the dashboard automatically updates
auto_refresh = st.sidebar.checkbox("Enable Live Updates", value=False)

# REFRESH RATE SLIDER
# Only matters if auto_refresh is enabled
# Allows user to control how often the dashboard updates (1-10 seconds)
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 1)

# Visual separator line in the sidebar
st.sidebar.markdown("---")

# ABOUT SECTION
# Provides context about what this dashboard does
st.sidebar.title("About")
st.sidebar.info(
    "This dashboard simulates network traffic using Faker. "
    "It monitors a Ubiquiti Dream Machine, Desktop PC, Mobile devices, and a Printer. "
    "Traffic data is randomly generated to demonstrate network monitoring capabilities."
)

# ============================================================================
# STEP 4: DASHBOARD HEADER WITH WEATHER WIDGET
# ============================================================================
# Create a two-column layout for header with weather widget on the right
header_left, header_right = st.columns([3, 1])

# Left column: Main title and subtitle
with header_left:
    st.title("📡 Ubiquiti Network Monitor")
    st.markdown("### Real-time Traffic Simulation")

# Right column: Weather widget
with header_right:
    # Fetch current weather data
    weather_data = st.session_state.weather_fetcher.get_current_weather()

    if weather_data:
        # Display weather widget with custom styling
        st.markdown(
            f"""
            <div style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-top: 10px;
            '>
                <h3 style='margin: 0; font-size: 16px; font-weight: 500;'>📍 {weather_data['city']}</h3>
                <h1 style='margin: 10px 0; font-size: 48px; font-weight: bold;'>{weather_data['temperature']}°{weather_data['unit']}</h1>
                <p style='margin: 5px 0; font-size: 18px;'>{weather_data['weather_text']}</p>
                <div style='margin-top: 10px; font-size: 14px; opacity: 0.9;'>
                    <p style='margin: 2px 0;'>💧 Humidity: {weather_data['humidity']}%</p>
                    <p style='margin: 2px 0;'>💨 Wind: {weather_data['wind_speed']} {weather_data['wind_unit']} {weather_data['wind_direction']}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Display error message if weather data couldn't be fetched
        st.error("Unable to fetch weather data")

# ============================================================================
# STEP 5: FETCH CURRENT DEVICE DATA
# ============================================================================
# Call the get_devices() method from our generator
# This triggers _simulate_traffic() internally, which:
#   - Updates traffic counters
#   - Randomly toggles device online/offline status
#   - Updates timestamps
# Returns a list of device dictionaries
devices = st.session_state.traffic_generator.get_devices()

# ============================================================================
# STEP 6: PROCESS DATA FOR DISPLAY
# ============================================================================
# Convert the list of device dictionaries into a pandas DataFrame
# DataFrames are easier to manipulate and display in Streamlit
df = pd.DataFrame(devices)

# CONVERT BYTES TO MEGABYTES
# Raw byte counts are hard to read (e.g., 5242880 bytes)
# Converting to MB makes it more human-readable (e.g., 5.00 MB)
# Formula: bytes / (1024 * 1024) = megabytes
df['Download (MB)'] = df['download_bytes'] / (1024 * 1024)
df['Upload (MB)'] = df['upload_bytes'] / (1024 * 1024)

# CALCULATE SUMMARY STATISTICS
# Count only devices with status == 'ONLINE'
total_devices = len(df[df['status'] == 'ONLINE'])
# Sum all download traffic across all devices
total_download = df['Download (MB)'].sum()
# Sum all upload traffic across all devices
total_upload = df['Upload (MB)'].sum()

# COLLECT CURRENT SPEEDS FOR HISTORY GRAPH
# Sum current speeds from all devices
current_download_speed = df['current_download_speed'].sum()
current_upload_speed = df['current_upload_speed'].sum()

# Add to history with timestamp
current_time = datetime.now()
st.session_state.traffic_history['timestamps'].append(current_time)
st.session_state.traffic_history['download_speeds'].append(current_download_speed)
st.session_state.traffic_history['upload_speeds'].append(current_upload_speed)

# Keep only last 30 minutes of data
cutoff_time = current_time - timedelta(minutes=30)
# Filter out data older than 30 minutes
valid_indices = [i for i, t in enumerate(st.session_state.traffic_history['timestamps']) if t >= cutoff_time]
st.session_state.traffic_history['timestamps'] = [st.session_state.traffic_history['timestamps'][i] for i in valid_indices]
st.session_state.traffic_history['download_speeds'] = [st.session_state.traffic_history['download_speeds'][i] for i in valid_indices]
st.session_state.traffic_history['upload_speeds'] = [st.session_state.traffic_history['upload_speeds'][i] for i in valid_indices]

# ============================================================================
# STEP 7: DISPLAY METRICS (TOP ROW)
# ============================================================================
# Create 3 equal-width columns for metric cards
col1, col2, col3 = st.columns(3)

# Each metric() creates a card with a label and value
# These provide quick overview stats at the top of the dashboard
col1.metric("Connected Devices", total_devices)
col2.metric("Total Download", f"{total_download:.2f} MB")
col3.metric("Total Upload", f"{total_upload:.2f} MB")

# ============================================================================
# STEP 7.5: NETWORK SPEED GRAPH (30-MINUTE HISTORY)
# ============================================================================
st.markdown("### Network Throughput (Last 30 Minutes)")

# Only show graph if we have enough data points
if len(st.session_state.traffic_history['timestamps']) > 0:
    # Create Plotly figure with two lines (Download and Upload)
    fig_speed = go.Figure()

    # Add Download speed line (blue)
    fig_speed.add_trace(go.Scatter(
        x=st.session_state.traffic_history['timestamps'],
        y=st.session_state.traffic_history['download_speeds'],
        mode='lines',
        name='Download',
        line=dict(color='#3b82f6', width=2),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))

    # Add Upload speed line (green)
    fig_speed.add_trace(go.Scatter(
        x=st.session_state.traffic_history['timestamps'],
        y=st.session_state.traffic_history['upload_speeds'],
        mode='lines',
        name='Upload',
        line=dict(color='#10b981', width=2),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.1)'
    ))

    # Update layout
    fig_speed.update_layout(
        xaxis_title="Time",
        yaxis_title="Speed (MB/s)",
        hovermode='x unified',
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Display the graph
    st.plotly_chart(fig_speed, use_container_width=True)
else:
    st.info("Collecting data... Graph will appear after a few updates.")

# ============================================================================
# STEP 8: GLOBAL TRAFFIC MAP (PLOTLY)
# ============================================================================
# This section creates an interactive map showing where external connections
# are coming from geographically

st.markdown("### Global Traffic Origins")
st.markdown("Live map of external servers communicating with your network.")

# FETCH CONNECTION DATA
# Returns a list of dictionaries with 'lat' and 'lon' keys
# Weighted by geography: 50% US, 10% China, 10% Russia, 30% EU
connections = st.session_state.traffic_generator.generate_external_connections()

# Convert to DataFrame for Plotly
map_df = pd.DataFrame(connections)

# CREATE INTERACTIVE PLOTLY MAP
# scatter_geo creates a scatter plot on a geographic map projection
# Each connection appears as a point on the globe
fig = px.scatter_geo(
    map_df,                          # DataFrame with lat/lon data
    lat='lat',                       # Column name for latitude
    lon='lon',                       # Column name for longitude
    projection='natural earth',      # Map projection style (globe-like)
    title='',                        # No title (we have markdown above)
    height=400                       # Height of the map in pixels
)

# CUSTOMIZE MAP APPEARANCE
fig.update_traces(
    marker=dict(
        size=8,                      # Size of each point
        color='red',                 # Color of connection points
        opacity=0.7                  # Slightly transparent
    )
)

# DISPLAY THE MAP
# use_container_width makes the map responsive to screen size
st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# STEP 9: DEVICE DETAILS TABLE
# ============================================================================
# This section displays a detailed table of all devices on the network

st.subheader("Device Details")

# SELECT COLUMNS TO DISPLAY
# We added 'connection_type' to show Wired vs Wi-Fi
# Order matters - this is how they'll appear left to right in the table
display_df = df[[
    'name',              # Device name (e.g., "Home Desktop PC")
    'type',              # Device type (e.g., "Desktop", "Mobile")
    'ip',                # IP address on local network
    'mac',               # MAC address (hardware identifier)
    'connection_type',   # NEW: "Wired" or "Wi-Fi"
    'status',            # "ONLINE" or "OFFLINE"
    'Download (MB)',     # Download traffic in megabytes
    'Upload (MB)',       # Upload traffic in megabytes
    'last_seen'          # Timestamp of last activity
]]

# DISPLAY THE TABLE
# The dataframe() function creates an interactive table
st.dataframe(
    display_df,
    use_container_width=True,        # Make table full width
    column_config={
        # Rename columns for better readability in the UI
        "name": "Device Name",
        "type": "Type",
        "ip": "IP Address",
        "mac": "MAC Address",
        "connection_type": "Connection",  # NEW: Display the Wired/Wi-Fi info
        "status": "Status",
        # NumberColumn allows formatting (e.g., "5.23 MB")
        "Download (MB)": st.column_config.NumberColumn("Download (MB)", format="%.2f MB"),
        "Upload (MB)": st.column_config.NumberColumn("Upload (MB)", format="%.2f MB"),
        "last_seen": "Last Seen"
    },
    hide_index=True                  # Don't show row numbers
)

# ============================================================================
# STEP 10: AUTO-REFRESH LOGIC
# ============================================================================
# If the user enabled "Live Updates" in the sidebar:
# 1. Wait for the specified number of seconds (refresh_rate)
# 2. Rerun the entire script (st.rerun())
# This creates a loop that continuously updates the dashboard

if auto_refresh:
    # Pause execution for the refresh_rate duration
    time.sleep(refresh_rate)
    # Rerun the entire script from the top
    # This will fetch new data and update all visualizations
    st.rerun()