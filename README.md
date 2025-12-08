#### INF601 - Advanced Programming in Python
#### Jeremy McKowski
#### Final Project


# Ubiquiti Network Monitor Dashboard

## Description

This web application is designed to display a live dashboard of a home network simulating a Ubiquiti router.

Due to router API limitations, this application uses Python Faker library to generate realistic simulated network traffic data for demonstration purposes of a Ubiquiti Router.

## Getting Started

### Dependencies

This project requires Python 3.8+ and the following packages:

```
pip install -r requirements.txt
```

### Setup Instructions

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Configure AccuWeather API:**

An API key from AccuWeather is required for the weather widget. Create a `.env` file in your root project directory: [Accuweather.com API Key](https://developer.accuweather.com/)

### Executing Program

To start the Streamlit dashboard, run in your terminal:

```
streamlit run app.py
```

After running the command, the application will automatically open in your default browser at:
- **Local URL**: http://localhost:8502


### Using the Dashboard

1. **Enable Live Updates**: Toggle the "Enable Live Updates" checkbox in the sidebar to see real-time data updates
2. **Adjust Refresh Rate**: Use the slider in the sidebar to control update frequency (1-10 seconds)
3. **Monitor Devices**: View all connected devices and their traffic statistics in the Device Details table
4. **Watch for Alerts**: Security alerts appear below the global traffic map when suspicious activity is detected
5. **Track Throughput**: The 30-minute graph builds up over time showing network speed trends

## Output

This web-app allows users to view a real-time network monitoring dashbaord of their home network.

I've included a weather API to display CVE for Ubiquit Systems Router so a user can see the latest Critical Vulnerabilities that may affect their network security.

## Authors

Jeremy McKowski

## Acknowledgments

Inspiration, code snippets, and resources:
* [Jason Zeller](https://www.youtube.com/@profzeller) 
* [Streamlit Documentation](https://docs.streamlit.io/) - Web framework documentation
* [Plotly](https://plotly.com/python/) - Interactive visualization library
* [AccuWeather API](https://developer.accuweather.com/) - Weather data provider
* [AccuWeather Core Weather Quick Start](https://developer.accuweather.com/documentation/core-weather-quick-start) - API integration guide
* [Faker Documentation](https://faker.readthedocs.io/en/master/) - Realistic fake data generation
* [Watchdog](https://pypi.org/project/watchdog/) - File system monitoring library
* [Pandas](https://pandas.pydata.org/) - Data manipulation and analysis
* [Streamlit Cybersecurity Dashboard](https://github.com/ajitagupta/streamlit-cybersecurity-dashboard) - Dashboard inspiration
* [Cloud Security Dashboard](https://github.com/VisionHub25/cloud-security-dashboard) - Security monitoring concepts
* [Build a Real-Time Network Traffic Dashboard - FreeCodeCamp](https://www.freecodecamp.org/news/build-a-real-time-network-traffic-dashboard-with-python-and-streamlit/#heading-future-enhancements) - Tutorial and implementation guidance
* [Claude Support](https://claude.ai/share/6150eb89-40c3-488c-b223-945e21b6f85a)