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