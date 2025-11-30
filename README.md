#### INF601 - Advanced Programming in Python
#### Jeremy McKowski
#### Final Project


# Final Project

## Description

This web application is designed to display a live dashboard of a home network. 
It allows a user to have a stand alone display of the home network status, including live metrics to understand the network as well as 
alerts for unusual activity. For a fun bonus it will include the local weather conditions as well.

Due to some routers limitations, this application also uses Python Faker Data to generate fake data for the network dashboard.
It will be a stand in for an Ubiquiti router. 


## Getting Started

### Dependencies

To download all requirements:

```
pip install -r requirements.txt
```

### Executing program

To create the migration files for the database, run in your terminal:
```
python manage.py makemigrations
```
An API key from Accuweather is utilized in this project: please create a .env file in your root project directory and obtain an Accuweather API key.
```
https://developer.accuweather.com/
```
To apply the migrations to the database, run in your terminal:

To start the server, run in your terminal:
```
TEXT HERE NEEDED 
```

After running the server, visit http:// to start the server

### Output

This application displays a live dashboard of a users network.  
## Authors

Stephen Blomberg

## Acknowledgments

Inspiration, code snippets, etc.
* [Jason Zeller](https://www.youtube.com/@profzeller)
* [Django](https://docs.djangoproject.com/en/5.0/)
* [Jinja](https://jinja.palletsprojects.com/en/stable/)
* [Bootstrap](https://getbootstrap.com/)
* [AccuWeather](https://developer.accuweather.com/)
* [django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/)
* [ChatGPT](https://chatgpt.com/share/674e43eb-8b44-8002-a965-168b4ffb2b90)