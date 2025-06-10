import json
import projectsecrets
import pprint

from flask import Flask, redirect, session, url_for, render_template, request, jsonify
from authlib.integrations.flask_client import OAuth

from functions import get_length_tracks, get_travel_duration, search_playlists, get_lat_lon, get_users_profile, \
    copy_playlist_into_library

from projectsecrets import app_secret, spotify_client_id, spotify_client_secret, openroute_service_key
app = Flask(__name__)
app.secret_key = app_secret

oauth = OAuth(app)
oauth.register(
    name="spotify",
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    authorize_url="https://accounts.spotify.com/authorize",
    access_token_url="https://accounts.spotify.com/api/token",
    api_base_url="https://api.spotify.com/v1/",
    client_kwargs={
        'scope': 'playlist-read-private user-top-read'
    }
)
# --------------------------------------------------- AUTHORIZE USER PAGES --------------------------------------------------
@app.route("/")
def index():
    try:
        token = session["spotify-token"]
        # print(request.args)
    except KeyError:
        return redirect(url_for("login"))

    # print("OAUTH:")
    # print(dir(oauth.spotify))
    #
    #access_token = session["spotify-token"]["access_token"]
    # print("Access Token:", access_token)
    #get_length_tracks(access_token)

    return render_template("index.html")

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    # print("Redirect URI being sent to Spotify: ", redirect_uri)
    return oauth.spotify.authorize_redirect(redirect_uri)

@app.route("/spotifyauthorize")
def authorize():
    print("Request args:", request.args)
    try:
        token = oauth.spotify.authorize_access_token()
        # print("Token received:", token)
        session["spotify-token"] = token
        return redirect(url_for('index'))
    except Exception as e:
        print("OAuth token error:", e)
        return f"OAuth token error: {e}", 400

@app.route('/results', methods=['GET', 'POST'])
def results():
    token = session["spotify-token"]
    if request.method == 'POST':
        travel_duration = get_travel_duration(openroute_service_key, request.form["start_location"], request.form["end_location"])
        user_id = get_users_profile(token)
        rec_playlist = search_playlists(token, request.form["search_term"])
        final_playlist = copy_playlist_into_library(token, user_id, rec_playlist, travel_duration)
            # todo: how to get playlist title, description and user for the results page??
        return render_template("results.html", playlist=final_playlist, legnth=travel_duration)
    else:
        return "<html><head></head><body><p>HTTP 400 error: Wrong HTTP request method</p></body></html>"

# --------------------------------------------------- MY PAGES --------------------------------------------------
# @app.route('/about')
# def about():
#     with urllib.request.urlopen('https://depts.washington.edu/ledlab/teaching/is-it-raining-in-seattle/') as response:
#         is_it_raining_in_seattle = response.read().decode()
#
#     if is_it_raining_in_seattle == "true":
#         return render_template("index.html", x="Yes")
#     else:
#         return render_template("index.html", x="No")
#
# # a page for getting the playlist
# @app.route('/getplaylist')
# def printplaylists():
#     # get the playlist:
#     playlists = search_playlists()
#     # get info from each track
#     time = get_length_tracks(playlists)
#
#     return render_template("index.html", x=time)
#
#
# @app.route('/maps')
# def maps():
#     return "maps"