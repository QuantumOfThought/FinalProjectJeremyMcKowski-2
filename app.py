"""
Ubiquiti Network Monitor Dashboard
This application provides real-time monitoring of network devices, traffic patterns,
security alerts, and CVE vulnerability tracking in a professional dashboard interface.

Author: Jeremy McKowski
Date: November 2025
Course: PYTHON_CLASS Final Project
"""

# ============================================================================
# REQUIRED LIBRARY IMPORTS
# ============================================================================
# I'm importing the external libraries I need for this project
# My professor taught us to put all imports at the top of the file

import streamlit as st
# I'm using Streamlit to build my web dashboard
# I chose this because I don't know HTML/CSS/JavaScript very well
# Streamlit lets me create web apps using just Python code

import pandas as pd
# I'm using Pandas to work with my device data in table format
# It's like working with Excel spreadsheets but in Python
# Makes it easier for me to filter and display the network information

import time
# I need the time module for my auto-refresh feature
# I use time.sleep() to pause between dashboard updates
# This way the dashboard doesn't refresh too fast and overwhelm the user

import plotly.express as px
# I'm using Plotly Express for my world map visualization
# My professor showed us this library for making interactive charts
# I picked it over matplotlib because users can zoom and hover on the charts

import plotly.graph_objects as go
# I'm using Plotly Graph Objects for my network speed graph
# This gives me more control over the colors and styling than plotly.express
# I needed this for the filled area under the speed lines

from datetime import datetime, timedelta
# I'm importing datetime tools to work with timestamps
# I use datetime to record when each data point happens
# I use timedelta to calculate the 30-minute window for my graphs

from data_generator import NetworkTrafficGenerator
# This is my custom module that creates fake network data
# I made this because I can't access real Ubiquiti router APIs
# It generates realistic device names, IPs, and traffic to make my demo work

from cve_fetcher import CVEFetcher
# This is my custom module for fetching security vulnerabilities
# I made this to pull CVE data from the National Vulnerability Database
# It shows the latest security issues for Ubiquiti routers

# ============================================================================
# STEP 1: PAGE CONFIGURATION
# ============================================================================
# I have to call st.set_page_config() first before any other Streamlit commands
# My professor said this MUST be the first Streamlit function or it crashes
# I learned this the hard way when I put it after other code and got errors

st.set_page_config(
    page_title="Ubiquiti Network Dashboard",
    # I set this to change what shows up in the browser tab
    # This way users can tell which tab is my dashboard

    layout="wide"
    # I set this to "wide" so my dashboard uses the full screen width
    # The default is "centered" which makes everything narrow
    # I need the full width to fit my charts and tables side by side
)

# ============================================================================
# STEP 2: CUSTOM CSS STYLING
# ============================================================================
# I'm using custom CSS to make my dashboard look cleaner and more professional
# My professor showed me how to inject CSS using st.markdown()
# I have to set unsafe_allow_html=True so Streamlit actually runs my CSS

st.markdown("""
    <style>
        /* ================================================================
           HIDING STREAMLIT UI ELEMENTS
           ================================================================
           I'm hiding some default Streamlit elements that look unprofessional
           My professor said this makes the dashboard look better for demos
        */

        /* I'm hiding the running man icon that shows in the corner */
        .stStatusWidget {
            display: none !important;
            /* The !important makes sure my rule wins over Streamlit's default */
            /* That icon was distracting during live updates */
        }

        /* I'm hiding the hamburger menu in the top right */
        #MainMenu {
            visibility: hidden;
            /* Users don't need access to Streamlit settings for my demo */
        }

        /* I'm hiding the "Made with Streamlit" footer */
        footer {
            visibility: hidden;
            /* This makes my dashboard look more professional */
        }

        /* I'm hiding more status widgets using data attributes */
        .stApp header + div[data-testid="stStatusWidget"] {
            display: none !important;
            /* I learned about data-testid from researching Streamlit's HTML structure */
        }

        /* This catches any other status widgets I might have missed */
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* I'm hiding the Deploy button too */
        .stDeployButton {
            display: none !important;
            /* I don't need cloud deployment for this class project */
        }

        /* ================================================================
           REMOVING ANIMATIONS AND TRANSITIONS
           ================================================================
           I'm disabling all the fade effects because they made my dashboard
           flicker during auto-refresh. I want instant updates instead.
        */

        /* I'm applying this to every element on the page */
        *, *::before, *::after {
            transition: none !important;
            /* Transition is what makes things fade smoothly */
            /* I set it to none so changes happen instantly */

            animation: none !important;
            /* Animation is for moving/changing effects */
            /* I don't want any of that */

            transition-duration: 0s !important;
            animation-duration: 0s !important;
            /* I'm forcing the duration to zero just to be extra sure */
        }

        /* I'm targeting the main HTML structure elements */
        html, body, #root, .stApp, .main, .block-container {
            transition: none !important;
            animation: none !important;
            opacity: 1 !important;
            /* Opacity 1 means fully visible - no fading */
        }

        /* I'm targeting all the different Streamlit components */
        .element-container,
        .stMarkdown,
        .stDataFrame,
        .stMetric,
        .stPlotlyChart,
        div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"],
        div[data-testid="column"],
        section[data-testid="stSidebar"],
        .stSelectbox,
        .stSlider,
        .stCheckbox {
            transition: none !important;
            animation: none !important;
            animation-duration: 0s !important;
            animation-delay: 0s !important;
            transition-delay: 0s !important;
            opacity: 1 !important;
            /* All of these render instantly now */
        }

        /* I'm hiding the skeleton loading screens */
        .stSkeleton {
            display: none !important;
            /* These are the gray placeholder boxes */
            /* I don't want those showing up */
        }

        /* I'm making sure the whole app container doesn't fade */
        [data-testid="stAppViewContainer"] {
            transition: none !important;
            animation: none !important;
            opacity: 1 !important;
            /* This stops the whole page from fading when it refreshes */
        }
    </style>
""", unsafe_allow_html=True)
# I have to set unsafe_allow_html=True to make the CSS work
# My professor warned us this is a security risk with user input
# But it's safe here because I wrote all the CSS myself (not from users)

# ============================================================================
# STEP 3: SESSION STATE INITIALIZATION
# ============================================================================
# I'm using st.session_state to store data that needs to persist across refreshes
# My professor taught us that Streamlit reruns the whole script every time
# something changes (button click, slider move, dropdown selection, etc.)
#
# The problem is that without session_state, my variables would reset to zero
# every single time. My traffic counters would never accumulate, device names
# would change constantly, and nothing would work right.
#
# So I'm using st.session_state as "memory" that survives the reruns
# It's like a dictionary that Streamlit maintains between page refreshes

if 'traffic_generator' not in st.session_state:
    # I check if traffic_generator already exists before creating it
    # This way I only create it once (first time the app runs)
    # If I didn't do this check, I'd recreate it every refresh

    st.session_state.traffic_generator = NetworkTrafficGenerator()
    # This is my custom class that generates fake network data
    # I create it once and keep reusing it so:
    #   - Device names stay the same across refreshes
    #   - Traffic counters keep accumulating instead of resetting
    #   - My app doesn't slow down from creating new objects constantly

if 'cve_fetcher' not in st.session_state:
    # Same idea - I only create my CVE fetcher once
    st.session_state.cve_fetcher = CVEFetcher()
    # This is my class that calls the NVD API for security vulnerabilities
    # I keep it in session_state so I can cache API responses
    # This helps me avoid hitting the rate limits

if 'traffic_history' not in st.session_state:
    # I'm initializing storage for my 30-minute traffic history
    # This is for the "All Devices" view on my speed graph
    st.session_state.traffic_history = {
        'timestamps': [],           # I'll store datetime objects here
        'download_speeds': [],      # I'll store download speeds here (MB/s)
        'upload_speeds': []         # I'll store upload speeds here (MB/s)
    }
    # I start with empty lists and they fill up as the dashboard runs
    # Eventually they'll have 30 minutes worth of data points

if 'security_alerts' not in st.session_state:
    # I'm initializing storage for security alerts
    st.session_state.security_alerts = []
    # Starts empty
    # My data generator will add fake security alerts to this list
    # I limit it to 50 alerts total so it doesn't grow forever

# ============================================================================
# STEP 4: SIDEBAR CONTROLS AND USER INPUTS
# ============================================================================
# I'm putting my user controls in the sidebar on the left
# My professor showed us that sidebars keep controls organized and out of the way
# Users can collapse the sidebar if they want more screen space

st.sidebar.title("Controls")
# I'm adding a heading to label this section
# This way users know these are the controls

# ----------------------------------------------------------------------------
# CONTROL 1: AUTO-REFRESH TOGGLE
# ----------------------------------------------------------------------------
# I'm adding a checkbox so users can turn live updates on or off

auto_refresh = st.sidebar.checkbox("Enable Live Updates", value=False)
# I'm using st.sidebar.checkbox() to create the toggle
# I set value=False so it starts unchecked (off by default)
# This returns True when checked, False when unchecked
# I use this variable later to control whether the dashboard auto-refreshes

# ----------------------------------------------------------------------------
# CONTROL 2: REFRESH RATE SLIDER
# ----------------------------------------------------------------------------
# I'm adding a slider so users can control how fast the dashboard updates

refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 1)
# I'm using st.sidebar.slider() to create the slider
# The parameters are: label, min value, max value, default value
# So users can pick anywhere from 1 to 10 seconds
# I start it at 1 second (fast updates)
# Even if live updates are off, this slider still works

# ----------------------------------------------------------------------------
# CONTROL 3: DEVICE SELECTION DROPDOWN
# ----------------------------------------------------------------------------
# I'm adding a dropdown so users can filter by device or view everything

temp_devices = st.session_state.traffic_generator.get_devices()
# I have to fetch the device list first so I can populate the dropdown
# I call it temp_devices because I just need it temporarily
# The main device data gets fetched later in the code

device_names = ["All Devices"] + [device['name'] for device in temp_devices]
# I'm building a list of device names for the dropdown
# I start with "All Devices" as the first option
# Then I use a list comprehension to extract just the names from temp_devices
# The + operator combines these into one list
# So I get: ["All Devices", "Home PC", "iPhone", etc.]

selected_device = st.sidebar.selectbox("Select Device", device_names, index=0)
# I'm using st.sidebar.selectbox() to create the dropdown
# I pass in my device_names list as the options
# I set index=0 so "All Devices" is selected by default
# This returns the name of whatever device the user picks
# I use this throughout my code to filter the data

st.sidebar.markdown("---")
# I'm adding a horizontal line to separate the controls from the About section
# This makes the sidebar look more organized

# ----------------------------------------------------------------------------
# ABOUT SECTION
# ----------------------------------------------------------------------------
# I'm adding an About section so users understand what my dashboard does

st.sidebar.title("About")
# Another heading for this section

st.sidebar.info(
    "Real-time network monitoring dashboard for Ubiquiti devices. "
    "Tracks connected devices, bandwidth usage, security alerts, and global traffic patterns. "
    "Features live throughput monitoring and CVE vulnerability tracking."
)
# I'm using st.sidebar.info() to create a blue info box
# This gives users a quick summary of what my dashboard does
# My professor said this is important for presentations

# ============================================================================
# STEP 5: DASHBOARD HEADER WITH ISP AND CVE WIDGETS
# ============================================================================
# I'm creating the top section of my dashboard with two widgets side by side
# Left side shows ISP info, right side shows CVE security vulnerabilities

header_left, header_right = st.columns([1, 1])
# I'm using st.columns() to create two equal-width columns
# The [1, 1] means 50/50 split (equal proportions)
# This returns two column objects that I can put content into

# ----------------------------------------------------------------------------
# LEFT HEADER: ISP INFORMATION DISPLAY
# ----------------------------------------------------------------------------
with header_left:
    # I'm using 'with' so everything inside here goes in the left column
    # This is how Streamlit knows where to put each widget

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
    # I'm using HTML/CSS here to create a custom info card
    # Streamlit's built-in widgets didn't give me the exact look I wanted
    # My CSS styling:
    #   - background: #1a1a1a makes it dark gray (matches my dashboard theme)
    #   - border: 1px solid #333 adds a subtle gray border
    #   - border-radius: 8px rounds the corners
    #   - padding: 15px adds space inside so text isn't cramped
    # The content:
    #   - First line shows the ISP name (ISP.net is just a placeholder)
    #   - Second line shows the public IP address (hardcoded for demo)
    # In a real app I'd fetch the actual ISP and IP dynamically

# ----------------------------------------------------------------------------
# RIGHT HEADER: CVE VULNERABILITY WIDGET
# ----------------------------------------------------------------------------
# I added this CVE widget to show security vulnerabilities for Ubiquiti routers
# CVE stands for Common Vulnerabilities and Exposures - it's how security bugs are tracked
# I fetch the data from the National Vulnerability Database API

with header_right:
    # This is the right column (I created 2 columns earlier for the header)
    # Left = ISP info, Right = CVE security info

    # =========================================================================
    # FETCH THE LATEST 3 CVES
    # =========================================================================
    # I call my CVE fetcher (stored in session state) to get 3 vulnerabilities
    cve_data = st.session_state.cve_fetcher.get_ubiquiti_cves(max_results=3)
    # This returns a list of dictionaries with CVE info, or None if it fails

    # =========================================================================
    # CHECK IF I GOT DATA BACK
    # =========================================================================
    # I need to make sure the API call worked and returned some CVEs
    if cve_data and len(cve_data) > 0:
        # Both conditions are true - I have data to display

        # =====================================================================
        # PICK A BORDER COLOR BASED ON SEVERITY
        # =====================================================================
        # I want the widget border to match how dangerous the first CVE is
        # The most recent CVE is always first in the list
        first_cve = cve_data[0]
        severity = first_cve.get('severity', 'UNKNOWN')

        # I pick a color based on how dangerous it is
        if severity in ['CRITICAL', 'HIGH']:
            severity_color = '#ef4444'  # Red for dangerous
        elif severity == 'MEDIUM':
            severity_color = '#f59e0b'  # Orange for medium risk
        else:
            severity_color = '#10b981'  # Green for low risk

        # =====================================================================
        # CREATE THE WIDGET HEADER
        # =====================================================================
        # I use HTML/CSS here because Streamlit's built-in widgets don't let me
        # customize the colors the way I want
        st.markdown(
            f"""
            <div style='
                background: #000000;
                border: 1px solid {severity_color};
                border-radius: 8px;
                padding: 15px;
                color: white;
                margin-bottom: 10px;
            '>
                <div style='font-size: 16px; font-weight: 500; margin-bottom: 8px; color: {severity_color};'>Latest Ubiquiti CVEs</div>
                <div style='font-size: 14px; color: #888; margin-bottom: 10px;'>Recent Security Vulnerabilities</div>
            """,
            unsafe_allow_html=True
            # I need to set this to True so Streamlit renders my HTML
        )
        # I opened a div here but I'll close it later (after displaying all 3 CVEs)

        # =====================================================================
        # LOOP THROUGH AND DISPLAY EACH CVE
        # =====================================================================
        # I have 3 CVEs to display, so I loop through the list
        for cve in cve_data:
            # Each time through the loop, 'cve' is one CVE dictionary

            # Pick a color for this CVE's border
            severity = cve.get('severity', 'UNKNOWN')
            if severity in ['CRITICAL', 'HIGH']:
                color = '#ef4444'  # Red
            elif severity == 'MEDIUM':
                color = '#f59e0b'  # Orange
            else:
                color = '#10b981'  # Green

            # Build the URL so users can click to see full details
            cve_id = cve['id']
            cve_url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            # Every CVE has a details page on the NVD website
            # I just insert the CVE ID into the URL

            # Display this CVE as a clickable card
            # I use HTML to create a card with the CVE info that links to the NVD page
            st.markdown(
                f"""
                <a href='{cve_url}' target='_blank' style='text-decoration: none;'>
                    <div style='
                        background: #1a1a1a;
                        border-left: 3px solid {color};
                        padding: 8px 10px;
                        margin-bottom: 8px;
                        border-radius: 4px;
                        transition: background 0.2s;
                    '>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>
                            <span style='font-size: 13px; font-weight: bold; color: white;'>{cve_id}</span>
                            <span style='font-size: 11px; color: {color};'>{severity} ({cve['cvss_score']})</span>
                        </div>
                        <div style='font-size: 11px; color: #999;'>{cve['published']}</div>
                    </div>
                </a>
                """,
                # The card layout:
                # - Left side: CVE ID in white
                # - Right side: Severity and score in colored text
                # - Bottom: Published date in gray
                # - Left border: Colored bar (red/orange/green)
                # - Whole thing is clickable and opens NVD in new tab
                unsafe_allow_html=True
            )
            # This loop repeats for each CVE (3 times total)

        # =====================================================================
        # CLOSE THE WIDGET CONTAINER
        # =====================================================================
        # I opened a div earlier for the widget container, now I close it
        st.markdown("</div>", unsafe_allow_html=True)

        # =====================================================================
        # ADD "VIEW ALL" LINK
        # =====================================================================
        # I add a link so users can see ALL Ubiquiti CVEs, not just the 3 I show
        st.markdown(
            """
            <div style='text-align: center; margin-top: 10px;'>
                <a href='https://nvd.nist.gov/vuln/search#/nvd/home?keyword=Ubiquiti&resultType=records'
                   target='_blank'
                   style='
                       color: #00d4ff;
                       text-decoration: none;
                       font-size: 12px;
                       font-weight: 500;
                   '>
                    View All Ubiquiti CVEs on NVD
                </a>
            </div>
            """,
            # Centered link in cyan color (matches my dashboard theme)
            # Opens NVD's search page for all Ubiquiti CVEs in a new tab
            unsafe_allow_html=True
        )

    else:
        # =====================================================================
        # ERROR CASE - API DIDN'T RETURN DATA
        # =====================================================================
        # If I get here, the API call failed or returned no CVEs
        # I show an error message so the widget space isn't just blank

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
                CVE data unavailable
            </div>
            """,
            # Simple error box - same style as the widget but with gray text
            # This tells users the API isn't responding (not a dashboard problem)
            unsafe_allow_html=True
        )

# ----------------------------------------------------------------------------
# MAIN DASHBOARD TITLE
# ----------------------------------------------------------------------------
st.title("Ubiquiti Network Monitor")
# I'm using st.title() to create my main dashboard heading
# This is the big title at the top that tells users what they're looking at

st.markdown("### Real-time Traffic Simulation")
# I'm adding a subheading to explain this is simulated data
# I use ### to make it smaller than the main title
# My professor said it's important to clarify this is demo data, not real

# ============================================================================
# STEP 5: FETCH CURRENT DEVICE DATA
# ============================================================================
# I'm calling my traffic generator to get the current device data
# This updates all the simulated traffic, device statuses, and timestamps
# It returns a list of dictionaries (one dictionary per device)
devices = st.session_state.traffic_generator.get_devices()

# ============================================================================
# STEP 6: PROCESS AND TRANSFORM RAW DEVICE DATA
# ============================================================================
# I'm taking my device data and transforming it into a more usable format
# My data generator gives me a list of dictionaries (one per device)
# I'm converting it to a pandas DataFrame so I can do calculations easier

df = pd.DataFrame(devices)
# I'm using pd.DataFrame() to convert my list of dicts into a table
# This makes it way easier to work with the data
# I can now use pandas methods like .sum(), .filter(), etc.
# Example: [{'name': 'PC', 'download_bytes': 5000000}, ...] becomes a table

# ----------------------------------------------------------------------------
# SUBSECTION 6A: UNIT CONVERSION (BYTES TO MEGABYTES)
# ----------------------------------------------------------------------------
# I'm converting the traffic from bytes to megabytes
# Bytes are too small to read easily (like 5,242,880 bytes)
# Megabytes are much cleaner (5.00 MB)

df['Download (MB)'] = df['download_bytes'] / (1024 * 1024)
# I'm dividing by 1024 twice (not 1,000,000)
# My professor taught us that computers use binary:
#   - 1 KB = 1,024 bytes (not 1,000)
#   - 1 MB = 1,024 KB = 1,048,576 bytes total
# This creates a new column in my DataFrame with the MB values
# The original bytes column stays there too

df['Upload (MB)'] = df['upload_bytes'] / (1024 * 1024)
# Same conversion for upload traffic
# Now I have both bytes and MB columns to work with

# ----------------------------------------------------------------------------
# SUBSECTION 6B: DATA FILTERING BASED ON USER SELECTION
# ----------------------------------------------------------------------------
# I'm filtering my data based on what the user picked in the dropdown
# If they picked a specific device, I only show that device's data
# If they picked "All Devices", I show everything

if selected_device != "All Devices":
    # User picked a specific device
    # I need to filter my DataFrame to just that one device

    df_filtered = df[df['name'] == selected_device].copy()
    # I'm creating a boolean mask where True = name matches
    # Then I use that mask to filter the DataFrame
    # .copy() makes a new DataFrame so I don't accidentally modify the original

    # I'm extracting that device's full info for the details panel
    if len(df_filtered) > 0:
        # I'm checking that the device actually exists in my data

        selected_device_data = df_filtered.iloc[0].to_dict()
        # iloc[0] gets the first row (should be only 1 row since I filtered by name)
        # .to_dict() converts it to a dictionary so I can access fields easily
        # This gives me all the device info: IP, MAC, status, etc.
    else:
        # Device doesn't exist (this shouldn't happen but I'm being safe)
        selected_device_data = None
else:
    # User picked "All Devices" - I show everything
    df_filtered = df.copy()
    # I'm copying the whole DataFrame
    # I do .copy() so I keep my code consistent (always use df_filtered)

    selected_device_data = None
    # No single device to show details for

# ----------------------------------------------------------------------------
# SUBSECTION 6C: CALCULATE AGGREGATE STATISTICS
# ----------------------------------------------------------------------------
# I'm calculating summary stats that I'll display at the top of my dashboard
# These calculations use my filtered data, so they change based on user selection

total_devices = len(df_filtered[df_filtered['status'] == 'ONLINE'])
# I'm counting how many online devices there are
# I create a boolean mask for devices with status=='ONLINE'
# Then I count how many rows match
# If viewing all devices: this is total online devices
# If viewing one device: this is 1 (if online) or 0 (if offline)

total_download = df_filtered['Download (MB)'].sum()
# I'm adding up all the download traffic
# .sum() adds all values in that column
# For "All Devices": this is total network traffic
# For single device: this is that device's traffic

total_upload = df_filtered['Upload (MB)'].sum()
# Same idea but for upload traffic

# ----------------------------------------------------------------------------
# SUBSECTION 6D: EXTRACT CURRENT SPEEDS FOR LIVE DISPLAY
# ----------------------------------------------------------------------------
# I'm getting the current speeds (not cumulative totals)
# These are the live MB/s values I show in the big speed cards

current_download_speed = df_filtered['current_download_speed'].sum()
# This is the current download speed from my data generator
# It represents what's happening right now (not total over time)
# I use .sum() to add up all devices (for "All Devices" view)
# For single device view, it's just that device's speed

current_upload_speed = df_filtered['current_upload_speed'].sum()
# Same thing but for upload speed

# ----------------------------------------------------------------------------
# SUBSECTION 6E: TRAFFIC HISTORY TRACKING (PER-DEVICE)
# ----------------------------------------------------------------------------
# I'm tracking historical speed data for each device over time
# This is what I use for my 30-minute throughput graph
# I store it in session_state so it doesn't reset on every refresh

if 'device_traffic_history' not in st.session_state:
    # First time running - I need to create the storage structure
    st.session_state.device_traffic_history = {}
    # This will be a dictionary of dictionaries:
    # Each device name is a key, value is another dict with timestamps and speeds

# I'm getting the current time to timestamp this data point
current_time = datetime.now()
# This gives me the exact current date and time
# I need this so I can plot my data on a time axis

# I'm looping through each device to record its current speed
for _, device in df.iterrows():
    # df.iterrows() lets me loop through the DataFrame row by row
    # I don't need the index so I use _ to ignore it
    # device is like a dictionary with all the columns for that row

    device_name = device['name']
    # I'm getting this device's name to use as a key

    if device_name not in st.session_state.device_traffic_history:
        # First time seeing this device - I need to create its history
        st.session_state.device_traffic_history[device_name] = {
            'timestamps': [],           # I'll store datetime objects here
            'download_speeds': [],      # I'll store download speeds here
            'upload_speeds': []         # I'll store upload speeds here
        }
        # These lists start empty and grow over time

    # I'm adding the current data point to this device's history
    st.session_state.device_traffic_history[device_name]['timestamps'].append(current_time)
    st.session_state.device_traffic_history[device_name]['download_speeds'].append(device['current_download_speed'])
    st.session_state.device_traffic_history[device_name]['upload_speeds'].append(device['current_upload_speed'])
    # .append() adds to the end of the list
    # All three lists stay the same length (synchronized)

    # -------------------------------------------------------------------------
    # REMOVING OLD DATA (OLDER THAN 30 MINUTES)
    # -------------------------------------------------------------------------
    # I need to delete old data or my lists would grow forever
    # My graph only shows 30 minutes anyway

    cutoff_time = current_time - timedelta(minutes=30)
    # timedelta(minutes=30) is a 30-minute duration
    # I subtract it from now to get the cutoff time
    # Example: If now is 6:00 PM, cutoff is 5:30 PM

    history = st.session_state.device_traffic_history[device_name]
    # I'm getting this device's history so I can clean it up

    valid_indices = [i for i, t in enumerate(history['timestamps']) if t >= cutoff_time]
    # I'm finding which data points are still within the 30-minute window
    # enumerate gives me (index, value) pairs
    # I keep only indices where timestamp >= cutoff
    # This gives me a list of indices to keep

    # I'm rebuilding the lists with only the valid indices
    history['timestamps'] = [history['timestamps'][i] for i in valid_indices]
    history['download_speeds'] = [history['download_speeds'][i] for i in valid_indices]
    history['upload_speeds'] = [history['upload_speeds'][i] for i in valid_indices]
    # These list comprehensions create new lists with only recent data
    # This removes the old data from the front of the lists
    # All three lists stay synchronized (same valid_indices)

# ----------------------------------------------------------------------------
# SUBSECTION 6F: TRAFFIC HISTORY TRACKING (ALL DEVICES COMBINED)
# ----------------------------------------------------------------------------
# I'm also tracking the combined traffic for ALL devices together
# This is what I show when the user picks "All Devices" in the dropdown

if 'traffic_history' not in st.session_state:
    # First run - I need to initialize this
    st.session_state.traffic_history = {
        'timestamps': [],
        'download_speeds': [],
        'upload_speeds': []
    }
    # Same structure as the per-device history

# I'm calculating the total network speeds right now
all_download_speed = df['current_download_speed'].sum()
all_upload_speed = df['current_upload_speed'].sum()
# I use .sum() to add up ALL devices (not the filtered data)
# This is the total bandwidth for my whole network

# I'm adding this data point to the overall history
st.session_state.traffic_history['timestamps'].append(current_time)
st.session_state.traffic_history['download_speeds'].append(all_download_speed)
st.session_state.traffic_history['upload_speeds'].append(all_upload_speed)
# Same pattern as the per-device history

# I'm removing old data (older than 30 minutes)
cutoff_time = current_time - timedelta(minutes=30)
valid_indices = [i for i, t in enumerate(st.session_state.traffic_history['timestamps']) if t >= cutoff_time]
st.session_state.traffic_history['timestamps'] = [st.session_state.traffic_history['timestamps'][i] for i in valid_indices]
st.session_state.traffic_history['download_speeds'] = [st.session_state.traffic_history['download_speeds'][i] for i in valid_indices]
st.session_state.traffic_history['upload_speeds'] = [st.session_state.traffic_history['upload_speeds'][i] for i in valid_indices]

# ----------------------------------------------------------------------------
# SUBSECTION 6G: SECURITY ALERT COLLECTION
# ----------------------------------------------------------------------------
# I'm collecting security alerts from my data generator
# These are fake alerts (port scans, malware, etc.) to make my demo realistic

new_alerts = st.session_state.traffic_generator.generate_security_alerts()
# My data generator has a 20% chance of creating alerts each refresh
# It returns a list of alert dictionaries
# If no alerts, it returns an empty list []

if new_alerts:
    # If there are new alerts, I need to add them to my list

    st.session_state.security_alerts = new_alerts + st.session_state.security_alerts
    # I'm putting the new alerts at the BEGINNING of my list
    # This way newest alerts appear first when I display them
    # The + operator concatenates the lists

# I'm limiting my alert list to 50 alerts max
st.session_state.security_alerts = st.session_state.security_alerts[:50]
# [:50] keeps only the first 50 alerts
# If I have less than 50, nothing happens
# If I have more than 50, the old ones get discarded
# This stops my list from growing forever and using too much memory

# ============================================================================
# STEP 6.5: DEVICE DETAILS (Single Device View Only)
# ============================================================================
# I'm showing detailed device info when the user picks a specific device
# This only appears for single devices, not "All Devices" view

if selected_device != "All Devices" and selected_device_data:
    # I check two things:
    #   1. User picked a specific device (not "All Devices")
    #   2. AND I successfully found that device's data
    # Both have to be true for this to run

    st.markdown(f"### {selected_device}")
    # I'm displaying the device name as a heading
    # The f-string inserts the actual device name

    # I'm creating 4 columns for my detail cards
    detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)
    # st.columns(4) creates 4 equal-width columns (25% each)
    # I'll put one info card in each column

    # -------------------------------------------------------------------------
    # DETAIL CARD 1: IP ADDRESS
    # -------------------------------------------------------------------------
    with detail_col1:
        # Everything in this 'with' block goes in the first column

        st.markdown(
            f"""
            <div style='
                background: #1a1a1a;
                border: 1px solid #00d4ff;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            '>
                <div style='color: #888; font-size: 12px; margin-bottom: 5px;'>IP ADDRESS</div>
                <div style='color: white; font-size: 16px; font-weight: bold;'>{selected_device_data['ip']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # I'm using HTML/CSS to create a custom card
        # My styling:
        #   - Dark background to match my theme
        #   - Cyan border (matches download color)
        #   - Rounded corners
        #   - Centered text
        # The card shows "IP ADDRESS" label on top and the actual IP below
        # This is the device's local network IP (like 192.168.1.5)

    # -------------------------------------------------------------------------
    # DETAIL CARD 2: MAC ADDRESS
    # -------------------------------------------------------------------------
    with detail_col2:
        # This goes in the second column

        st.markdown(
            f"""
            <div style='
                background: #1a1a1a;
                border: 1px solid #a855f7;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            '>
                <div style='color: #888; font-size: 12px; margin-bottom: 5px;'>MAC ADDRESS</div>
                <div style='color: white; font-size: 16px; font-weight: bold;'>{selected_device_data['mac']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Same structure but with purple border (matches upload color)
        # MAC address is the hardware ID burned into the network card
        # Format is like AA:BB:CC:DD:EE:FF (6 pairs of hex digits)
        # This can't be changed - it's like a serial number for the network card

    # -------------------------------------------------------------------------
    # DETAIL CARD 3: CONNECTION TYPE
    # -------------------------------------------------------------------------
    with detail_col3:
        # This goes in the third column

        # I'm picking a color based on the connection type
        if selected_device_data['connection_type'] == "Wired":
            connection_color = "#00d4ff"  # Cyan for wired
        else:
            connection_color = "#a855f7"  # Purple for Wi-Fi
        # I broke this out instead of using a ternary operator
        # My professor said simpler code is better even if it's longer

        st.markdown(
            f"""
            <div style='
                background: #1a1a1a;
                border: 1px solid {connection_color};
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            '>
                <div style='color: #888; font-size: 12px; margin-bottom: 5px;'>CONNECTION</div>
                <div style='color: white; font-size: 16px; font-weight: bold;'>{selected_device_data['connection_type']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # The border color changes based on connection type
        # Wired gets cyan, Wi-Fi gets purple
        # Shows whether device is plugged in (Wired) or wireless (Wi-Fi)

    # -------------------------------------------------------------------------
    # DETAIL CARD 4: STATUS
    # -------------------------------------------------------------------------
    with detail_col4:
        # This goes in the fourth column

        # I'm picking a color based on online/offline status
        if selected_device_data['status'] == "ONLINE":
            status_color = "#10b981"  # Green for online
        else:
            status_color = "#ef4444"  # Red for offline
        # Green means good (online), red means bad (offline)

        st.markdown(
            f"""
            <div style='
                background: #1a1a1a;
                border: 1px solid {status_color};
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            '>
                <div style='color: #888; font-size: 12px; margin-bottom: 5px;'>STATUS</div>
                <div style='color: {status_color}; font-size: 16px; font-weight: bold;'>{selected_device_data['status']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # The status text itself is colored (not just the border)
        # "ONLINE" appears green, "OFFLINE" appears red
        # This gives instant visual feedback on device state

    st.markdown("---")
    # I'm adding a horizontal line to separate sections
    # Makes the layout cleaner

# ============================================================================
# STEP 7: DISPLAY METRICS (TOP ROW)
# ============================================================================
# I'm showing summary statistics at the top of my dashboard
# These give users a quick overview of the network status
# The numbers change based on what the user selected in the dropdown

# I'm creating 3 columns for my metric cards
col1, col2, col3 = st.columns(3)
# st.columns(3) splits the width into three equal parts
# Each column gets one metric card

# I'm displaying the three metrics
col1.metric("Connected Devices", total_devices)
# This shows how many devices are currently online
# I calculated this number earlier in STEP 6C
# For "All Devices": shows total online devices
# For single device: shows 1 (online) or 0 (offline)

col2.metric("Total Download", f"{total_download:.2f} MB")
# This shows the cumulative download traffic
# I'm using an f-string with :.2f to format to 2 decimal places
# So 156.789 becomes "156.79 MB"
# This is the total downloaded (not current speed)

col3.metric("Total Upload", f"{total_upload:.2f} MB")
# Same idea but for upload traffic
# Upload is usually lower than download
# Most internet connections are asymmetric (more download than upload)

# ============================================================================
# STEP 7.25: LIVE THROUGHPUT DISPLAY
# ============================================================================
# I'm showing the CURRENT network speeds (not totals)
# These are the live speeds happening right now
# Measured in Mbps (megabits per second)

st.markdown("### Live Throughput")
# I'm adding a heading for this section
# "Live" tells users this is real-time, not historical

# I'm creating 2 columns for download and upload speeds
throughput_col1, throughput_col2 = st.columns(2)
# 50/50 split for side-by-side display
# Download on left, upload on right

# ----------------------------------------------------------------------------
# LIVE DOWNLOAD SPEED CARD
# ----------------------------------------------------------------------------
with throughput_col1:
    # This goes in the left column

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
    # I'm using HTML/CSS for a custom card with cyan styling
    # I made the font size really big (36px) so users can see it easily
    # The speed is in Mbps (megabits per second)
    # Note: Mbps is different from MB/s (megabytes per second)
    # 8 Mbps = 1 MB/s because 1 byte = 8 bits
    # ISPs use Mbps because the numbers are bigger

# ----------------------------------------------------------------------------
# LIVE UPLOAD SPEED CARD
# ----------------------------------------------------------------------------
with throughput_col2:
    # This goes in the right column

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
    # Same structure but with purple color (matches upload theme)
    # Side-by-side lets users compare download vs upload easily
    # Upload is typically much lower than download

# ============================================================================
# STEP 7.5: NETWORK SPEED GRAPH (30-MINUTE HISTORY)
# ============================================================================
# I'm creating a graph that shows network speeds over the last 30 minutes
# This lets users see trends and patterns in their network usage
# I'm tracking this data in STEP 6E (per device) and STEP 6F (all devices)

st.markdown("### Network Throughput (Last 30 Minutes)")
# I'm adding a heading for the graph section
# The "Last 30 Minutes" tells users the time window

# I'm picking which history data to show
if selected_device != "All Devices" and selected_device in st.session_state.device_traffic_history:
    # User picked a specific device AND I have history for it
    # So I show just that device's traffic

    history_data = st.session_state.device_traffic_history[selected_device]
    # This gets me the timestamps and speeds for just this device
else:
    # Either user picked "All Devices" OR the device doesn't have history yet
    # So I show the combined network traffic

    history_data = st.session_state.traffic_history
    # This has the summed-up traffic from all devices

# I only show the graph if I have data to plot
if len(history_data['timestamps']) > 0:
    # I'm checking if there's any data collected yet
    # On first run the lists are empty
    # After a few refreshes I'll have data points to graph
    # -------------------------------------------------------------------------
    # CREATE PLOTLY FIGURE OBJECT
    # -------------------------------------------------------------------------
    fig_speed = go.Figure()
    # I'm creating an empty Plotly graph
    # This is like a blank canvas I'll add lines to
    # I'm using go.Figure() which gives me more control than plotly.express

    # -------------------------------------------------------------------------
    # ADD DOWNLOAD SPEED LINE (CYAN)
    # -------------------------------------------------------------------------
    fig_speed.add_trace(go.Scatter(
        # I'm adding a line for download speeds
        # go.Scatter can make scatter plots or line plots

        x=history_data['timestamps'],
        # x-axis is time
        # This is my list of datetime objects
        # Plotly formats these nicely as time labels

        y=history_data['download_speeds'],
        # y-axis is speed in MB/s
        # This is my list of download speeds
        # Each speed corresponds to a timestamp (same index)

        mode='lines',
        # I'm using 'lines' mode to connect the points
        # This makes a smooth line chart
        # I could use 'markers' for dots or 'lines+markers' for both

        name='Download',
        # This is the label that shows in the legend
        # Users can click it to hide/show the line

        line=dict(color='#00d4ff', width=2),
        # I'm styling the line cyan (#00d4ff) to match my download theme
        # width=2 makes it 2 pixels thick
        # dict() creates the styling dictionary

        fill='tozeroy',
        # I'm filling the area under the line
        # 'tozeroy' means fill down to the x-axis (y=0)
        # This makes it look like professional dashboards

        fillcolor='rgba(0, 212, 255, 0.2)'
        # I'm making the fill cyan but transparent (20% opacity)
        # rgba is Red, Green, Blue, Alpha (transparency)
        # I need transparency so you can see both fills when they overlap
    ))

    # -------------------------------------------------------------------------
    # ADD UPLOAD SPEED LINE (PURPLE)
    # -------------------------------------------------------------------------
    fig_speed.add_trace(go.Scatter(
        # I'm adding a second line for upload speeds
        # Both lines show on the same graph

        x=history_data['timestamps'],
        # Same timestamps as download (shared time axis)

        y=history_data['upload_speeds'],
        # Upload speeds (usually lower than download)

        mode='lines',
        # Same line mode

        name='Upload',
        # This shows "Upload" in the legend

        line=dict(color='#a855f7', width=2),
        # I'm using purple for upload (consistent with my theme)
        # Same 2px width as download

        fill='tozeroy',
        # Fill under this line too

        fillcolor='rgba(168, 85, 247, 0.2)'
        # Purple fill at 20% opacity
        # RGB values match the purple hex color
    ))

    # -------------------------------------------------------------------------
    # CONFIGURE GRAPH LAYOUT AND STYLING
    # -------------------------------------------------------------------------
    fig_speed.update_layout(
        # I'm configuring how the graph looks overall
        # This controls the axes, legend, size, etc.

        xaxis_title="Time",
        # Label for the x-axis (horizontal)
        # Tells users this axis is time

        yaxis_title="Speed (MB/s)",
        # Label for the y-axis (vertical)
        # MB/s = megabytes per second

        hovermode='x unified',
        # I'm setting how tooltips work when you hover
        # 'x unified' shows both download and upload in one tooltip
        # This way users can see both speeds at the same time

        height=400,
        # I'm setting the graph height to 400 pixels
        # This makes it big enough to see but doesn't take over the page

        margin=dict(l=0, r=0, t=0, b=0),
        # I'm setting all margins to 0
        # Streamlit adds its own padding so I don't need extra
        # dict creates the margin dictionary

        legend=dict(
            # I'm configuring the legend box

            orientation="h",
            # "h" means horizontal (items side-by-side)
            # This saves vertical space

            yanchor="bottom",
            # This sets the anchor point for positioning

            y=1.02,
            # I'm placing it slightly above the graph
            # 1.0 = top of graph, 1.02 = a bit above
            # This way it doesn't cover my data

            xanchor="right",
            # Anchor for horizontal positioning

            x=1
            # I'm placing it at the right edge
            # Combined with the anchors, this puts it top-right
        )
    )

    # -------------------------------------------------------------------------
    # DISPLAY THE COMPLETED GRAPH
    # -------------------------------------------------------------------------
    st.plotly_chart(fig_speed, use_container_width=True)
    # I'm displaying the graph I created
    # use_container_width=True makes it fill the available width
    # Plotly charts are interactive:
    #   - Hover to see values
    #   - Click legend to hide/show lines
    #   - Drag to zoom, double-click to reset

else:
    # This runs if I don't have any data yet
    # Happens on first load before any refreshes

    st.info("Collecting data... Graph will appear after a few updates.")
    # I'm showing a message so users know why the graph isn't there yet
    # After a few refreshes I'll have data and the graph will show

# ============================================================================
# STEP 8: DEVICES CURRENTLY CONNECTED
# ============================================================================
# I'm showing a table with all the device information
# This is an interactive table users can sort and scroll
# The table changes based on whether they picked "All Devices" or a single device

# I'm changing the header based on what's selected
if selected_device != "All Devices":
    # User picked one device - use singular
    st.subheader("Current Device")
    # "Current" makes it clear this is the one they picked
else:
    # User is viewing all devices - use plural
    st.subheader("Devices Currently Connected")
    # This tells users they're seeing all connected devices

# I'm selecting which columns to show in the table
# My DataFrame has lots of columns but I don't need all of them
display_df = df_filtered[[
    # I'm using double brackets to select multiple columns
    # This returns a new DataFrame with just these columns

    'name',              # Device name like "Home PC" or "iPhone"
    'type',              # Device type (Desktop, Mobile, Tablet, IoT)
    'ip',                # Local network IP address
    'mac',               # MAC address (hardware ID)
    'connection_type',   # Wired or Wi-Fi
    'status',            # ONLINE or OFFLINE
    'Download (MB)',     # Total download traffic
    'Upload (MB)',       # Total upload traffic
    'last_seen'          # Last activity timestamp
]]
# These 9 columns have all the important info users need
# The order here is the order they appear left to right

# I'm displaying the table
st.dataframe(
    # st.dataframe() creates an interactive table
    # Users can sort by clicking column headers

    display_df,
    # This is the DataFrame I created above with 9 columns

    use_container_width=True,
    # This makes the table fill the available width
    # Without this it would be narrow and hard to read

    column_config={
        # I'm customizing how each column looks

        "name": "Device Name",
        # Renaming for clarity

        "type": "Type",
        # Capitalizing it

        "ip": "IP Address",
        # Expanding the abbreviation

        "mac": "MAC Address",
        # MAC = Media Access Control

        "connection_type": "Connection",
        # Shortening to save space

        "status": "Status",
        # This is already clear

        "Download (MB)": st.column_config.NumberColumn("Download (MB)", format="%.2f MB"),
        # I'm using NumberColumn to format the numbers nicely
        # %.2f means 2 decimal places
        # So 5.234567 becomes "5.23 MB"

        "Upload (MB)": st.column_config.NumberColumn("Upload (MB)", format="%.2f MB"),
        # Same formatting for upload

        "last_seen": "Last Seen"
        # Making it look nicer with capitals and space
    },

    hide_index=True
    # I'm hiding the row numbers (0, 1, 2...)
    # They're not useful here and make the table cluttered
)

# ============================================================================
# STEP 9: GLOBAL TRAFFIC MAP (PLOTLY) - Only show for "All Devices"
# ============================================================================
# I'm creating a world map showing where external servers are located
# This only shows for "All Devices" view (not single device)
# It helps users see if connections are coming from unexpected places

if selected_device == "All Devices":
    # Map only shows for "All Devices" view
    # It doesn't make sense for single device view

    st.markdown("### Global Traffic Origins")
    # I'm adding a heading for the map section

    st.markdown("Live map of external servers communicating with your network.")
    # I'm explaining what the map shows
    # External servers = computers outside the local network
    # Like websites, cloud services, etc.

    # -------------------------------------------------------------------------
    # FETCH CONNECTION DATA
    # -------------------------------------------------------------------------
    connections = st.session_state.traffic_generator.generate_external_connections()
    # I'm getting fake connection data from my data generator
    # Each connection has a latitude and longitude
    # My generator makes realistic distribution:
    #   - 50% United States (most traffic)
    #   - 10% China
    #   - 10% Russia
    #   - 30% European Union
    # This simulates real global internet patterns

    # I'm converting to a DataFrame for Plotly
    map_df = pd.DataFrame(connections)
    # Plotly needs DataFrame format (not list of dicts)
    # This creates a table with 'lat' and 'lon' columns
    # Each row is one connection point on the map

    # -------------------------------------------------------------------------
    # CREATE PLOTLY GEOGRAPHIC SCATTER PLOT
    # -------------------------------------------------------------------------
    fig = px.scatter_geo(
        # I'm creating a scatter plot on a world map
        # px.scatter_geo() is from plotly.express (easier to use)
        # Each connection appears as a dot on the map

        map_df,
        # My DataFrame with lat/lon data

        lat='lat',
        # Column name for latitude
        # Latitude goes from -90 (South Pole) to +90 (North Pole)

        lon='lon',
        # Column name for longitude
        # Longitude goes from -180 (West) to +180 (East)

        projection='equirectangular',
        # This is the map projection (how I flatten the globe to 2D)
        # equirectangular is a simple rectangular grid
        # It's familiar looking but distorts size near the poles

        title='',
        # No title because I already added one with st.markdown()

        height=450
        # Map height in pixels
        # 450px is big enough to see but doesn't dominate the page
    )

    # -------------------------------------------------------------------------
    # CUSTOMIZE MAP MARKER APPEARANCE
    # -------------------------------------------------------------------------
    fig.update_traces(
        # I'm customizing how the connection dots look

        marker=dict(
            # marker is a dictionary with styling options

            size=10,
            # Each dot is 10 pixels wide
            # Big enough to see but not too big

            color='#00d4ff',
            # Cyan color (matches my download theme)

            opacity=0.8,
            # 80% opaque, 20% transparent
            # Transparency lets you see overlapping dots

            line=dict(
                # Border around each dot

                width=1,
                # Thin 1px border

                color='white'
                # White border makes dots stand out against the dark map
            )
        )
    )

    # -------------------------------------------------------------------------
    # CUSTOMIZE MAP GEOGRAPHY (LAND, OCEAN, BORDERS)
    # -------------------------------------------------------------------------
    fig.update_geos(
        # I'm customizing how the map itself looks

        showcountries=True,
        # Show country borders

        countrycolor="rgba(100, 100, 100, 0.3)",
        # Gray borders at 30% opacity
        # Subtle so they don't compete with my cyan dots

        showcoastlines=True,
        # Show coastlines

        coastlinecolor="rgba(255, 255, 255, 0.3)",
        # White coastlines at 30% opacity
        # Slightly brighter than country borders

        showland=True,
        # Show land masses

        landcolor="rgba(30, 30, 30, 0.8)",
        # Very dark gray for land
        # Matches my dark theme

        showocean=True,
        # Show oceans

        oceancolor="rgba(10, 10, 30, 0.9)",
        # Even darker for oceans
        # Slight blue tint to distinguish from land

        projection_type='equirectangular',
        # Reinforcing the projection type

        bgcolor='rgba(0,0,0,0)'
        # Transparent background so Streamlit's background shows through
    )

    # -------------------------------------------------------------------------
    # CONFIGURE OVERALL FIGURE LAYOUT
    # -------------------------------------------------------------------------
    fig.update_layout(
        # I'm setting the overall layout styling

        paper_bgcolor='rgba(0,0,0,0)',
        # Transparent background for the outer area

        plot_bgcolor='rgba(0,0,0,0)',
        # Transparent background for the plot area

        geo=dict(bgcolor='rgba(0,0,0,0)')
        # Transparent background for the geo layer
        # All transparent so it integrates nicely with Streamlit
    )

    # -------------------------------------------------------------------------
    # DISPLAY THE COMPLETED MAP
    # -------------------------------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)
    # I'm displaying the map
    # use_container_width=True makes it fill the available width
    # The map is interactive:
    #   - Hover to see coordinates
    #   - Zoom and pan
    #   - Reset with the home button
    # This helps users see if traffic is coming from unexpected places

# ============================================================================
# STEP 8.5: SECURITY ALERTS TABLE
# ============================================================================
# I'm displaying security warnings for suspicious network activity
# These are simulated alerts (port scans, malware, etc.) from my data generator
# The table filters based on what device the user selected

st.markdown("### Suspicious Traffic Alerts")
# I'm adding a heading for the security alerts section
# "Suspicious" tells users these might be security problems

# -------------------------------------------------------------------------
# FILTER ALERTS BASED ON DEVICE SELECTION
# -------------------------------------------------------------------------
if selected_device != "All Devices":
    # User picked a specific device - show only that device's alerts
    # This helps them focus on one device's security

    filtered_alerts = [alert for alert in st.session_state.security_alerts if alert['device'] == selected_device]
    # I'm using a list comprehension to filter
    # This loops through all alerts and keeps only ones for this device
    # More compact than writing a for loop with if statement and append
else:
    # User is viewing "All Devices" - show all alerts
    filtered_alerts = st.session_state.security_alerts
    # No filtering needed - use the full list

# -------------------------------------------------------------------------
# DISPLAY ALERTS IF ANY EXIST
# -------------------------------------------------------------------------
if filtered_alerts:
    # I'm checking if there are any alerts to show
    # Empty list is "falsy" so this won't run if no alerts
    # -------------------------------------------------------------------------
    # CONVERT ALERTS TO DATAFRAME
    # -------------------------------------------------------------------------
    alerts_df = pd.DataFrame(filtered_alerts)
    # I'm converting my list of alert dictionaries to a DataFrame
    # This makes it easier to display and format

    # -------------------------------------------------------------------------
    # FORMAT TIMESTAMP FOR READABILITY
    # -------------------------------------------------------------------------
    alerts_df['Time'] = alerts_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # I'm creating a nicely formatted time column
    # .dt.strftime() lets me format datetime objects
    # The format is Year-Month-Day Hour:Minute:Second
    # Example: "2025-11-30 17:45:23"

    # -------------------------------------------------------------------------
    # SELECT AND RENAME COLUMNS FOR DISPLAY
    # -------------------------------------------------------------------------
    display_alerts = alerts_df[['Time', 'device', 'external_ip', 'reason', 'severity']]
    # I'm selecting just the columns I want to show
    # Time first, then device, external IP, alert type, severity

    display_alerts.columns = ['Time', 'Device', 'External IP', 'Alert Type', 'Severity']
    # I'm renaming the columns to look more professional
    # 'reason' becomes 'Alert Type' which is clearer

    # -------------------------------------------------------------------------
    # DEFINE SEVERITY HIGHLIGHTING FUNCTION
    # -------------------------------------------------------------------------
    def highlight_severity(row):
        # I'm creating a function to color-code rows by severity
        # This gets called for each row in the table

        if row['Severity'] == 'High':
            # High severity = red highlighting
            return ['background-color: #fee2e2; color: #991b1b'] * len(row)
            # Light red background, dark red text
            # * len(row) applies this to every column in the row

        elif row['Severity'] == 'Medium':
            # Medium severity = yellow highlighting
            return ['background-color: #fef3c7; color: #92400e'] * len(row)
            # Light yellow background, dark orange text

        else:
            # Low severity = no special styling
            return [''] * len(row)
            # Empty string means default styling

    # -------------------------------------------------------------------------
    # APPLY STYLING TO DATAFRAME
    # -------------------------------------------------------------------------
    styled_df = display_alerts.style.apply(highlight_severity, axis=1)
    # I'm applying my highlighting function to the DataFrame
    # .style creates a Styler object
    # .apply with axis=1 means it runs on each row
    # Now my high/medium alerts will be colored

    # -------------------------------------------------------------------------
    # DISPLAY STYLED ALERTS TABLE
    # -------------------------------------------------------------------------
    st.dataframe(
        # I'm displaying the color-coded alerts table

        styled_df,
        # My styled DataFrame with color coding

        use_container_width=True,
        # Make it fill the available width

        column_config={
            # I'm customizing column widths

            "Time": st.column_config.TextColumn("Time", width="medium"),
            "Device": st.column_config.TextColumn("Device", width="medium"),
            "External IP": st.column_config.TextColumn("External IP", width="medium"),
            "Alert Type": st.column_config.TextColumn("Alert Type", width="large"),
            # Alert type gets large width because descriptions can be long
            "Severity": st.column_config.TextColumn("Severity", width="small")
            # Severity is small because it's just "High", "Medium", or "Low"
        },

        hide_index=True
        # I'm hiding row numbers
    )

    # -------------------------------------------------------------------------
    # ALERT SUMMARY METRICS
    # -------------------------------------------------------------------------
    # I'm adding summary metrics below the table
    # This gives users quick stats about the alerts

    high_alerts = len([a for a in filtered_alerts if a['severity'] == 'High'])
    # I'm counting how many high severity alerts there are
    # Using a list comprehension to filter and count

    medium_alerts = len([a for a in filtered_alerts if a['severity'] == 'Medium'])
    # Same for medium severity

    col_alert1, col_alert2, col_alert3 = st.columns(3)
    # I'm creating 3 columns for my metrics

    col_alert1.metric("Total Alerts", len(filtered_alerts))
    # Total count of all alerts

    col_alert2.metric("High Severity", high_alerts, delta=None, delta_color="inverse")
    # Count of high severity alerts
    # delta=None means no change arrow
    # delta_color="inverse" would make decreases good (not used here)

    col_alert3.metric("Medium Severity", medium_alerts)
    # Count of medium severity alerts

else:
    # This runs if there are no alerts to display
    # Either no alerts exist or the selected device has none

    # -------------------------------------------------------------------------
    # NO ALERTS MESSAGE
    # -------------------------------------------------------------------------
    if selected_device != "All Devices":
        # User is viewing a specific device with no alerts
        st.info(f"No suspicious traffic detected from {selected_device}.")
        # I'm showing a message that includes the device name

    else:
        # User is viewing "All Devices" with no alerts
        st.info("No suspicious traffic detected. Your network appears secure.")
        # I'm showing a generic "all clear" message

# ============================================================================
# STEP 10: AUTO-REFRESH LOGIC
# ============================================================================
# I'm implementing the "Live Updates" feature here
# When enabled, this makes the dashboard automatically refresh
# This is what creates the real-time monitoring effect

if auto_refresh:
    # I'm checking if the user enabled "Enable Live Updates" in the sidebar
    # auto_refresh is the boolean from my checkbox (True or False)
    # If True, I run this code to create the auto-refresh loop

    # -------------------------------------------------------------------------
    # PAUSE EXECUTION
    # -------------------------------------------------------------------------
    time.sleep(refresh_rate)
    # I'm pausing for the number of seconds the user picked with the slider
    # refresh_rate is 1-10 seconds from the sidebar slider
    # This creates a delay between updates
    # Without this pause, the dashboard would refresh crazy fast

    # -------------------------------------------------------------------------
    # TRIGGER COMPLETE SCRIPT RERUN
    # -------------------------------------------------------------------------
    st.rerun()
    # I'm telling Streamlit to restart the script from the top
    # This is how I create the auto-refresh:
    #   1. Script runs from top to bottom
    #   2. Gets to this point and pauses (time.sleep)
    #   3. Then st.rerun() restarts from line 1
    #   4. Repeat forever (or until user unchecks the box)
    #
    # Each time it reruns:
    #   - My data generator creates new fake data
    #   - Traffic history gets new data points
    #   - New security alerts might appear
    #   - All graphs and tables update with fresh data
    #
    # The loop continues until:
    #   - User unchecks "Enable Live Updates"
    #   - User closes the browser
    #   - I stop the Streamlit server
    #
    # My session_state variables (traffic_history, alerts, etc.) persist
    # across reruns so my data accumulates instead of resetting

# ============================================================================
# END OF SCRIPT
# ============================================================================
# If auto_refresh is False (Live Updates disabled):
#   - Script runs once and stops here
#   - Dashboard shows a static snapshot
#   - Only updates when user changes something (dropdown, slider, etc.)
#
# If auto_refresh is True (Live Updates enabled):
#   - st.rerun() is called above
#   - Script never reaches this point
#   - It reruns from the top before getting here
#   - Creates continuous refresh loop