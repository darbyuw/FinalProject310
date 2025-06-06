import json
import projectsecrets
import pprint

from flask import Flask, redirect, session, url_for, render_template, request, jsonify
from authlib.integrations.flask_client import OAuth

from functions import get_length_tracks, get_travel_duration, search_playlists

from projectsecrets import app_secret, spotify_client_id, spotify_client_secret
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
        print(request.args)
    except KeyError:
        return redirect(url_for("login"))

    # print("OAUTH:")
    # print(dir(oauth.spotify))
    #
    access_token = session["spotify-token"]["access_token"]
    # print("Access Token:", access_token)
    get_length_tracks(access_token)

    return render_template("index.html", x=get_length_tracks(access_token))

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    print("Redirect URI being sent to Spotify: ", redirect_uri)
    return oauth.spotify.authorize_redirect(redirect_uri)

@app.route("/spotifyauthorize")
def authorize():
    print("Request args:", request.args)
    try:
        token = oauth.spotify.authorize_access_token()
        print("Token received:", token)
        session["spotify-token"] = token
        return redirect(url_for('index'))
    except Exception as e:
        print("OAuth token error:", e)
        return f"OAuth token error: {e}", 400

# --------------------------------------------------- MY PAGES --------------------------------------------------
@app.route('/about')
def about():
    with urllib.request.urlopen('https://depts.washington.edu/ledlab/teaching/is-it-raining-in-seattle/') as response:
        is_it_raining_in_seattle = response.read().decode()

    if is_it_raining_in_seattle == "true":
        return render_template("index.html", x="Yes")
    else:
        return render_template("index.html", x="No")

# a page for getting the playlist
@app.route('/getplaylist')
def printplaylists():
    # get the playlist:
    playlists = search_playlists()
    # get info from each track
    time = get_length_tracks(playlists)

    return render_template("index.html", x=time)


@app.route('/maps')
def maps():
    return "maps"