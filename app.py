import json
import projectsecrets

from flask import Flask, redirect, session, url_for, render_template, request, jsonify
from authlib.integrations.flask_client import OAuth

from functions import * # TODO: add this!

from projectsecrets import app_secret, spotify_client_id, spotify_client_secret
# TODO: USE THIS STRUCTURE WHEN MAKING USER ENTER THEIR TOKEN!!
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
    except KeyError:
        return redirect(url_for("login"))

    # todo: do stuff here ??
    # get user inputs for type of playlist, starting, and ending locations (potench also ask for type of plalist)
    # call the function that uses maps api to get duration of travel
    # call the function that gets a playlist
    # call the function that gets the length of the playlist
    # while playlist length is not within 15 seconds of the total_travel_time:
    # if that length is total_time + or - 15 seconds:
        # return the results page and display the playlist
    # else:
        # call the function that will remove one song from the playlist

    print(dir(oauth.spotify))
    data = oauth.spotify.get("me/top/tracks?limit=5", token=token).text
    return json.loads(data)

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    print(redirect_uri)
    return oauth.spotify.authorize_redirect(redirect_uri)


@app.route("/spotify-authorize")
def authorize():
    token = oauth.spotify.authorize_access_token()
    session["spotify-token"] = token
    return token

@app.route('/')
def index():
    x = "something"
    return render_template("index.html", x=x)

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
    playlists = search_walking_playlists()
    # get info from each track
    time = get_length_tracks(playlists)

    return render_template("index.html", x=time)


@app.route('/maps')
def maps():
    return "maps"