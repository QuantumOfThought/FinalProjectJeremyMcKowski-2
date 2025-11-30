import streamlit as st
import pandas as pd
import time
import plotly.express as px  # Plotly for interactive maps and charts
from data_generator import NetworkTrafficGenerator

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
# STEP 2: INITIALIZE DATA GENERATOR
# ============================================================================
# Streamlit reruns the entire script on every interaction (button click, slider move, etc.)
# To preserve data between reruns, we use st.session_state
# This is like a dictionary that persists across reruns
# We check if 'traffic_generator' already exists; if not, create it ONCE
if 'traffic_generator' not in st.session_state:
    # Create a new instance of our NetworkTrafficGenerator class
    # This will only happen on the first run or after clearing cache
    st.session_state.traffic_generator = NetworkTrafficGenerator()

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
# STEP 4: DASHBOARD HEADER
# ============================================================================
# Main title and subtitle for the dashboard
st.title("📡 Ubiquiti Network Monitor")
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