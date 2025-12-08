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
# These imports bring in external libraries that provide functionality
# that Python doesn't have built-in

import streamlit as st
# Streamlit: Framework for building web-based data applications
# Chosen because it allows creating dashboards without HTML/CSS/JavaScript knowledge
# Provides widgets (buttons, sliders) and auto-reloading on code changes

import pandas as pd
# Pandas: Data manipulation library for working with tabular data (like Excel)
# Used here to organize device information into DataFrames (tables)
# Makes it easy to filter, sort, and display network device data

import time
# Time: Built-in Python module for time-related functions
# Used here for the auto-refresh feature - pauses execution between updates
# Allows the dashboard to update at user-defined intervals (1-10 seconds)

import plotly.express as px
# Plotly Express: High-level charting library for creating interactive visualizations
# Used for the geographic map showing global traffic origins
# Chosen over matplotlib because it creates interactive charts (zoom, hover, pan)

import plotly.graph_objects as go
# Plotly Graph Objects: Lower-level Plotly library for custom chart creation
# Used for the network throughput graph with custom styling
# Allows more control over colors, fills, and layout than plotly.express

from datetime import datetime, timedelta
# Datetime: Built-in Python module for working with dates and times
# datetime: Gets current time for timestamps on data points
# timedelta: Calculates time differences (used for 30-minute history window)

from data_generator import NetworkTrafficGenerator
# Custom module that simulates network device data
# Generates realistic device names, IP addresses, traffic volumes, security alerts
# This keeps the dashboard demo functional without requiring actual network hardware

from cve_fetcher import CVEFetcher
# Custom module that retrieves CVE vulnerability data from National Vulnerability Database
# Adds security vulnerability tracking for Ubiquiti devices
# Displays latest CVEs related to Ubiquiti and Ubiquiti routers

# ============================================================================
# STEP 1: PAGE CONFIGURATION
# ============================================================================
# IMPORTANT: st.set_page_config() MUST be the first Streamlit command
# If called after other st commands, Streamlit will throw an error
# This is a Streamlit requirement to ensure proper page initialization

st.set_page_config(
    page_title="Ubiquiti Network Dashboard",
    # Sets the text shown in the browser tab
    # Helps users identify the page when multiple tabs are open

    layout="wide"
    # Makes the dashboard use the full browser width instead of a narrow column
    # Critical for displaying multiple charts and tables side-by-side
    # Options are "centered" (default) or "wide"
)

# ============================================================================
# STEP 2: CUSTOM CSS STYLING FOR PROFESSIONAL APPEARANCE
# ============================================================================
# CSS (Cascading Style Sheets) controls the visual presentation of the dashboard
# Streamlit allows injecting custom CSS using st.markdown() with unsafe_allow_html=True
# This overrides Streamlit's default styling to create a cleaner interface

st.markdown("""
    <style>
        /* ================================================================
           SECTION 1: HIDE UNNECESSARY STREAMLIT INTERFACE ELEMENTS
           ================================================================
           Streamlit adds various UI elements by default (status indicators,
           menus, branding). For a professional dashboard, these are hidden
           to create a cleaner, more focused user experience.
        */

        /* Hide the "running" status widget in the top-right corner */
        .stStatusWidget {
            display: none !important;
            /* !important ensures this rule overrides Streamlit's defaults */
            /* This removes the animated running man icon that appears during updates */
        }

        /* Hide the hamburger menu (three dots) in the top-right corner */
        #MainMenu {
            visibility: hidden;
            /* MainMenu contains options like "Rerun", "Settings", "About" */
            /* Hidden because users don't need these options in production */
        }

        /* Hide Streamlit's "Made with Streamlit" footer */
        footer {
            visibility: hidden;
            /* Removes branding footer for a more professional appearance */
            /* Important for class presentation/demo purposes */
        }

        /* Additional targeting for status widgets using data attributes */
        .stApp header + div[data-testid="stStatusWidget"] {
            display: none !important;
            /* data-testid is Streamlit's way of marking specific elements */
            /* This targets status widgets that appear next to the header */
        }

        /* Catch-all for any status widgets missed by previous rules */
        div[data-testid="stStatusWidget"] {
            display: none !important;
            /* Ensures all status indicators are hidden */
        }

        /* Hide the "Deploy" button that Streamlit adds */
        .stDeployButton {
            display: none !important;
            /* Deploy button is for Streamlit Cloud deployment */
            /* Not needed for local/class demo usage */
        }

        /* ================================================================
           SECTION 2: ELIMINATE FADE/DIM ANIMATIONS
           ================================================================
           By default, Streamlit adds fade-in animations when updating content
           This can cause a flickering/dimming effect during auto-refresh
           All animations are disabled for instant, smooth updates
        */

        /* Universal selector (*) applies to ALL HTML elements */
        *, *::before, *::after {
            transition: none !important;
            /* transition creates smooth changes between states (color, size, etc.) */
            /* Setting to 'none' makes all changes instant */

            animation: none !important;
            /* animation creates keyframe-based animations */
            /* Setting to 'none' prevents any animated effects */

            transition-duration: 0s !important;
            animation-duration: 0s !important;
            /* Belt-and-suspenders approach: force duration to zero */
            /* Ensures even if transition/animation is defined, it's instant */
        }

        /* Target core HTML structure elements for opacity control */
        html, body, #root, .stApp, .main, .block-container {
            transition: none !important;
            animation: none !important;
            opacity: 1 !important;
            /* opacity: 1 means fully visible (no transparency) */
            /* Prevents fade-in effects that make content temporarily invisible */
        }

        /* Target all major Streamlit component types */
        .element-container,      /* Generic container for all Streamlit elements */
        .stMarkdown,             /* Markdown text blocks */
        .stDataFrame,            /* DataFrame/table displays */
        .stMetric,               /* Metric cards (number displays) */
        .stPlotlyChart,          /* Plotly charts and graphs */
        div[data-testid="stVerticalBlock"],    /* Vertical layout containers */
        div[data-testid="stHorizontalBlock"],  /* Horizontal layout containers */
        div[data-testid="column"],             /* Individual columns */
        section[data-testid="stSidebar"],      /* Sidebar panel */
        .stSelectbox,            /* Dropdown menus */
        .stSlider,               /* Slider controls */
        .stCheckbox {            /* Checkbox inputs */
            transition: none !important;
            animation: none !important;
            animation-duration: 0s !important;
            animation-delay: 0s !important;    /* Prevents delayed animations */
            transition-delay: 0s !important;   /* Prevents delayed transitions */
            opacity: 1 !important;
            /* All these elements render instantly with no fade effects */
        }

        /* Disable Streamlit's skeleton loading placeholders */
        .stSkeleton {
            display: none !important;
            /* Streamlit shows gray "skeleton" placeholders while loading */
            /* These are hidden for instant content display */
        }

        /* Target the main app view container to prevent page-level fades */
        [data-testid="stAppViewContainer"] {
            transition: none !important;
            animation: none !important;
            opacity: 1 !important;
            /* This is the outermost container of the app content */
            /* Prevents the entire page from fading during reruns */
        }
    </style>
""", unsafe_allow_html=True)
# unsafe_allow_html=True is required because the markdown contains HTML/CSS
# Without this flag, Streamlit would escape the HTML and display it as text
# Security note: Only safe here because the CSS is hardcoded, not user input

# ============================================================================
# STEP 3: SESSION STATE INITIALIZATION
# ============================================================================
# CRITICAL CONCEPT: Understanding Streamlit's Execution Model
# ----------------------------------------------------------
# Streamlit reruns the ENTIRE script from top to bottom on every user interaction
# Examples of interactions that trigger reruns:
#   - Clicking a button
#   - Moving a slider
#   - Selecting from a dropdown
#   - Checking a checkbox
#   - Auto-refresh timer expiring
#
# Problem: Without persistence, variables would reset on every rerun
# Solution: st.session_state - a dictionary that survives across reruns
#
# Think of session_state as "memory" that persists between page refreshes
# It's similar to using global variables, but Streamlit-aware and user-isolated

if 'traffic_generator' not in st.session_state:
    # The 'not in' check prevents recreation on every rerun
    # This block ONLY executes on the first run of the app
    # After that, the object already exists in session_state and is reused

    st.session_state.traffic_generator = NetworkTrafficGenerator()
    # NetworkTrafficGenerator is a class from data_generator.py
    # It maintains simulated device data (names, IPs, MACs, traffic volumes)
    # Creating it once and reusing ensures:
    #   1. Device names stay consistent across refreshes
    #   2. Traffic counters accumulate properly (don't reset)
    #   3. Better performance (don't recreate objects unnecessarily)

if 'cve_fetcher' not in st.session_state:
    # Same pattern: create once, reuse across reruns
    st.session_state.cve_fetcher = CVEFetcher()
    # CVEFetcher is a class from cve_fetcher.py
    # It makes API calls to NVD (National Vulnerability Database) to get CVE data
    # Persisting it allows caching of API responses (avoid rate limits)

if 'traffic_history' not in st.session_state:
    # Initialize the master history for "All Devices" view
    # This will be populated in STEP 6F as the app runs
    st.session_state.traffic_history = {
        'timestamps': [],           # List of datetime objects
        'download_speeds': [],      # List of float values (MB/s)
        'upload_speeds': []         # List of float values (MB/s)
    }
    # Starting with empty lists - they'll be filled by subsequent code
    # These lists grow over time (up to 30 minutes of data)

if 'security_alerts' not in st.session_state:
    # Initialize storage for security alerts
    st.session_state.security_alerts = []
    # Starts as empty list
    # The data generator will populate this with simulated alerts
    # List grows over time (capped at 50 alerts in STEP 6G)

# ============================================================================
# STEP 4: SIDEBAR CONTROLS AND USER INPUTS
# ============================================================================
# The sidebar is the collapsible panel on the left side of the Streamlit dashboard
# It provides an organized location for controls without cluttering the main view
# Sidebar automatically appears on the left and can be collapsed by the user

st.sidebar.title("Controls")
# .title() creates a large heading in the sidebar
# This organizes related controls under a clear header

# ----------------------------------------------------------------------------
# CONTROL 1: AUTO-REFRESH TOGGLE
# ----------------------------------------------------------------------------
# Allows users to enable/disable automatic dashboard updates

auto_refresh = st.sidebar.checkbox("Enable Live Updates", value=False)
# .checkbox() creates a checkbox input widget
# Parameters:
#   - First argument: Label text shown next to the checkbox
#   - value=False: Default state (unchecked when app loads)
# Returns: Boolean (True if checked, False if unchecked)
# Stored in 'auto_refresh' variable for use in STEP 10
# When checked, the dashboard will automatically reload at the specified interval
# When unchecked, dashboard only updates when user manually interacts

# ----------------------------------------------------------------------------
# CONTROL 2: REFRESH RATE SLIDER
# ----------------------------------------------------------------------------
# Lets users control how frequently the dashboard updates (if auto-refresh is on)

refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 1)
# .slider() creates a horizontal slider widget
# Parameters:
#   - First argument: Label text displayed above the slider
#   - 1: Minimum value (left end of slider)
#   - 10: Maximum value (right end of slider)
#   - 1: Default value (starting position)
# Returns: Integer between 1 and 10
# Note: This value is used even when auto_refresh is False (doesn't cause error)
# User can adjust this before enabling live updates to set desired refresh speed

# ----------------------------------------------------------------------------
# CONTROL 3: DEVICE SELECTION DROPDOWN
# ----------------------------------------------------------------------------
# Allows filtering the entire dashboard to a single device or viewing all

temp_devices = st.session_state.traffic_generator.get_devices()
# Must fetch device list BEFORE creating the dropdown
# .get_devices() returns list of dictionaries with device information
# Called 'temp_devices' because it's only used to extract names for dropdown
# This is separate from the main device fetch in STEP 5 (happens later)

device_names = ["All Devices"] + [device['name'] for device in temp_devices]
# Create list of device names for the dropdown options
# Breakdown:
#   - ["All Devices"]: Start with this special option (overview mode)
#   - List comprehension [device['name'] for device in temp_devices]
#     extracts just the 'name' field from each device dictionary
#   - The + operator concatenates the lists
# Result: ["All Devices", "User iPhone", "Home PC", "Smart TV", ...]
# "All Devices" always appears first

selected_device = st.sidebar.selectbox("Select Device", device_names, index=0)
# .selectbox() creates a dropdown menu widget
# Parameters:
#   - First argument: Label text shown above the dropdown
#   - device_names: List of options to display in the dropdown
#   - index=0: Default selection (0 = first option = "All Devices")
# Returns: String (the selected device name)
# This variable is used throughout the code to filter data (STEP 6B, 8, etc.)

st.sidebar.markdown("---")
# .markdown("---") creates a horizontal rule (divider line)
# Separates controls from the About section for better visual organization

# ----------------------------------------------------------------------------
# ABOUT SECTION
# ----------------------------------------------------------------------------
# Provides context about the dashboard's purpose and capabilities

st.sidebar.title("About")
# Second heading in sidebar (after "Controls")

st.sidebar.info(
    "Real-time network monitoring dashboard for Ubiquiti devices. "
    "Tracks connected devices, bandwidth usage, security alerts, and global traffic patterns. "
    "Features live throughput monitoring and CVE vulnerability tracking."
)
# .info() creates a blue information box with an icon
# Alternative options: .success() (green), .warning() (yellow), .error() (red)
# Provides users with a quick summary of what the dashboard does
# Important for presentations/demos to set context

# ============================================================================
# STEP 5: DASHBOARD HEADER WITH ISP/WEATHER WIDGETS
# ============================================================================
# This section creates the top bar of the dashboard with ISP info and weather
# Uses custom HTML/CSS for precise control over layout and styling

header_left, header_right = st.columns([1, 1])
# st.columns() creates side-by-side layout containers
# [1, 1] means equal width columns (50/50 split)
# Could use [2, 1] for 2/3 + 1/3 split, etc.
# Returns a tuple of column objects: (left_column, right_column)

# ----------------------------------------------------------------------------
# LEFT HEADER: ISP INFORMATION DISPLAY
# ----------------------------------------------------------------------------
with header_left:
    # 'with' statement makes all Streamlit commands target this specific column
    # Any st.xyz() calls inside this block render in the left column only

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
    # This creates a custom HTML card using inline CSS
    # Breakdown of CSS properties:
    #   - background: #1a1a1a (very dark gray, almost black)
    #   - border: 1px solid #333 (thin gray border for definition)
    #   - border-radius: 8px (rounded corners for modern look)
    #   - padding: 15px (space inside the box around the text)
    #   - color: white (text color)
    #   - margin-bottom: 10px (space below the widget)
    # Inner divs:
    #   - First div: "ISP: ISP.net" in larger font
    #   - Second div: "IP Address: 1.2.3.4" in smaller, grayed text
    # Note: These values are hardcoded placeholders (would be dynamic in production)

# ----------------------------------------------------------------------------
# RIGHT HEADER: CVE VULNERABILITY WIDGET
# ----------------------------------------------------------------------------
# CVE = Common Vulnerabilities and Exposures
# This is a standard way to identify security vulnerabilities in software
# Example: CVE-2024-1234 uniquely identifies a specific security flaw
# This section displays the latest security vulnerabilities found in Ubiquiti products

with header_right:
    # We're working in the right column of the header (remember we made 2 columns earlier)
    # The left column shows ISP info, this right column shows CVE security info

    # =========================================================================
    # STEP 1: FETCH CVE DATA FROM OUR CVE FETCHER
    # =========================================================================
    # Get the CVE fetcher object from session state (we created this earlier)
    # Then call its method to get the latest 3 Ubiquiti vulnerabilities
    cve_data = st.session_state.cve_fetcher.get_ubiquiti_cves(max_results=3)
    # What this returns:
    #   - If successful: A list of dictionaries, each containing CVE info
    #   - If failed: None (could be network error, API down, etc.)
    # Example of what cve_data might look like:
    # [
    #   {'id': 'CVE-2024-1234', 'severity': 'HIGH', 'cvss_score': 8.5, ...},
    #   {'id': 'CVE-2024-5678', 'severity': 'MEDIUM', 'cvss_score': 6.2, ...},
    #   {'id': 'CVE-2024-9012', 'severity': 'LOW', 'cvss_score': 3.1, ...}
    # ]

    # =========================================================================
    # STEP 2: CHECK IF WE GOT DATA SUCCESSFULLY
    # =========================================================================
    # We need to check two things:
    # 1. Is cve_data not None? (did the API call succeed?)
    # 2. Does the list have at least 1 item? (are there any CVEs?)
    if cve_data and len(cve_data) > 0:
        # Great! We have CVE data to display
        # The 'and' means BOTH conditions must be True
        # If cve_data is None, Python won't even check len() (short-circuit evaluation)

        # =====================================================================
        # STEP 3: DETERMINE COLOR FOR THE WIDGET BORDER
        # =====================================================================
        # We want the border color to match the severity of the MOST RECENT CVE
        # The most recent CVE is the first one in the list (index 0)
        first_cve = cve_data[0]
        # Get the first CVE from the list
        # Example: first_cve = {'id': 'CVE-2024-1234', 'severity': 'HIGH', ...}

        # Extract the severity level from the CVE dictionary
        # .get() is safer than ['severity'] because it won't crash if key doesn't exist
        # The second parameter 'UNKNOWN' is the default value if severity key is missing
        severity = first_cve.get('severity', 'UNKNOWN')
        # severity will be something like: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', or 'UNKNOWN'

        # Now we pick a color based on severity
        # We use an if-elif-else chain (like a series of questions)
        if severity in ['CRITICAL', 'HIGH']:
            # Is severity either CRITICAL or HIGH?
            # 'in' checks if the value is in the list
            severity_color = '#ef4444'
            # Red color (hex code) - use for dangerous vulnerabilities
            # Hex colors: # followed by 6 characters (RRGGBB in hexadecimal)
            # ef=red, 44=green, 44=blue = mostly red = danger color
        elif severity == 'MEDIUM':
            # If not critical/high, is it medium?
            severity_color = '#f59e0b'
            # Orange color - use for moderate vulnerabilities
            # f5=red, 9e=green, 0b=blue = orange = warning color
        else:
            # If none of the above (LOW or UNKNOWN)
            severity_color = '#10b981'
            # Green color - use for low-risk vulnerabilities
            # 10=red, b9=green, 81=blue = green = safe/low risk color

        # =====================================================================
        # STEP 4: CREATE THE WIDGET HEADER BOX
        # =====================================================================
        # We use st.markdown() with HTML/CSS to create a custom styled box
        # Why? Streamlit's built-in widgets don't give us enough control over appearance
        st.markdown(
            # f-string (f"...") lets us insert Python variables into the string
            # Variables in {curly braces} get replaced with their values
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
            # Let me explain this HTML/CSS:
            # - <div> = division/container element in HTML
            # - style='...' = inline CSS styling
            # - background: #000000 = black background
            # - border: 1px solid {severity_color} = thin border with color based on severity
            # - border-radius: 8px = rounded corners (8 pixels of rounding)
            # - padding: 15px = space inside the box (15 pixels on all sides)
            # - color: white = text color is white
            # - margin-bottom: 10px = space below the box
            # The {severity_color} gets replaced with the color variable we set above

            unsafe_allow_html=True
            # This tells Streamlit: "Yes, I know I'm using HTML, please render it"
            # By default, Streamlit escapes HTML (displays it as text for security)
            # Setting this to True allows the HTML to actually render
            # Only do this with code YOU write, never with user input!
        )
        # At this point, we've opened the container but haven't closed it yet
        # We'll close it later after displaying all the CVEs

        # =====================================================================
        # STEP 5: LOOP THROUGH EACH CVE AND DISPLAY IT
        # =====================================================================
        # We have 3 CVEs in our list, we need to display each one
        # A 'for' loop lets us repeat code for each item in a list
        for cve in cve_data:
            # 'for' loop explanation:
            # - 'cve' is a variable that will hold each CVE one at a time
            # - 'in cve_data' means loop through the cve_data list
            # - First iteration: cve = first CVE
            # - Second iteration: cve = second CVE
            # - Third iteration: cve = third CVE
            # Example: cve = {'id': 'CVE-2024-1234', 'severity': 'HIGH', ...}

            # -----------------------------------------------------------------
            # STEP 5A: DETERMINE COLOR FOR THIS SPECIFIC CVE
            # -----------------------------------------------------------------
            # Each CVE might have a different severity, so we need to check again
            severity = cve.get('severity', 'UNKNOWN')
            # Get the severity for THIS specific CVE
            # Same as before, .get() with default 'UNKNOWN'

            # Now pick the color for THIS CVE (same logic as before)
            if severity in ['CRITICAL', 'HIGH']:
                color = '#ef4444'  # Red
            elif severity == 'MEDIUM':
                color = '#f59e0b'  # Orange
            else:
                color = '#10b981'  # Green

            # -----------------------------------------------------------------
            # STEP 5B: CHECK IF THIS CVE IS ROUTER-RELATED
            # -----------------------------------------------------------------
            # Some CVEs affect routers specifically, we want to mark those
            # We check if the 'is_router_related' field is True
            # NOTE: Router badge emoji removed per user request
            # We still track if it's router-related in the data, just don't display a badge
            router_badge = ""
            # No badge is displayed anymore (emoji removed)
            # This keeps the code simple and clean

            # -----------------------------------------------------------------
            # STEP 5C: BUILD THE NVD URL FOR THIS CVE
            # -----------------------------------------------------------------
            # NVD = National Vulnerability Database (run by US government)
            # Every CVE has a page on NVD with detailed information
            # The URL format is always: https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX
            # We just need to add the CVE ID to the end

            cve_id = cve['id']
            # Get the CVE ID (like "CVE-2024-1234")
            # We use ['id'] not .get() because we KNOW this field exists
            # (our CVE fetcher always includes it)

            cve_url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            # Build the complete URL by inserting the CVE ID
            # Example result: "https://nvd.nist.gov/vuln/detail/CVE-2024-1234"
            # Users can click this to read full details about the vulnerability

            # -----------------------------------------------------------------
            # STEP 5D: DISPLAY THIS CVE AS A CLICKABLE CARD
            # -----------------------------------------------------------------
            st.markdown(
                # Again using f-string to insert multiple variables
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
                            <span style='font-size: 13px; font-weight: bold; color: white;'>{cve_id}{router_badge}</span>
                            <span style='font-size: 11px; color: {color};'>{severity} ({cve['cvss_score']})</span>
                        </div>
                        <div style='font-size: 11px; color: #999;'>{cve['published']}</div>
                    </div>
                </a>
                """,
                # Let me explain this HTML/CSS in detail:
                #
                # <a href='...' target='_blank' style='text-decoration: none;'>
                #   - <a> = anchor tag = hyperlink
                #   - href='{cve_url}' = where the link goes (the NVD page)
                #   - target='_blank' = open in NEW tab (don't leave dashboard)
                #   - text-decoration: none = remove underline from link
                #
                # <div style='...'>
                #   - background: #1a1a1a = very dark gray (darker than outer box)
                #   - border-left: 3px solid {color} = thick left border with severity color
                #   - padding: 8px 10px = space inside (8px top/bottom, 10px left/right)
                #   - margin-bottom: 8px = space between CVE cards
                #   - border-radius: 4px = slightly rounded corners
                #   - transition: background 0.2s = smooth color change on hover (0.2 seconds)
                #
                # <div style='display: flex; justify-content: space-between; ...'>
                #   - display: flex = use flexbox layout (modern CSS layout system)
                #   - justify-content: space-between = push content to left and right edges
                #   - align-items: center = vertically center the content
                #   - This creates a row with CVE ID on left, severity on right
                #
                # <span style='font-size: 13px; font-weight: bold; color: white;'>
                #   - <span> = inline element (doesn't create new line)
                #   - font-size: 13px = text size in pixels
                #   - font-weight: bold = make text bold
                #   - color: white = white text
                #   - {cve_id}{router_badge} = CVE ID + optional globe icon
                #
                # <span style='font-size: 11px; color: {color};'>
                #   - Smaller text (11px) for severity info
                #   - color: {color} = use the severity color (red/orange/green)
                #   - {severity} ({cve['cvss_score']}) = "HIGH (8.5)" for example
                #
                # <div style='font-size: 11px; color: #999;'>
                #   - Small gray text for the published date
                #   - #999 = medium gray
                #   - {cve['published']} = date like "2024-11-30"

                unsafe_allow_html=True
                # Again, allow HTML to render (we trust our own code)
            )
            # The for loop will repeat this for each CVE in the list
            # After 3 iterations (3 CVEs), the loop ends

        # =====================================================================
        # STEP 6: CLOSE THE MAIN WIDGET CONTAINER
        # =====================================================================
        # Remember we opened a <div> way back in STEP 4?
        # HTML tags must be closed, or the page layout breaks
        st.markdown("</div>", unsafe_allow_html=True)
        # This closes the outer container div
        # </div> is the closing tag (note the /)

        # =====================================================================
        # STEP 7: ADD A "VIEW ALL" LINK BELOW THE WIDGET
        # =====================================================================
        # Give users a way to see ALL Ubiquiti CVEs, not just the latest 3
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
            # Let me explain this link:
            #
            # <div style='text-align: center; margin-top: 10px;'>
            #   - text-align: center = center the link horizontally
            #   - margin-top: 10px = space above the link
            #
            # <a href='https://nvd.nist.gov/vuln/search#/nvd/home?...' target='_blank'>
            #   - This URL goes to NVD's search page
            #   - The URL structure:
            #     * /vuln/search = NVD vulnerability search interface
            #     * #/nvd/home = navigation to NVD home section
            #     * ?keyword=Ubiquiti = search keyword parameter
            #     * &resultType=records = display results as records (detailed view)
            #   - target='_blank' = open in new tab (don't leave the dashboard)
            #   - This keeps the user's dashboard open while viewing CVE details
            #
            # style='color: #00d4ff; text-decoration: none; ...'
            #   - color: #00d4ff = cyan color (matches download theme throughout dashboard)
            #   - text-decoration: none = no underline (cleaner look)
            #   - font-size: 12px = small text (not too prominent)
            #   - font-weight: 500 = medium weight (between normal and bold)
            #
            # View All Ubiquiti CVEs on NVD
            #   - Simple, clear text (emojis removed per user request)
            #   - Tells user exactly what will happen when they click

            unsafe_allow_html=True
            # Allow the HTML to render (we trust our own HTML code)
        )

    else:
        # =====================================================================
        # ERROR CASE: CVE DATA UNAVAILABLE
        # =====================================================================
        # If we reach this 'else' block, it means:
        # - Either cve_data is None (API call failed)
        # - Or cve_data is an empty list (no CVEs found)
        # We show a simple error message so the space isn't blank

        st.markdown(
            # Simple box with error message
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
            # CSS explanation:
            # - background: #000000 = black (same as working widget)
            # - border: 1px solid #ffffff = white border (neutral, no severity)
            # - border-radius: 8px = rounded corners (same as working widget)
            # - padding: 15px = space inside
            # - color: #888 = gray text (indicates disabled/error state)
            # - text-align: center = center the error message
            #
            # The message "CVE data unavailable" tells the user:
            # - There's nothing wrong with the dashboard
            # - The CVE API just isn't responding right now
            # - They should try refreshing later

            unsafe_allow_html=True
            # Allow HTML rendering
        )
        # No need to add detailed comments here since it's just an error message
        # The important part is that we show SOMETHING instead of blank space

# ----------------------------------------------------------------------------
# MAIN DASHBOARD TITLE
# ----------------------------------------------------------------------------
st.title("Ubiquiti Network Monitor")
# .title() creates a large heading (HTML <h1> tag)
# This is the primary title for the entire dashboard
# No emoji used to avoid rendering issues during live updates

st.markdown("### Real-time Traffic Simulation")
# .markdown() with ### creates a subheading (HTML <h3> tag)
# Provides context about the nature of the dashboard (simulated data)
# Important for academic presentations to clarify this is a demo

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
# STEP 6: PROCESS AND TRANSFORM RAW DEVICE DATA
# ============================================================================
# The data_generator provides device information as a list of dictionaries
# Each dictionary represents one device with keys like 'name', 'ip', 'download_bytes'
# Converting to a DataFrame makes the data easier to filter, calculate, and display

df = pd.DataFrame(devices)
# pd.DataFrame() converts Python list of dicts into a pandas DataFrame (table)
# Example input: [{'name': 'PC', 'download_bytes': 5000000}, {'name': 'Phone', ...}]
# Example output: A table with columns 'name', 'download_bytes', etc.
# DataFrames provide methods like .sum(), .filter(), .sort() that lists don't have

# ----------------------------------------------------------------------------
# SUBSECTION 6A: UNIT CONVERSION (BYTES TO MEGABYTES)
# ----------------------------------------------------------------------------
# Network traffic is measured in bytes, but bytes are hard to read at scale
# Example: 5,242,880 bytes is difficult to parse mentally
# Converting to megabytes makes it human-readable: 5.00 MB

df['Download (MB)'] = df['download_bytes'] / (1024 * 1024)
# Why divide by 1,024 twice (instead of 1,000,000)?
#   - Computers use binary (base-2), not decimal (base-10)
#   - 1 KB = 1,024 bytes (not 1,000)
#   - 1 MB = 1,024 KB = 1,024 × 1,024 = 1,048,576 bytes
# This creates a NEW column in the DataFrame called 'Download (MB)'
# The original 'download_bytes' column remains unchanged

df['Upload (MB)'] = df['upload_bytes'] / (1024 * 1024)
# Same conversion for upload traffic
# Now the DataFrame has both byte and MB columns for flexibility

# ----------------------------------------------------------------------------
# SUBSECTION 6B: DATA FILTERING BASED ON USER SELECTION
# ----------------------------------------------------------------------------
# The user can select either "All Devices" or a specific device from the dropdown
# This section creates a filtered view of the data based on that selection

if selected_device != "All Devices":
    # User selected a specific device (e.g., "User iPhone")
    # Need to filter the DataFrame to show only that device's data

    df_filtered = df[df['name'] == selected_device].copy()
    # Breakdown of this line:
    #   df['name'] == selected_device creates a boolean mask (True/False for each row)
    #   Example: [True, False, False, True, False] if device name matches
    #   df[mask] returns only rows where mask is True
    #   .copy() creates a new DataFrame instead of a view (prevents warnings)

    # Extract the device's full information for the details panel
    if len(df_filtered) > 0:
        # Verify the filtered DataFrame actually has data (device exists)

        selected_device_data = df_filtered.iloc[0].to_dict()
        # iloc[0] gets the first row of the filtered DataFrame
        # Since filtered by exact name match, there should only be 1 row
        # .to_dict() converts the row into a Python dictionary
        # Result: {'name': 'User iPhone', 'ip': '192.168.1.5', 'mac': '...', etc.}
        # This dictionary is used later to display device details (IP, MAC, etc.)
    else:
        # Device not found in data (shouldn't happen, but handle edge case)
        selected_device_data = None
else:
    # User selected "All Devices" - show everything
    df_filtered = df.copy()
    # .copy() creates a duplicate of the entire DataFrame
    # This keeps the code consistent (always working with df_filtered)
    # Avoids accidentally modifying the original df

    selected_device_data = None
    # No single device selected, so no device details to show

# ----------------------------------------------------------------------------
# SUBSECTION 6C: CALCULATE AGGREGATE STATISTICS
# ----------------------------------------------------------------------------
# The dashboard displays summary metrics (total devices, total traffic)
# These calculations work on the filtered data, so they adapt to user selection

total_devices = len(df_filtered[df_filtered['status'] == 'ONLINE'])
# Count how many devices are currently online
# Breakdown:
#   df_filtered['status'] == 'ONLINE' creates boolean mask for online devices
#   df_filtered[mask] filters to only online devices
#   len() counts the number of rows
# If viewing "All Devices": counts all online devices
# If viewing single device: returns 1 (if online) or 0 (if offline)

total_download = df_filtered['Download (MB)'].sum()
# .sum() adds up all values in the 'Download (MB)' column
# For "All Devices": total network download traffic
# For single device: that device's total download traffic
# Returns a float (e.g., 156.75)

total_upload = df_filtered['Upload (MB)'].sum()
# Same concept as download, but for upload traffic

# ----------------------------------------------------------------------------
# SUBSECTION 6D: EXTRACT CURRENT SPEEDS FOR LIVE DISPLAY
# ----------------------------------------------------------------------------
# In addition to cumulative totals, the dashboard shows current speed
# Current speed is measured in MB/s (megabytes per second)

current_download_speed = df_filtered['current_download_speed'].sum()
# 'current_download_speed' is provided by the data generator
# Represents the instantaneous download rate at this moment
# .sum() adds speeds across all devices in the filtered data
# For "All Devices": combined network speed
# For single device: that device's individual speed

current_upload_speed = df_filtered['current_upload_speed'].sum()
# Same concept for upload speed

# ----------------------------------------------------------------------------
# SUBSECTION 6E: TRAFFIC HISTORY TRACKING (PER-DEVICE)
# ----------------------------------------------------------------------------
# The 30-minute throughput graph needs historical data, not just current values
# This section maintains a time-series record of each device's traffic over time
# Data is stored in st.session_state so it persists across page refreshes

if 'device_traffic_history' not in st.session_state:
    # First run of the app - initialize the storage structure
    st.session_state.device_traffic_history = {}
    # This will become a dictionary of dictionaries:
    # {
    #   'User iPhone': {'timestamps': [...], 'download_speeds': [...], 'upload_speeds': [...]},
    #   'Home PC': {'timestamps': [...], 'download_speeds': [...], 'upload_speeds': [...]},
    #   ...
    # }

# Get current time to timestamp this data point
current_time = datetime.now()
# datetime.now() returns current date and time (e.g., 2025-11-30 17:45:23)
# This timestamp allows plotting data chronologically on the graph

# Loop through each device and record its current speed
for _, device in df.iterrows():
    # df.iterrows() loops over DataFrame rows as (index, Series) tuples
    # The index isn't needed (hence _), device is a Series with all columns
    # Example: device['name'] = "User iPhone", device['current_download_speed'] = 2.5

    device_name = device['name']
    # Extract the device name to use as a key in the history dictionary

    if device_name not in st.session_state.device_traffic_history:
        # First time seeing this device - create its history structure
        st.session_state.device_traffic_history[device_name] = {
            'timestamps': [],           # Will hold datetime objects
            'download_speeds': [],      # Will hold float values (MB/s)
            'upload_speeds': []         # Will hold float values (MB/s)
        }
        # These lists will grow over time as data points are appended

    # Append current data point to this device's history
    st.session_state.device_traffic_history[device_name]['timestamps'].append(current_time)
    st.session_state.device_traffic_history[device_name]['download_speeds'].append(device['current_download_speed'])
    st.session_state.device_traffic_history[device_name]['upload_speeds'].append(device['current_upload_speed'])
    # .append() adds the value to the end of the list
    # All three lists stay synchronized (same length, corresponding indices)

    # -------------------------------------------------------------------------
    # GARBAGE COLLECTION: Remove data older than 30 minutes
    # -------------------------------------------------------------------------
    # Without this, the lists would grow infinitely and consume memory
    # Also, the graph only shows 30 minutes, so old data isn't needed

    cutoff_time = current_time - timedelta(minutes=30)
    # timedelta(minutes=30) represents a 30-minute duration
    # Subtracting it from current_time gives the threshold timestamp
    # Example: If now is 18:00, cutoff is 17:30

    history = st.session_state.device_traffic_history[device_name]
    # Get reference to this device's history dictionary for easier access

    valid_indices = [i for i, t in enumerate(history['timestamps']) if t >= cutoff_time]
    # List comprehension that finds indices of timestamps still within 30-minute window
    # enumerate() gives (index, value) pairs: [(0, timestamp1), (1, timestamp2), ...]
    # The condition 't >= cutoff_time' keeps only recent timestamps
    # Result: List of indices to keep, e.g., [45, 46, 47, ..., 120] if first 44 are old

    # Rebuild each list with only valid (recent) indices
    history['timestamps'] = [history['timestamps'][i] for i in valid_indices]
    history['download_speeds'] = [history['download_speeds'][i] for i in valid_indices]
    history['upload_speeds'] = [history['upload_speeds'][i] for i in valid_indices]
    # List comprehensions create new lists containing only elements at valid indices
    # This effectively "trims" the old data from the beginning of each list
    # All three lists remain synchronized because they use the same valid_indices

# ----------------------------------------------------------------------------
# SUBSECTION 6F: TRAFFIC HISTORY TRACKING (ALL DEVICES COMBINED)
# ----------------------------------------------------------------------------
# In addition to per-device history, maintain an aggregate view of all traffic
# This is used when the user selects "All Devices" from the dropdown

if 'traffic_history' not in st.session_state:
    # First run - initialize overall history structure
    st.session_state.traffic_history = {
        'timestamps': [],
        'download_speeds': [],
        'upload_speeds': []
    }
    # Same structure as per-device, but holds combined network traffic

# Calculate total network speeds at this moment
all_download_speed = df['current_download_speed'].sum()
all_upload_speed = df['current_upload_speed'].sum()
# .sum() adds up speeds across ALL devices (not filtered)
# This represents the entire network's bandwidth usage

# Append to overall history
st.session_state.traffic_history['timestamps'].append(current_time)
st.session_state.traffic_history['download_speeds'].append(all_download_speed)
st.session_state.traffic_history['upload_speeds'].append(all_upload_speed)
# Same append pattern as per-device history

# Trim data older than 30 minutes (same garbage collection logic)
cutoff_time = current_time - timedelta(minutes=30)
valid_indices = [i for i, t in enumerate(st.session_state.traffic_history['timestamps']) if t >= cutoff_time]
st.session_state.traffic_history['timestamps'] = [st.session_state.traffic_history['timestamps'][i] for i in valid_indices]
st.session_state.traffic_history['download_speeds'] = [st.session_state.traffic_history['download_speeds'][i] for i in valid_indices]
st.session_state.traffic_history['upload_speeds'] = [st.session_state.traffic_history['upload_speeds'][i] for i in valid_indices]

# ----------------------------------------------------------------------------
# SUBSECTION 6G: SECURITY ALERT COLLECTION
# ----------------------------------------------------------------------------
# The dashboard displays suspicious traffic alerts (port scans, malware, etc.)
# The data generator randomly creates these alerts to simulate security monitoring

new_alerts = st.session_state.traffic_generator.generate_security_alerts()
# generate_security_alerts() has a 20% chance per refresh to return alerts
# Returns a list of dictionaries, each representing one alert
# Example: [{'device': 'Home PC', 'external_ip': '1.2.3.4', 'reason': 'Port scan', ...}]
# Returns empty list [] if no alerts generated this refresh

if new_alerts:
    # Only process if the generator actually created alerts (list is not empty)

    st.session_state.security_alerts = new_alerts + st.session_state.security_alerts
    # Prepend new alerts to the BEGINNING of the existing list
    # new_alerts + existing_alerts creates: [newest, ..., older, ..., oldest]
    # This keeps the list chronologically ordered with newest first
    # The alerts table will display them in this order (most recent at top)

# Trim alert list to prevent unbounded growth
st.session_state.security_alerts = st.session_state.security_alerts[:50]
# List slicing [:50] keeps only the first 50 elements
# If list has fewer than 50 elements, this does nothing
# If list has more than 50, it discards everything after index 49
# This caps memory usage and keeps the interface manageable
# 50 alerts is enough for meaningful security review without overwhelming the user

# ============================================================================
# STEP 6.5: DEVICE DETAILS (Single Device View Only)
# ============================================================================
# When a user selects a specific device from the dropdown, this section displays
# detailed information about that device in a prominent card layout
# This section is ONLY shown for single device views, not "All Devices"

if selected_device != "All Devices" and selected_device_data:
    # Two conditions must be true for this block to execute:
    #   1. selected_device != "All Devices" - User selected a specific device
    #   2. selected_device_data is not None - Device data was successfully found
    # The 'and' operator requires BOTH conditions to be True

    st.markdown(f"### {selected_device}")
    # Display device name as a heading using markdown (### = h3 tag)
    # F-string substitutes the actual device name (e.g., "User iPhone")
    # This provides context for the details shown below

    # Create columns for device details
    detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)
    # st.columns(4) creates FOUR equal-width columns (25% each)
    # Returns a tuple of 4 column objects: (col1, col2, col3, col4)
    # This creates a horizontal layout for the four info cards below

    # -------------------------------------------------------------------------
    # DETAIL CARD 1: IP ADDRESS
    # -------------------------------------------------------------------------
    with detail_col1:
        # 'with' statement targets all Streamlit commands to the first column
        # Everything inside this block renders in detail_col1 only

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
        # Custom HTML card using f-string to inject device IP address
        # CSS Breakdown:
        #   - background: #1a1a1a (dark gray matching dashboard theme)
        #   - border: 1px solid #00d4ff (cyan border matching download color)
        #   - border-radius: 8px (rounded corners for modern appearance)
        #   - padding: 15px (internal spacing around content)
        #   - text-align: center (centers both label and value)
        # Card structure:
        #   - Top line: "IP ADDRESS" label in small gray text
        #   - Bottom line: Actual IP (e.g., "192.168.1.5") in large white text
        # IP Address explained:
        #   - Private IP address on the local network (not public internet)
        #   - Format: 192.168.x.x or 10.x.x.x (private ranges per RFC 1918)
        #   - Identifies this specific device on the LAN

    # -------------------------------------------------------------------------
    # DETAIL CARD 2: MAC ADDRESS
    # -------------------------------------------------------------------------
    with detail_col2:
        # Targets second column (25% width, right of IP card)

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
        # Similar structure to IP card but with purple border (#a855f7, upload color)
        # MAC Address explained:
        #   - Media Access Control address: hardware identifier burned into network card
        #   - Format: 6 pairs of hexadecimal digits (e.g., AA:BB:CC:DD:EE:FF)
        #   - Unique to each network interface (like a serial number)
        #   - Cannot be changed (normally) - used for network layer 2 communication
        #   - First 3 pairs identify manufacturer (Organizational Unique Identifier)
        # Why purple border?
        #   - Alternating colors (cyan/purple) provide visual distinction
        #   - Matches the upload line color used in graphs throughout dashboard

    # -------------------------------------------------------------------------
    # DETAIL CARD 3: CONNECTION TYPE
    # -------------------------------------------------------------------------
    with detail_col3:
        # Targets third column (right of MAC card)

        connection_color = "#00d4ff" if selected_device_data['connection_type'] == "Wired" else "#a855f7"
        # Ternary operator (conditional expression) for dynamic color selection
        # Syntax: value_if_true if condition else value_if_false
        # Breakdown:
        #   - If connection_type == "Wired": use cyan (#00d4ff)
        #   - Otherwise (Wi-Fi): use purple (#a855f7)
        # This provides visual distinction between wired and wireless connections
        # Wired = cyan (faster, more stable) | Wi-Fi = purple (wireless)

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
        # F-string injects BOTH the dynamic color AND the connection type text
        # {connection_color} gets replaced with hex color code
        # {selected_device_data['connection_type']} becomes "Wired" or "Wi-Fi"
        # Connection Type explained:
        #   - "Wired": Device connected via Ethernet cable (RJ-45 connector)
        #     Benefits: Faster speeds, lower latency, more reliable
        #   - "Wi-Fi": Device connected wirelessly via radio waves
        #     Benefits: Mobility, no physical cable needed
        #     Drawbacks: Slower than wired, subject to interference

    # -------------------------------------------------------------------------
    # DETAIL CARD 4: STATUS
    # -------------------------------------------------------------------------
    with detail_col4:
        # Targets fourth and final column (rightmost)

        status_color = "#10b981" if selected_device_data['status'] == "ONLINE" else "#ef4444"
        # Another ternary operator for status-based coloring
        # Breakdown:
        #   - If status == "ONLINE": use green (#10b981)
        #   - Otherwise (OFFLINE): use red (#ef4444)
        # Color psychology:
        #   - Green: Good, active, operational (universal positive indicator)
        #   - Red: Alert, inactive, offline (universal warning indicator)

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
        # IMPORTANT DIFFERENCE: The status text ITSELF is colored (not just border)
        # Look at: <div style='color: {status_color};...
        # This makes "ONLINE" appear green and "OFFLINE" appear red
        # Provides immediate visual feedback on device state
        # Status explained:
        #   - "ONLINE": Device is actively connected and communicating
        #   - "OFFLINE": Device is disconnected (powered off, out of range, etc.)
        # The data generator randomly toggles status to simulate real network behavior

    st.markdown("---")
    # Horizontal divider line (---) separates device details from metrics below
    # Provides visual spacing and section distinction

# ============================================================================
# STEP 7: DISPLAY METRICS (TOP ROW)
# ============================================================================
# Metric cards provide at-a-glance summary statistics
# These appear immediately after device details (if shown) or after the title
# Metrics are calculated from df_filtered, so they adapt to "All Devices" or single device view

# Create 3 equal-width columns for metric cards
col1, col2, col3 = st.columns(3)
# st.columns(3) divides the width into three equal parts (33.33% each)
# Returns tuple: (col1, col2, col3)

# Each metric() creates a card with a label and value
# These provide quick overview stats at the top of the dashboard
col1.metric("Connected Devices", total_devices)
# .metric(label, value) creates a styled card with large number display
# Parameters:
#   - "Connected Devices": Label text shown above the number
#   - total_devices: The actual count (calculated in STEP 6C)
# Displays number of ONLINE devices (offline devices not counted)
# For "All Devices": counts all online devices on network
# For single device: shows 1 (if online) or 0 (if offline)

col2.metric("Total Download", f"{total_download:.2f} MB")
# F-string with format specification: {value:.2f}
# Breakdown:
#   - : indicates format specification follows
#   - .2f means "floating point with 2 decimal places"
#   - Example: 156.789 becomes "156.79"
# This shows cumulative download traffic (all-time total, not current speed)
# Measured in megabytes (MB) after conversion from bytes in STEP 6A

col3.metric("Total Upload", f"{total_upload:.2f} MB")
# Same formatting as download
# Upload typically lower than download (asymmetric internet connections)
# Most home/business connections prioritize download speed
# Example: 100 Mbps down / 20 Mbps up is common

# ============================================================================
# STEP 7.25: LIVE THROUGHPUT DISPLAY
# ============================================================================
# This section shows CURRENT network speed (real-time bandwidth usage)
# Different from metrics above (which show cumulative totals)
# Throughput = data transfer rate (MB/s or Mbps)

st.markdown("### Live Throughput")
# Section heading using markdown (### = h3 tag)
# "Live" indicates this updates continuously, not historical data

# Create columns for download and upload speeds
throughput_col1, throughput_col2 = st.columns(2)
# Two equal-width columns (50/50 split) for side-by-side display
# Download on left (cyan), Upload on right (purple)

# ----------------------------------------------------------------------------
# LIVE DOWNLOAD SPEED CARD
# ----------------------------------------------------------------------------
with throughput_col1:
    # Targets left column for download display

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
    # Custom HTML card with cyan color scheme
    # CSS Notable differences from metric cards:
    #   - padding: 20px (larger than device details for emphasis)
    #   - font-size: 36px (VERY large for at-a-glance viewing)
    #   - color: #00d4ff (cyan, matching download theme throughout dashboard)
    # {current_download_speed:.2f} displays current speed from STEP 6D
    # "Mbps" = Megabits per second (standard network speed unit)
    # NOTE: This is Mbps (bits), not MB/s (bytes) - different from totals above
    #   - 1 byte = 8 bits
    #   - 8 Mbps = 1 MB/s
    #   - ISPs advertise in Mbps because numbers look bigger

# ----------------------------------------------------------------------------
# LIVE UPLOAD SPEED CARD
# ----------------------------------------------------------------------------
with throughput_col2:
    # Targets right column for upload display

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
    # Identical structure to download card but with purple color scheme
    # Purple (#a855f7) consistently represents upload throughout the dashboard
    # Side-by-side layout allows easy comparison of download vs upload speeds
    # Typical pattern: Download significantly higher than upload
    # Example: 100 Mbps down / 10 Mbps up is common for residential internet

# ============================================================================
# STEP 7.5: NETWORK SPEED GRAPH (30-MINUTE HISTORY)
# ============================================================================
# This graph visualizes throughput over time (time-series data)
# Shows trends, patterns, and fluctuations in network usage
# Data is tracked in STEP 6E (per-device) and STEP 6F (all devices)

st.markdown("### Network Throughput (Last 30 Minutes)")
# Section heading for the historical graph
# "Last 30 Minutes" indicates the time window (older data is trimmed)

# Use appropriate history based on selected device
if selected_device != "All Devices" and selected_device in st.session_state.device_traffic_history:
    # Condition breakdown:
    #   1. User selected a specific device (not "All Devices")
    #   2. AND that device has history data (in the device_traffic_history dict)
    # If both true: show that device's individual traffic history

    history_data = st.session_state.device_traffic_history[selected_device]
    # Get the history dictionary for the selected device
    # Contains: {'timestamps': [...], 'download_speeds': [...], 'upload_speeds': [...]}
    # This shows ONLY the selected device's traffic over time
else:
    # Otherwise: show combined network traffic (all devices)
    # This executes for "All Devices" selection OR if device history doesn't exist yet
    history_data = st.session_state.traffic_history
    # Get the overall network history (aggregated across all devices)
    # Same structure as per-device, but values are summed from STEP 6F

# Only show graph if there are enough data points
if len(history_data['timestamps']) > 0:
    # Check if any data has been collected yet
    # On first run, the lists are empty (no data to plot)
    # After a few refreshes, data accumulates and graph becomes meaningful
    # len() returns the number of elements in the timestamps list
    # -------------------------------------------------------------------------
    # CREATE PLOTLY FIGURE OBJECT
    # -------------------------------------------------------------------------
    fig_speed = go.Figure()
    # go.Figure() creates an empty Plotly graph object
    # go = graph_objects (imported at top of file)
    # This is the canvas on which data traces (lines) will be added
    # Lower-level API compared to plotly.express (more control over styling)

    # -------------------------------------------------------------------------
    # ADD DOWNLOAD SPEED LINE (CYAN)
    # -------------------------------------------------------------------------
    fig_speed.add_trace(go.Scatter(
        # .add_trace() adds a data series (line, bar, scatter, etc.) to the figure
        # go.Scatter creates a scatter/line plot (can show points, lines, or both)

        x=history_data['timestamps'],
        # x-axis: Time values (list of datetime objects)
        # Example: [2025-11-30 17:30:00, 17:30:05, 17:30:10, ...]
        # Plotly automatically formats these as readable time labels

        y=history_data['download_speeds'],
        # y-axis: Speed values (list of floats in MB/s)
        # Example: [2.5, 3.1, 2.8, 4.2, ...]
        # These correspond to the timestamps (same indices match)

        mode='lines',
        # mode controls what's displayed:
        #   - 'lines': Connect points with lines (what is used here)
        #   - 'markers': Show just the data points as dots
        #   - 'lines+markers': Show both lines and points
        # 'lines' creates a smooth continuous chart

        name='Download',
        # Legend label for this trace
        # Appears in the legend box (top of graph)
        # User can click to show/hide this line

        line=dict(color='#00d4ff', width=2),
        # line styling using a dictionary
        # color: #00d4ff (cyan, matching download theme)
        # width: 2 (pixel width of the line - thin but visible)
        # dict() creates a Python dictionary: {'color': '...', 'width': 2}

        fill='tozeroy',
        # fill creates an area fill under the line
        # 'tozeroy' means "fill from line down to y=0 (x-axis)"
        # This creates the shaded area effect seen in professional dashboards
        # Makes it easier to compare relative magnitudes visually

        fillcolor='rgba(0, 212, 255, 0.2)'
        # Color of the filled area
        # rgba() format: Red, Green, Blue, Alpha (transparency)
        # rgba(0, 212, 255, 0.2) = cyan at 20% opacity
        # Why transparent? Allows seeing both areas when they overlap
        # RGB values (0, 212, 255) match the hex #00d4ff from line color
    ))

    # -------------------------------------------------------------------------
    # ADD UPLOAD SPEED LINE (PURPLE)
    # -------------------------------------------------------------------------
    fig_speed.add_trace(go.Scatter(
        # Second trace added to the same figure (creates overlay)
        # Both lines will appear on the same graph with shared x/y axes

        x=history_data['timestamps'],
        # Same timestamps as download (synchronized time axis)

        y=history_data['upload_speeds'],
        # Upload speeds from the history data
        # Typically lower values than download (asymmetric connections)

        mode='lines',
        # Same as download - continuous line chart

        name='Upload',
        # Legend label distinguishes this from download line
        # Both "Download" and "Upload" appear in legend

        line=dict(color='#a855f7', width=2),
        # Purple color (#a855f7) used consistently for upload
        # Same width as download line (2px) for visual balance

        fill='tozeroy',
        # Same fill style as download (fill to x-axis)
        # Both filled areas visible due to transparency

        fillcolor='rgba(168, 85, 247, 0.2)'
        # Purple fill at 20% opacity
        # RGB (168, 85, 247) = hex #a855f7
        # Transparency allows both filled areas to be visible simultaneously
    ))

    # -------------------------------------------------------------------------
    # CONFIGURE GRAPH LAYOUT AND STYLING
    # -------------------------------------------------------------------------
    fig_speed.update_layout(
        # .update_layout() modifies the overall graph appearance
        # This controls axes, margins, legend, size, etc.

        xaxis_title="Time",
        # Label for the horizontal (x) axis
        # Shows users what the horizontal dimension represents

        yaxis_title="Speed (MB/s)",
        # Label for the vertical (y) axis
        # MB/s = Megabytes per second (data transfer rate)

        hovermode='x unified',
        # Controls hover tooltip behavior when mouse moves over graph
        # 'x unified': All traces (download + upload) shown in single tooltip
        # When hovering over a time point, see both speeds simultaneously
        # Alternative modes: 'closest', 'x', 'y' (less useful for comparison)

        height=400,
        # Graph height in pixels
        # 400px provides good visibility without dominating the page
        # Width is controlled by use_container_width parameter below

        margin=dict(l=0, r=0, t=0, b=0),
        # Margins around the graph (left, right, top, bottom)
        # All set to 0 for maximum use of available space
        # Streamlit container provides its own padding
        # dict(l=0, r=0, t=0, b=0) creates: {'l': 0, 'r': 0, 't': 0, 'b': 0}

        legend=dict(
            # Legend configuration (the box showing "Download" and "Upload")

            orientation="h",
            # "h" = horizontal (legend items side-by-side)
            # Alternative: "v" = vertical (stacked)
            # Horizontal saves vertical space, works well with 2 items

            yanchor="bottom",
            # Anchor point for y positioning
            # "bottom" means y position refers to bottom edge of legend

            y=1.02,
            # Vertical position (1.0 = top of graph, 0 = bottom)
            # 1.02 places legend slightly ABOVE the graph (outside plot area)
            # Prevents legend from obscuring data

            xanchor="right",
            # Anchor point for x positioning
            # "right" means x position refers to right edge of legend

            x=1
            # Horizontal position (1.0 = right side, 0 = left side)
            # Places legend at right edge of graph
            # Combined with anchors: legend appears top-right, outside plot area
        )
    )

    # -------------------------------------------------------------------------
    # DISPLAY THE COMPLETED GRAPH
    # -------------------------------------------------------------------------
    st.plotly_chart(fig_speed, use_container_width=True)
    # .plotly_chart() renders the Plotly figure in Streamlit
    # Parameters:
    #   - fig_speed: The figure object created above
    #   - use_container_width=True: Graph expands to fill container width
    #     Without this, graph would have fixed width (might be too narrow)
    # Plotly charts are interactive by default:
    #   - Hover to see exact values
    #   - Click legend items to show/hide lines
    #   - Drag to zoom, double-click to reset
    #   - Pan by dragging (if zoomed)

else:
    # This block executes if len(history_data['timestamps']) == 0
    # Happens when dashboard first loads (no data collected yet)

    st.info("Collecting data... Graph will appear after a few updates.")
    # .info() displays a blue informational message box
    # Explains why graph isn't showing (prevents user confusion)
    # After a few auto-refreshes, data accumulates and graph appears
    # Message disappears automatically when data is available

# ============================================================================
# STEP 8: DEVICES CURRENTLY CONNECTED
# ============================================================================
# This section displays a detailed table of all devices on the network
# Shows comprehensive device information in an interactive, sortable table format
# Table content adapts based on whether user selected "All Devices" or specific device

# Change header based on selection
if selected_device != "All Devices":
    # User is viewing a specific device - use singular form
    st.subheader("Current Device")
    # .subheader() creates a medium-sized heading (HTML <h2>)
    # "Current" emphasizes this is showing the selected device only
else:
    # User is viewing all devices - use plural form
    st.subheader("Devices Currently Connected")
    # Different wording provides context about what the table shows
    # "Currently Connected" clarifies this is a real-time snapshot

# SELECT COLUMNS TO DISPLAY
# DataFrame (df_filtered) contains many columns - not all are needed in UI
# This selects specific columns and defines their display order
display_df = df_filtered[[
    # Double brackets [[ ]] syntax: selects multiple columns, returns DataFrame
    # Single brackets [ ] would select one column, return Series
    # Column names must exactly match those in df_filtered

    'name',              # Device name (e.g., "Home Desktop PC", "User iPhone")
                        # Generated by Faker library to sound realistic

    'type',              # Device type (e.g., "Desktop", "Mobile", "Tablet", "IoT")
                        # Categorizes device for easier network management

    'ip',                # IP address on local network (e.g., "192.168.1.5")
                        # Private IP assigned by DHCP (router)

    'mac',               # MAC address (hardware identifier)
                        # Format: AA:BB:CC:DD:EE:FF (6 hexadecimal pairs)

    'connection_type',   # "Wired" or "Wi-Fi"
                        # Important for troubleshooting speed issues
                        # Wired = faster/stable, Wi-Fi = slower/variable

    'status',            # "ONLINE" or "OFFLINE"
                        # Current connectivity state
                        # Randomly toggled by data generator to simulate real behavior

    'Download (MB)',     # Download traffic in megabytes (cumulative)
                        # Converted from bytes in STEP 6A
                        # Shows total data received by device since tracking started

    'Upload (MB)',       # Upload traffic in megabytes (cumulative)
                        # Shows total data sent by device

    'last_seen'          # Timestamp of last activity
                        # Format: "2025-11-30 17:45:23" (datetime string)
                        # Useful for identifying inactive devices
]]
# Result: display_df contains only these 9 columns in this exact left-to-right order
# Original df_filtered remains unchanged (still has all columns)

# -------------------------------------------------------------------------
# DISPLAY THE TABLE WITH CUSTOM CONFIGURATION
# -------------------------------------------------------------------------
st.dataframe(
    # .dataframe() creates an interactive table widget
    # Features: sorting (click column headers), scrolling, resizing columns
    # Streamlit automatically handles rendering and interactivity

    display_df,
    # First argument: The DataFrame to display (created above)
    # Contains 9 columns with filtered device data

    use_container_width=True,
    # Make table expand to fill available horizontal space
    # Without this: table has fixed narrow width (bad UX on wide screens)
    # With this: table uses full width of Streamlit container (responsive)

    column_config={
        # Dictionary that customizes how each column appears
        # Keys: column names from DataFrame
        # Values: display names OR column configuration objects

        "name": "Device Name",
        # Simple string mapping: rename "name" to "Device Name"
        # More descriptive for end users

        "type": "Type",
        # Capitalize for consistency ("type" becomes "Type")

        "ip": "IP Address",
        # Expand abbreviation for clarity

        "mac": "MAC Address",
        # Expand abbreviation (MAC = Media Access Control)

        "connection_type": "Connection",
        # Shorten to save horizontal space in table header
        # Still clear what it represents (Wired vs Wi-Fi)

        "status": "Status",
        # No change needed (already clear)

        "Download (MB)": st.column_config.NumberColumn("Download (MB)", format="%.2f MB"),
        # NumberColumn is a special configuration object for numeric data
        # Parameters:
        #   - First argument: Display name for column header
        #   - format="%.2f MB": How to format the numbers
        #     %.2f = floating point with 2 decimal places
        #     MB suffix added to each cell value
        #     Example: 5.234567 displays as "5.23 MB"
        # NumberColumn enables features like right-alignment and numeric sorting

        "Upload (MB)": st.column_config.NumberColumn("Upload (MB)", format="%.2f MB"),
        # Same formatting as Download for consistency
        # Both traffic columns appear with MB suffix and 2 decimals

        "last_seen": "Last Seen"
        # Timestamp column - clearer with capital letters and space
    },
    # Result: Table displays with user-friendly column headers and formatted numbers

    hide_index=True
    # Streamlit tables show row numbers (0, 1, 2...) by default
    # hide_index=True removes this column
    # Why? Row numbers aren't meaningful for device data
    # Cleaner appearance without unnecessary column
)

# ============================================================================
# STEP 9: GLOBAL TRAFFIC MAP (PLOTLY) - Only show for "All Devices"
# ============================================================================
# This section creates an interactive geographic map showing external connection origins
# Visualizes where in the world external servers are located
# ONLY displayed when viewing "All Devices" (hidden in single device view)
# Provides security awareness (detect suspicious foreign connections)

if selected_device == "All Devices":
    # Conditional: Map only shown in aggregate view, not single device view
    # Why? Map shows network-wide external connections, not device-specific
    # Single device view focuses on that device's details, not geography

    st.markdown("### Global Traffic Origins")
    # Section heading - indicates geographic visualization follows

    st.markdown("Live map of external servers communicating with your network.")
    # Explanatory subtitle helps users understand what they're seeing
    # "External servers" = computers outside the local network
    # Could be: websites, APIs, CDNs, cloud services, etc.

    # -------------------------------------------------------------------------
    # FETCH CONNECTION DATA
    # -------------------------------------------------------------------------
    connections = st.session_state.traffic_generator.generate_external_connections()
    # Call data generator method to create simulated external connection points
    # Returns a list of dictionaries, each representing one connection:
    # Example: [{'lat': 37.7749, 'lon': -122.4194}, {'lat': 51.5074, 'lon': -0.1278}, ...]
    # Geographic distribution (built into generator):
    #   - 50% United States (simulates domestic traffic)
    #   - 10% China (represents Asian traffic)
    #   - 10% Russia (represents Eastern European traffic)
    #   - 30% European Union (represents Western European traffic)
    # This weighted distribution simulates realistic global internet patterns

    # Convert to DataFrame for Plotly
    map_df = pd.DataFrame(connections)
    # Plotly expects DataFrame format (not list of dicts)
    # Conversion creates a table with 'lat' and 'lon' columns
    # Example DataFrame:
    #       lat        lon
    #   0   37.7749    -122.4194
    #   1   51.5074    -0.1278
    #   2   39.9042    116.4074
    # Each row = one point on the map

    # -------------------------------------------------------------------------
    # CREATE PLOTLY GEOGRAPHIC SCATTER PLOT
    # -------------------------------------------------------------------------
    fig = px.scatter_geo(
        # px.scatter_geo() creates a scatter plot overlaid on a world map
        # px = plotly.express (high-level API, easier than graph_objects)
        # Each data point appears as a marker on the map at its lat/lon coordinates

        map_df,
        # DataFrame containing the connection data (latitude/longitude pairs)

        lat='lat',
        # Column name for latitude values
        # Latitude: -90 (South Pole) to +90 (North Pole)
        # Example: 37.7749 = San Francisco, CA

        lon='lon',
        # Column name for longitude values
        # Longitude: -180 (West) to +180 (East) from Prime Meridian
        # Example: -122.4194 = San Francisco, CA (West of Greenwich)

        projection='equirectangular',
        # Map projection type (how 3D globe is flattened to 2D)
        # 'equirectangular': Simple rectangular projection (lat/lon as x/y grid)
        # Pros: Familiar appearance, good for global view, no distortion at equator
        # Cons: Distorts size near poles (Greenland looks huge)
        # Alternatives: 'orthographic' (globe), 'natural earth' (curved)

        title='',
        # No title in the figure itself (empty string)
        # Title already provided by st.markdown() above
        # Avoids redundant labeling

        height=450
        # Map height in pixels
        # 450px provides good visibility without dominating the page
        # Width controlled by use_container_width (below)
    )

    # -------------------------------------------------------------------------
    # CUSTOMIZE MAP MARKER APPEARANCE
    # -------------------------------------------------------------------------
    fig.update_traces(
        # .update_traces() modifies the data points (markers) on the map
        # Changes how each connection point is rendered

        marker=dict(
            # marker is a dictionary defining point appearance

            size=10,
            # Radius of each circular marker in pixels
            # 10px is large enough to see clearly but not overwhelming
            # All markers same size (no size variation based on data)

            color='#00d4ff',
            # Marker fill color: cyan (#00d4ff)
            # Matches download color theme throughout dashboard
            # Creates visual consistency across all visualizations

            opacity=0.8,
            # Transparency level (0 = fully transparent, 1 = fully opaque)
            # 0.8 = 80% opaque, 20% transparent
            # Why transparent? Allows seeing overlapping markers
            # Dense regions (e.g., US East Coast) would obscure each other at 1.0

            line=dict(
                # Border around each marker (outline)

                width=1,
                # Border thickness in pixels
                # 1px thin outline provides definition without being heavy

                color='white'
                # White border creates contrast against dark map background
                # Makes markers more visible and distinct
                # Separates overlapping markers visually
            )
        )
    )

    # -------------------------------------------------------------------------
    # CUSTOMIZE MAP GEOGRAPHY (LAND, OCEAN, BORDERS)
    # -------------------------------------------------------------------------
    fig.update_geos(
        # .update_geos() configures the geographic map features
        # Controls what map elements are visible and how they're styled

        showcountries=True,
        # Display country borders on the map
        # True = borders visible (helps identify regions)
        # False = no borders (cleaner but harder to orient)

        countrycolor="rgba(100, 100, 100, 0.3)",
        # Color of country border lines
        # rgba(100, 100, 100, 0.3) = medium gray at 30% opacity
        # Subtle borders don't compete with cyan markers for attention

        showcoastlines=True,
        # Display coastlines (land/ocean boundaries)
        # Important for distinguishing continents and islands

        coastlinecolor="rgba(255, 255, 255, 0.3)",
        # Color of coastline borders
        # rgba(255, 255, 255, 0.3) = white at 30% opacity
        # Slightly brighter than country borders for distinction

        showland=True,
        # Display land masses (continents, islands)
        # True = land has fill color (defined below)

        landcolor="rgba(30, 30, 30, 0.8)",
        # Fill color for land areas
        # rgba(30, 30, 30, 0.8) = very dark gray at 80% opacity
        # Dark theme matches dashboard aesthetic
        # Slightly lighter than ocean for subtle contrast

        showocean=True,
        # Display ocean areas
        # True = ocean has fill color (defined below)

        oceancolor="rgba(10, 10, 30, 0.9)",
        # Fill color for ocean areas
        # rgba(10, 10, 30, 0.9) = very dark blue-gray at 90% opacity
        # Darker than land (oceans recede visually)
        # Slight blue tint distinguishes from land

        projection_type='equirectangular',
        # Reinforces the projection type set earlier
        # Ensures consistency if other code modifies it

        bgcolor='rgba(0,0,0,0)'
        # Background color of the map container
        # rgba(0,0,0,0) = black at 0% opacity = transparent
        # Allows Streamlit's background to show through
    )

    # -------------------------------------------------------------------------
    # CONFIGURE OVERALL FIGURE LAYOUT
    # -------------------------------------------------------------------------
    fig.update_layout(
        # .update_layout() controls the figure's outer container

        paper_bgcolor='rgba(0,0,0,0)',
        # "Paper" = the area surrounding the plot
        # rgba(0,0,0,0) = transparent
        # Integrates seamlessly with Streamlit's dark theme

        plot_bgcolor='rgba(0,0,0,0)',
        # "Plot" = the area where data is drawn
        # Also transparent for consistency

        geo=dict(bgcolor='rgba(0,0,0,0)')
        # Geographic subplot background
        # Another layer of background control
        # All set to transparent for clean integration
    )

    # -------------------------------------------------------------------------
    # DISPLAY THE COMPLETED MAP
    # -------------------------------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)
    # .plotly_chart() renders the Plotly figure in Streamlit
    # Parameters:
    #   - fig: The map figure created and configured above
    #   - use_container_width=True: Map expands to fill horizontal space
    # Interactive features:
    #   - Hover over markers to see exact coordinates
    #   - Zoom in/out with scroll or toolbar buttons
    #   - Pan by clicking and dragging
    #   - Reset view with home button in toolbar
    # Map provides visual security awareness:
    #   - Many connections from one country? Might be normal (US servers)
    #   - Unexpected connections from unusual countries? Worth investigating
    #   - Clustering in specific regions helps identify traffic patterns

# ============================================================================
# STEP 8.5: SECURITY ALERTS TABLE
# ============================================================================
# This section displays security warnings for suspicious network activity
# Helps identify potential threats: port scans, malware, unusual connections
# Alerts are generated randomly by the data generator (STEP 6G)
# Table is filtered based on device selection (show all or device-specific alerts)

st.markdown("### Suspicious Traffic Alerts")
# Section heading - "Suspicious" indicates these are potential security issues
# Users should investigate these alerts for network security

# -------------------------------------------------------------------------
# FILTER ALERTS BASED ON DEVICE SELECTION
# -------------------------------------------------------------------------
if selected_device != "All Devices":
    # User selected a specific device - show only that device's alerts
    # This helps focus on security issues for a particular device

    filtered_alerts = [alert for alert in st.session_state.security_alerts if alert['device'] == selected_device]
    # List comprehension: creates new list containing only matching alerts
    # Breakdown:
    #   - for alert in st.session_state.security_alerts: loop through all alerts
    #   - if alert['device'] == selected_device: keep only if device matches
    # Example: If selected_device = "Home PC", only alerts where device = "Home PC"
    # List comprehensions are Pythonic (concise, readable)
    # Alternative (more verbose):
    #   filtered_alerts = []
    #   for alert in st.session_state.security_alerts:
    #       if alert['device'] == selected_device:
    #           filtered_alerts.append(alert)
else:
    # User viewing "All Devices" - show all alerts across entire network
    filtered_alerts = st.session_state.security_alerts
    # No filtering needed - use the complete alert list
    # Shows comprehensive security picture for the network

# -------------------------------------------------------------------------
# DISPLAY ALERTS IF ANY EXIST
# -------------------------------------------------------------------------
if filtered_alerts:
    # Check if there are any alerts to display (non-empty list)
    # Empty list is "falsy" in Python (evaluates to False in if statement)
    # Non-empty list is "truthy" (evaluates to True)
    # -------------------------------------------------------------------------
    # CONVERT ALERTS TO DATAFRAME
    # -------------------------------------------------------------------------
    alerts_df = pd.DataFrame(filtered_alerts)
    # Convert list of dictionaries to pandas DataFrame for easy manipulation
    # Each dictionary becomes a row, dictionary keys become column names
    # Example input: [{'timestamp': ..., 'device': 'PC', 'severity': 'High'}, ...]
    # Example output: DataFrame with columns: timestamp, device, external_ip, reason, severity

    # -------------------------------------------------------------------------
    # FORMAT TIMESTAMP FOR READABILITY
    # -------------------------------------------------------------------------
    alerts_df['Time'] = alerts_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # Create new 'Time' column with formatted timestamp string
    # .dt.strftime() is pandas datetime accessor for formatting
    # %Y-%m-%d %H:%M:%S format:
    #   - %Y: 4-digit year (2025)
    #   - %m: 2-digit month (11)
    #   - %d: 2-digit day (30)
    #   - %H: 24-hour (17)
    #   - %M: minutes (45)
    #   - %S: seconds (23)
    # Result: "2025-11-30 17:45:23" (human-readable)

    # -------------------------------------------------------------------------
    # SELECT AND RENAME COLUMNS FOR DISPLAY
    # -------------------------------------------------------------------------
    display_alerts = alerts_df[['Time', 'device', 'external_ip', 'reason', 'severity']]
    # Select only columns needed for the table (hide internal fields)
    # Order: Time first (chronological), then device, IP, alert type, severity

    display_alerts.columns = ['Time', 'Device', 'External IP', 'Alert Type', 'Severity']
    # Rename columns for professional appearance
    # .columns assignment replaces ALL column names in order
    # 'reason' becomes 'Alert Type' (more descriptive)
    # Capitalization for consistency

    # -------------------------------------------------------------------------
    # DEFINE SEVERITY HIGHLIGHTING FUNCTION
    # -------------------------------------------------------------------------
    def highlight_severity(row):
        # Function to apply conditional row styling based on severity
        # Called by pandas .style.apply() method (below)
        # Parameter: row = a pandas Series representing one table row
        # Returns: list of CSS style strings (one per column)

        if row['Severity'] == 'High':
            # High severity alerts (critical security threats)
            return ['background-color: #fee2e2; color: #991b1b'] * len(row)
            # Background: #fee2e2 (light red/pink)
            # Text color: #991b1b (dark red)
            # * len(row) repeats the style string for EACH column in the row
            # All columns get the same styling (entire row highlighted)
            # Red = danger, urgency, immediate attention needed

        elif row['Severity'] == 'Medium':
            # Medium severity alerts (potential issues, worth investigating)
            return ['background-color: #fef3c7; color: #92400e'] * len(row)
            # Background: #fef3c7 (light yellow/cream)
            # Text color: #92400e (dark orange-brown)
            # Yellow = warning, caution, monitor situation
            # Less urgent than red but still important

        else:
            # Low severity or other (informational, routine)
            return [''] * len(row)
            # Empty string = no special styling
            # Uses default table appearance (white background, dark text)
            # Doesn't distract from high/medium priority alerts

    # -------------------------------------------------------------------------
    # APPLY STYLING TO DATAFRAME
    # -------------------------------------------------------------------------
    styled_df = display_alerts.style.apply(highlight_severity, axis=1)
    # .style creates a Styler object (allows conditional formatting)
    # .apply(function, axis=1) applies function to each row
    #   - axis=1 means row-wise (each row passed to function)
    #   - axis=0 would be column-wise (each column passed)
    # highlight_severity function returns CSS for each row
    # Result: DataFrame with color-coded rows based on severity

    # -------------------------------------------------------------------------
    # DISPLAY STYLED ALERTS TABLE
    # -------------------------------------------------------------------------
    st.dataframe(
        # Render the styled DataFrame with color-coded rows

        styled_df,
        # The Styler object created above (contains data + styling rules)

        use_container_width=True,
        # Table expands to fill horizontal space (responsive design)

        column_config={
            # Fine-tune column appearance (widths, types)

            "Time": st.column_config.TextColumn("Time", width="medium"),
            # Medium width for timestamp (enough for "YYYY-MM-DD HH:MM:SS")

            "Device": st.column_config.TextColumn("Device", width="medium"),
            # Medium width for device name

            "External IP": st.column_config.TextColumn("External IP", width="medium"),
            # Medium width for IP address (xxx.xxx.xxx.xxx)

            "Alert Type": st.column_config.TextColumn("Alert Type", width="large"),
            # Large width for alert description (can be long text)
            # Examples: "Port scan detected", "Malware connection attempt"

            "Severity": st.column_config.TextColumn("Severity", width="small")
            # Small width - just "High", "Medium", or "Low"
            # Color coding makes severity obvious, width can be minimal
        },

        hide_index=True
        # Don't show row numbers (not meaningful for alerts)
    )

    # -------------------------------------------------------------------------
    # ALERT SUMMARY METRICS
    # -------------------------------------------------------------------------
    # Display quick statistics about alerts using metric cards
    # Helps users quickly assess security situation

    high_alerts = len([a for a in filtered_alerts if a['severity'] == 'High'])
    # List comprehension: count alerts with 'High' severity
    # Breakdown:
    #   - [a for a in filtered_alerts if ...]: create list of matching alerts
    #   - len(...): count how many alerts match
    # Could also use: sum(1 for a in filtered_alerts if a['severity'] == 'High')

    medium_alerts = len([a for a in filtered_alerts if a['severity'] == 'Medium'])
    # Same pattern for medium severity alerts
    # Low severity alerts not counted (less important)

    col_alert1, col_alert2, col_alert3 = st.columns(3)
    # Three equal-width columns for summary metrics

    col_alert1.metric("Total Alerts", len(filtered_alerts))
    # First metric: total count of all alerts (high + medium + low)
    # len(filtered_alerts) counts all items in the list

    col_alert2.metric("High Severity", high_alerts, delta=None, delta_color="inverse")
    # Second metric: count of high severity alerts only
    # delta=None: no change indicator (arrow up/down)
    # delta_color="inverse": if delta shown, red=good, green=bad (inverse of normal)
    #   - Normal: green=increase (good for revenue), red=decrease (bad)
    #   - Inverse: green=decrease (good for alerts), red=increase (bad)
    # Not used here (delta=None) but included for future expansion

    col_alert3.metric("Medium Severity", medium_alerts)
    # Third metric: count of medium severity alerts
    # No delta parameters (simpler than high severity metric)

else:
    # This block executes if filtered_alerts is empty (no alerts to display)
    # Happens when: no alerts generated OR selected device has no alerts

    # -------------------------------------------------------------------------
    # NO ALERTS MESSAGE
    # -------------------------------------------------------------------------
    if selected_device != "All Devices":
        # User viewing specific device with no alerts
        st.info(f"No suspicious traffic detected from {selected_device}.")
        # F-string includes device name for context
        # .info() creates blue informational box (not green success - neutral)
        # "From {selected_device}" clarifies this is device-specific, not network-wide

    else:
        # User viewing "All Devices" with no alerts across entire network
        st.info("No suspicious traffic detected. Your network appears secure.")
        # Generic message (no device name)
        # "Network appears secure" provides reassurance
        # Note: This is simulated data, in production would be based on real analysis

# ============================================================================
# STEP 10: AUTO-REFRESH LOGIC
# ============================================================================
# This section implements the "Live Updates" feature
# Creates a continuous refresh loop when enabled by the user
# Allows dashboard to update automatically without manual interaction
# Essential for real-time monitoring scenarios

if auto_refresh:
    # Check if user enabled "Enable Live Updates" checkbox in sidebar
    # auto_refresh is a boolean (True/False) from st.sidebar.checkbox() in STEP 4
    # If True: execute this block (enable auto-refresh)
    # If False: skip this block (dashboard stays static until user interacts)

    # -------------------------------------------------------------------------
    # PAUSE EXECUTION
    # -------------------------------------------------------------------------
    time.sleep(refresh_rate)
    # time.sleep(seconds) pauses the program for the specified duration
    # refresh_rate comes from the slider in STEP 4 (1-10 seconds)
    # This creates the delay between automatic updates
    # Example: If refresh_rate = 3, dashboard waits 3 seconds before updating
    # During sleep:
    #   - Script execution is paused
    #   - Dashboard remains visible to user
    #   - No CPU usage (efficient waiting)
    # Why pause? Prevents excessive refresh (CPU usage, API rate limits, readability)

    # -------------------------------------------------------------------------
    # TRIGGER COMPLETE SCRIPT RERUN
    # -------------------------------------------------------------------------
    st.rerun()
    # st.rerun() restarts script execution from the very top (line 1)
    # Streamlit's execution model explained:
    #   1. Script runs top to bottom when user interacts
    #   2. st.rerun() manually triggers a new run (simulates interaction)
    #   3. All code executes again: data fetching, calculations, displays
    #   4. Session state persists (traffic_history, security_alerts, etc.)
    #
    # This creates an infinite loop:
    #   Run script, Display dashboard, Sleep N seconds, Rerun, Repeat
    #
    # Loop continues until:
    #   - User unchecks "Enable Live Updates" (auto_refresh becomes False)
    #   - User closes the browser tab
    #   - Streamlit server stops
    #
    # Each rerun:
    #   - Fetches new device data (traffic, status, speeds)
    #   - Updates traffic history (adds new data points)
    #   - Possibly generates new security alerts
    #   - Re-renders ALL visualizations with fresh data
    #
    # IMPORTANT: Without the time.sleep(), this would refresh instantly and continuously
    # Result: CPU maxed out, UI flickering, unusable dashboard
    # The sleep creates controlled, user-defined refresh intervals

# ============================================================================
# END OF SCRIPT
# ============================================================================
# If auto_refresh is False (Live Updates disabled):
#   - Script reaches this point and stops
#   - Dashboard displays static snapshot of data
#   - Only updates when user interacts (change dropdown, slider, etc.)
#
# If auto_refresh is True (Live Updates enabled):
#   - st.rerun() is called (above)
#   - Script never actually reaches this point
#   - Rerun happens before reaching the end
#   - Creates continuous refresh loop