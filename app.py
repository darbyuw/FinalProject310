from flask import Flask, redirect, session, url_for, render_template, request
from authlib.integrations.flask_client import OAuth

from functions import get_length_tracks, get_travel_duration, search_playlists, get_users_profile, \
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
    refresh_token_url="https://accounts.spotify.com/api/token",
    api_base_url="https://api.spotify.com/v1/",
    client_kwargs={
        'scope': 'user-read-private playlist-modify-private playlist-read-private',
        'token_endpoint_auth_method': 'client_secret_post'
    }
)
# --------------------------------------------------- PAGES --------------------------------------------------
@app.route("/")
def index():
    # access_token = get_token()
    # if not access_token:
    #     return redirect(url_for("login"))
    try:
        token = session["spotify-token"]["access_token"]
        #print(request.args)
    except KeyError:
        return redirect(url_for("login"))

    return render_template("index.html")

# def get_token():
#     token = session.get("spotify-token")
#     if token:
#         # If token is expired, try to refresh it
#         if oauth.spotify.token.is_expired(token):
#             try:
#                 new_token = oauth.spotify.refresh_token(
#                     url="https://accounts.spotify.com/api/token",
#                     refresh_token=token["refresh_token"]
#                 )
#                 session["spotify-token"] = new_token
#                 return new_token["access_token"]
#             except Exception as e:
#                 print("Error refreshing token:", e)
#                 return None
#         return token["access_token"]
#     return None

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    print("Redirect URI being sent to Spotify: ", redirect_uri)
    # return oauth.spotify.authorize_redirect(redirect_uri)
    return oauth.spotify.authorize_redirect(
        redirect_uri,
        show_dialog=True  # forces approval screen
    )

@app.route("/spotifyauthorize")
def authorize():
    # print("Request args:", request.args)
    try:
        token = oauth.spotify.authorize_access_token()
        print("Token received:", token)
        session["spotify-token"] = token
        return redirect(url_for('index'))
    except Exception as e:
        print("OAuth token error:", e)
        return f"OAuth token error: {e}", 400

@app.route('/results', methods=['GET', 'POST'])
def results():
    token = session["spotify-token"]["access_token"]
    if request.method == 'POST':
        travel_duration = get_travel_duration(openroute_service_key, request.form["start_location"],
                                              request.form["end_location"], request.form["travel_type_user"])
        user_id = get_users_profile(token)
        if request.form["search_term"]:
            rec_playlist = search_playlists(token, user_id, request.form["search_term"])
        else:
            rec_playlist = search_playlists(token, user_id)
        final_playlist = copy_playlist_into_library(token, user_id, rec_playlist, travel_duration)
        title = final_playlist[0]["title"]
        owner = final_playlist[0]["owner"]
        url = final_playlist[0]["url"]
        if final_playlist[0]["description"]:
            description = final_playlist[0]["description"]
        else:
            description = ""
        images = final_playlist[0]["images"][0]["url"]
        playlist_length = round(get_length_tracks(token, playlist=final_playlist), 2)
        return render_template("results.html", title=title, duration=travel_duration,
                               owner=owner, playlist_length=playlist_length, url=url, description=description, images=images,
                               start=request.form["start_location"], end=request.form["end_location"], travel=request.form["travel_type_user"])
    else:
        return "<html><head></head><body><p>HTTP 400 error: Wrong HTTP request method</p></body></html>"
