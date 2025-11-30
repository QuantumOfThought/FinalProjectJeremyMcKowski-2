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
    page_icon="🌐",                            # Browser tab icon
    layout="wide"                              # Use full width of browser
)

# ============================================================================
# STEP 1.5: CUSTOM CSS TO HIDE STATUS ICONS AND REDUCE FLICKER
# ============================================================================
st.markdown("""
    <style>
        /* Hide the running man icon and status indicators */
        .stStatusWidget {
            display: none !important;
        }

        /* Hide the app menu dots in top right */
        #MainMenu {
            visibility: hidden;
        }

        /* Hide streamlit branding footer */
        footer {
            visibility: hidden;
        }

        /* Hide "Running..." text */
        .stApp header + div[data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* Additional status widget hiding */
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* Hide the deploy button */
        .stDeployButton {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

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

# Initialize security alerts storage
if 'security_alerts' not in st.session_state:
    st.session_state.security_alerts = []

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
    "Real-time network monitoring dashboard for Ubiquiti devices. "
    "Tracks connected devices, bandwidth usage, security alerts, and global traffic patterns. "
    "Features live throughput monitoring and weather integration."
)

# ============================================================================
# STEP 4: DASHBOARD HEADER WITH ISP INFO AND WEATHER WIDGET
# ============================================================================
# Create a two-column layout for ISP info and weather widget
header_left, header_right = st.columns([1, 1])

# Left column: ISP Information
with header_left:
    st.markdown(
        """
        <div style='
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            color: white;
            margin-bottom: 10px;
        '>
            <div style='font-size: 16px; font-weight: 500; margin-bottom: 8px;'>ISP: ISP.net</div>
            <div style='font-size: 14px; color: #888;'>IP Address: 1.2.3.4</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Right column: Weather widget (horizontal rectangle)
with header_right:
    # Fetch current weather data
    weather_data = st.session_state.weather_fetcher.get_current_weather()

    if weather_data:
        # Display compact horizontal weather widget
        st.markdown(
            f"""
            <div style='
                background: #000000;
                border: 1px solid #ffffff;
                border-radius: 8px;
                padding: 15px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            '>
                <div>
                    <div style='font-size: 14px; color: #888;'>{weather_data['city']}</div>
                    <div style='font-size: 24px; font-weight: bold;'>{weather_data['temperature']}°{weather_data['unit']}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 14px;'>{weather_data['weather_text']}</div>
                    <div style='font-size: 12px; color: #888;'>Humidity: {weather_data['humidity']}%</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Display error message if weather data couldn't be fetched
        st.markdown(
            """
            <div style='
                background: #000000;
                border: 1px solid #ffffff;
                border-radius: 8px;
                padding: 15px;
                color: #888;
                text-align: center;
            '>
                Weather unavailable
            </div>
            """,
            unsafe_allow_html=True
        )

# Main title (no emoji to prevent icon glitch)
st.title("Ubiquiti Network Monitor")
st.markdown("### Real-time Traffic Simulation")

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

# COLLECT SECURITY ALERTS
# Generate new alerts (20% chance per refresh)
new_alerts = st.session_state.traffic_generator.generate_security_alerts()

# Add new alerts to the beginning of the list (most recent first)
if new_alerts:
    st.session_state.security_alerts = new_alerts + st.session_state.security_alerts

# Keep only last 50 alerts
st.session_state.security_alerts = st.session_state.security_alerts[:50]

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
# STEP 7.25: LIVE THROUGHPUT DISPLAY
# ============================================================================
st.markdown("### Live Throughput")

# Create columns for download and upload speeds
throughput_col1, throughput_col2 = st.columns(2)

with throughput_col1:
    st.markdown(
        f"""
        <div style='
            background: #1a1a1a;
            border: 1px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        '>
            <div style='color: #888; font-size: 14px; margin-bottom: 10px;'>DOWNLOAD</div>
            <div style='color: #00d4ff; font-size: 36px; font-weight: bold;'>{current_download_speed:.2f} Mbps</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with throughput_col2:
    st.markdown(
        f"""
        <div style='
            background: #1a1a1a;
            border: 1px solid #a855f7;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        '>
            <div style='color: #888; font-size: 14px; margin-bottom: 10px;'>UPLOAD</div>
            <div style='color: #a855f7; font-size: 36px; font-weight: bold;'>{current_upload_speed:.2f} Mbps</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================================
# STEP 7.5: NETWORK SPEED GRAPH (30-MINUTE HISTORY)
# ============================================================================
st.markdown("### Network Throughput (Last 30 Minutes)")

# Only show graph if we have enough data points
if len(st.session_state.traffic_history['timestamps']) > 0:
    # Create Plotly figure with two lines (Download and Upload)
    fig_speed = go.Figure()

    # Add Download speed line (cyan - matching reference image)
    fig_speed.add_trace(go.Scatter(
        x=st.session_state.traffic_history['timestamps'],
        y=st.session_state.traffic_history['download_speeds'],
        mode='lines',
        name='Download',
        line=dict(color='#00d4ff', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 212, 255, 0.2)'
    ))

    # Add Upload speed line (purple/magenta - matching reference image)
    fig_speed.add_trace(go.Scatter(
        x=st.session_state.traffic_history['timestamps'],
        y=st.session_state.traffic_history['upload_speeds'],
        mode='lines',
        name='Upload',
        line=dict(color='#a855f7', width=2),
        fill='tozeroy',
        fillcolor='rgba(168, 85, 247, 0.2)'
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
# STEP 8: DEVICES CURRENTLY CONNECTED
# ============================================================================
# This section displays a detailed table of all devices on the network

st.subheader("Devices Currently Connected")

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
# STEP 9: GLOBAL TRAFFIC MAP (PLOTLY)
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

# CREATE INTERACTIVE PLOTLY MAP with better coloring
# scatter_geo creates a scatter plot on a geographic map projection
fig = px.scatter_geo(
    map_df,                          # DataFrame with lat/lon data
    lat='lat',                       # Column name for latitude
    lon='lon',                       # Column name for longitude
    projection='equirectangular',    # Flat map projection for better visibility
    title='',                        # No title (we have markdown above)
    height=450                       # Height of the map in pixels
)

# CUSTOMIZE MAP APPEARANCE with better colors
fig.update_traces(
    marker=dict(
        size=10,                     # Size of each point
        color='#00d4ff',             # Cyan color matching download theme
        opacity=0.8,                 # Slightly transparent
        line=dict(
            width=1,
            color='white'
        )
    )
)

# Update map layout for better colors
fig.update_geos(
    showcountries=True,
    countrycolor="rgba(100, 100, 100, 0.3)",
    showcoastlines=True,
    coastlinecolor="rgba(255, 255, 255, 0.3)",
    showland=True,
    landcolor="rgba(30, 30, 30, 0.8)",
    showocean=True,
    oceancolor="rgba(10, 10, 30, 0.9)",
    projection_type='equirectangular',
    bgcolor='rgba(0,0,0,0)'
)

fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    geo=dict(bgcolor='rgba(0,0,0,0)')
)

# DISPLAY THE MAP
# use_container_width makes the map responsive to screen size
st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# STEP 8.5: SECURITY ALERTS TABLE
# ============================================================================
st.markdown("### 🚨 Suspicious Traffic Alerts")

if st.session_state.security_alerts:
    # Convert alerts to DataFrame for display
    alerts_df = pd.DataFrame(st.session_state.security_alerts)

    # Format timestamp for better readability
    alerts_df['Time'] = alerts_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Select and rename columns for display
    display_alerts = alerts_df[['Time', 'device', 'external_ip', 'reason', 'severity']]
    display_alerts.columns = ['Time', 'Device', 'External IP', 'Alert Type', 'Severity']

    # Apply color coding based on severity
    def highlight_severity(row):
        if row['Severity'] == 'High':
            return ['background-color: #fee2e2; color: #991b1b'] * len(row)
        elif row['Severity'] == 'Medium':
            return ['background-color: #fef3c7; color: #92400e'] * len(row)
        else:
            return [''] * len(row)

    # Display styled dataframe
    styled_df = display_alerts.style.apply(highlight_severity, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True,
        column_config={
            "Time": st.column_config.TextColumn("Time", width="medium"),
            "Device": st.column_config.TextColumn("Device", width="medium"),
            "External IP": st.column_config.TextColumn("External IP", width="medium"),
            "Alert Type": st.column_config.TextColumn("Alert Type", width="large"),
            "Severity": st.column_config.TextColumn("Severity", width="small")
        },
        hide_index=True
    )

    # Show alert summary
    high_alerts = len([a for a in st.session_state.security_alerts if a['severity'] == 'High'])
    medium_alerts = len([a for a in st.session_state.security_alerts if a['severity'] == 'Medium'])

    col_alert1, col_alert2, col_alert3 = st.columns(3)
    col_alert1.metric("Total Alerts", len(st.session_state.security_alerts))
    col_alert2.metric("High Severity", high_alerts, delta=None, delta_color="inverse")
    col_alert3.metric("Medium Severity", medium_alerts)
else:
    st.info("No suspicious traffic detected. Your network appears secure.")

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