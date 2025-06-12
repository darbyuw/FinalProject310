# FinalProject310

Welcome to Route Rhythms! The perfect playlist generator for your commute.
This web app takes user input for a starting location, ending location, type of travel, and a word 
to describe the desired playlist. Then it creates a Spotify playlist that is the same length as the duration of the 
travel time to get from the start location to the end location via the mode of travel. 
The web app displays the created playlist title, image, and description. The user can click on the image or button 
to open the Spotify playlist. The playlist will be saved to the user's library. 

## Important Info
This Flask app creates a playlist in your Spotify library. Be aware that sending the form multiple times will create 
multiple new playlists. Spotify allows each user to have 10,000 playlists on their account. 

NOTE: This program takes a long time to run because it has to add and remove songs from a playlist until it reaches the 
desired length. Be aware that you may have to wait a few minutes for it to finish. 

I recommend opening the site in Google Chrome rather than Safari. I had several issues opening it in Safari when the 
session expired. This is not be a problem if only running the program once. 

The form fields expect you to enter an address or location for the start and end locations. 

## Getting API Keys
Both the Spotify API and the OpenRouteService API require API keys. 

First create a hidden file called projectsecrets.py and create a variable called app_secret and enter a random app secret.

To get the API key for the Spotify Search API, you can follow the instructions on this page:
https://developer.spotify.com/documentation/web-api/tutorials/getting-started

The process does not take long, however, you must have a Spotify account (free or premium).

First, log onto the Spotify Development Dashboard using your Spotify account.
Dashboard can be found here: https://developer.spotify.com/dashboard

Navigate to the Dashboard (under the dropdown under your name in the upper right corner).
Click "Create an app" and enter the following info:
App Name: My App
App Description: This is my first Spotify app
Redirect URI: You won't need this parameter in this example, so let's use http://127.0.0.1:3000

You need two keys which can be found by navigating to your Dashboard and clicking on the app you just created.
The Client ID can be found here. The Client Secret can be found behind the View client secret link.

Paste these into the hidden projectsecrets.py file in variables called "spotify_client_id" and "spotify_client_secret".

To get the API key for the OpenRouteService API, go to this page: 
https://openrouteservice.org/dev/#/api-docs?loginSuccessful=true
and click "log in" in the upper right corner. Sign up with a free OpenRouteService account which requires an email and 
password and your name. 

It will then take you to a page with your API key and profile information. At the top, next to "Basic Key:" copy your API
key. Then paste this key into a variable in the hidden projectsecrets.py file called "openroute_service_key". 
