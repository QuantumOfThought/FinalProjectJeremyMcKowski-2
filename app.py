import streamlit as st
import pandas as pd
import time
from data_generator import NetworkTrafficGenerator

# Step 1: Page Configuration
st.set_page_config(
    page_title="Ubiquiti Network Dashboard",
    page_icon="📡",
    layout="wide"
)

# Step 2: Initialize the Data Generator
if 'traffic_generator' not in st.session_state:
    st.session_state.traffic_generator = NetworkTrafficGenerator()

# Step 3: Sidebar Controls
st.sidebar.title("Controls")
# Add a toggle for Auto-Refresh
auto_refresh = st.sidebar.checkbox("Enable Live Updates", value=False)
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 1)

st.sidebar.markdown("---")
st.sidebar.title("About")
st.sidebar.info(
    "This dashboard simulates network traffic using Faker. "
    "It monitors a Ubiquiti Dream Machine, a Desktop, and a Mobile device."
)
# Step 4: Dashboard Header
st.title("📡 Ubiquiti Network Monitor")
st.markdown("### Real-time Traffic Simulation")

# Step 5: Get Data
# Fetch the latest device data
devices = st.session_state.traffic_generator.get_devices()

# Step 6: Process Data (Convert to MB)
# We convert the raw list of dicts into a DataFrame first for easier manipulation
df = pd.DataFrame(devices)

# Create new columns for MB for better readability
df['Download (MB)'] = df['download_bytes'] / (1024 * 1024)
df['Upload (MB)'] = df['upload_bytes'] / (1024 * 1024)

# Calculate totals
# Only count devices that are currently ONLINE
total_devices = len(df[df['status'] == 'ONLINE'])
total_download = df['Download (MB)'].sum()
total_upload = df['Upload (MB)'].sum()

# Step 7: Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Connected Devices", total_devices)
col2.metric("Total Download", f"{total_download:.2f} MB")
col3.metric("Total Upload", f"{total_upload:.2f} MB")

# Step 8: Visualizations (Map)
st.markdown("### Global Traffic Origins")
st.markdown("Live map of external servers communicating with your network.")

# Get connection data from generator
connections = st.session_state.traffic_generator.generate_external_connections()
map_df = pd.DataFrame(connections)

# Display the map
st.map(map_df)

# Step 9: Display Data Table
st.subheader("Device Details")
# Select and rename columns for the view
display_df = df[['name', 'type', 'ip', 'status', 'Download (MB)', 'Upload (MB)', 'last_seen', 'mac']]

st.dataframe(
    display_df,
    width='stretch',
    column_config={
        "name": "Device Name",
        "type": "Type",
        "ip": "IP Address",
        "status": "Status",
        "Download (MB)": st.column_config.NumberColumn("Download (MB)", format="%.2f MB"),
        "Upload (MB)": st.column_config.NumberColumn("Upload (MB)", format="%.2f MB"),
        "last_seen": "Last Connected",
        "mac": "MAC Address"
    }
)

# Step 10: Auto-Refresh Logic
# If the checkbox is checked, we wait for the specified time and then rerun the script.
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()