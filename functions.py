# functions called by app.py
from flask import jsonify
import urllib.request
import urllib.parse
import base64
import json
import projectsecrets

# todo: pass the token into each of these functions instead of calling

# This function returns a list of dictionaries of playlists on Spotify from the query: walking.
def search_walking_playlists(access_token):
    # access_token = get_access_token()
    # if not access_token:
    #     return jsonify({"error": "Failed to get access token"}), 500

    query = urllib.parse.urlencode({
        "q": "walking",
        "type": "playlist",
        "market": "US",
        "limit": 10
    })
    url = f"https://api.spotify.com/v1/search?{query}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as res:
            res_data = res.read()
            data = json.loads(res_data)

            print(json.dumps(data, indent=2))  # Debugging output

            playlists = []
            for item in data.get("playlists", {}).get("items", []):
                if item and "name" in item and "owner" in item and "external_urls" in item:
                    playlists.append({
                        "name": item["name"],
                        "owner": item["owner"].get("display_name", "Unknown"),
                        "url": item["external_urls"].get("spotify", ""),
                        "tracks": item["tracks"],
                        "id": item["id"]
                    })

            return playlists

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTPError {e.code}: {error_body}")
        return jsonify({"error": f"HTTPError {e.code}", "details": error_body}), e.code
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500



# This function gets the length in ms of each song within the playlist
# and then adds up the total length of the playlist and returns the value in seconds.
def get_length_tracks(playlist, access_token):
    # access_token = get_access_token()
    # if not access_token:
    #     return jsonify({"error": "Failed to get access token"}), 500
    print("Went inside get_length_tracks")
    # TODO: add some print statements to see if it even gets to here !!
    # put the url together for the API call:
    playlist_id = playlist[0]["id"]
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    # i think we have to call the API to get the playlist list of tracks from the href
        # and then we have to use the Get Track to get info on each track
    # get the list of tracks:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    request1 = urllib.request.Request(playlist_url, headers=headers)
    # data = request1.json() # todo: do we do this line or the one below with json.loads?? whats the diff??

    try:
        with urllib.request.urlopen(request1) as res:
            print("inside try")
            res_data = res.read()
            playlists = json.loads(res_data) # todo: not exactly sure what this line does so might not work
            # get the tracks from the track list in playlist:
            tracks = []
            for item in playlists.get("playlists", {}).get("items", []): # todo: playlists might not be the correct object to call .get on
                print("inside loop") # todo: ask chat why its not working and show your code !!
                if item and "track" in item:
                    tracks.append({
                        "id": item["track"]["id"]
                    })
                    print("Went inside for loop")
                else:
                    print(f"Error: {item}")
    except urllib.error.HTTPError as e:
        print("Failed to get access token: {}".format(e))

    # the following loop uses the Get Track API to get info on each track in the above list of tracks
    total_time = 0
    for track in tracks:
        # put the url together for the API call:
        track_id = track["id"]
        track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
        headers = {
            "Authorization": f"Bearer {access_token}" # todo: do i need a new access token every time we make an API call??
        }
        # make request to get track info
        request2 = urllib.request.Request(track_url, headers=headers)
        # data = request2.json()


        try:
            with urllib.request.urlopen(request1) as res:
                res_data = res.read()
                track = json.loads(res_data)  # todo: not exactly sure what this line does so might not work
                # add the length of the track to the total playlist duration
                track_duration = track.get("duration_ms", {})
                total_time += track_duration
                return total_time
        except urllib.error.HTTPError as e:
            print("Failed to get access token: {}".format(e))