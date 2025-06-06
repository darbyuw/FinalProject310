# functions called by app.py
from flask import jsonify
import urllib.request
import urllib.parse
import json
import projectsecrets
import requests
import pprint

# ---------------------------------------- OPEN ROUTE SERVICE API FUNCTIONS --------------------------------------------

# Returns a tuple containing the coordinates for the start location and the coordinates for the end location.
# Accepts an API key (str), a start destination (str), and an end destination (str).
def get_lat_lon(key, start_destination, end_destination):

    query = urllib.parse.urlencode({
        "api_key": key,
        "text": start_destination,
    })

    url = f"https://api.openrouteservice.org/geocode/search?{query}"
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    call = requests.get(url, headers=headers) # todo: put this within a try/except block

    # pprint.pprint(call.json())
    # print("Here are the start coordinates:", call.json()['features'][0]['geometry']['coordinates'])

    query2 = urllib.parse.urlencode({
        "api_key": key,
        "text": end_destination,
    })

    url2 = f"https://api.openrouteservice.org/geocode/search?{query2}"
    headers2 = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    call2 = requests.get(url2, headers=headers2)

    # print("Here are the end coordinates:", call2.json()['features'][0]['geometry']['coordinates'])
    return [call.json()['features'][0]['geometry']['coordinates'], call2.json()['features'][0]['geometry']['coordinates']]

# Returns the duration in minutes of the travel time from the start destination to the end destination. Rounds down.
def get_travel_duration(key, travel_type, start_destination, end_destination):

    travel_type = "driving-car" # todo: allow users to change this

    locations = get_lat_lon(key, start_destination, end_destination)

    body = {"locations": locations,
            "metrics": ["duration"]}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    call = requests.post('https://api.openrouteservice.org/v2/matrix/' + travel_type, json=body, headers=headers)

    # pprint.pprint(call.json())

    seconds = call.json()['durations'][0][1]
    minutes = int(seconds) // 60

    return minutes


# --------------------------------------------------- SPOTiFY API FUNCTIONS --------------------------------------------

# This function returns a list of dictionaries of playlists on Spotify from the query: walking.
def search_playlists(access_token, search="walking"):

    query = urllib.parse.urlencode({
        "q": search,
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

            # print(json.dumps(data, indent=2))  # Debugging output

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
def get_length_tracks(access_token, search="walking"):
    # print("Access Token:", access_token)
    playlist = search_playlists(access_token, search)
    # print(playlist)

    if not playlist:
        print("No playlists found.")
        return 0

    # put the url together for the API call:
    playlist_id = playlist[0]["id"]
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    # get the list of tracks:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    request1 = urllib.request.Request(playlist_url, headers=headers)

    try:
        with urllib.request.urlopen(request1) as res:

            res_data = res.read()
            playlists = json.loads(res_data)
            # get the tracks from the track list in playlist:
            tracks = []
            for item in playlists.get("items", []):
                # print("inside loop")
                # if item and "track" in item:
                #     tracks.append({
                #         "id": item["track"]["id"]
                #     })
                #     # print("Went inside for loop")
                # else:
                #     print(f"Error: {item}")
                track_info = item.get("track")
                if track_info and "id" in track_info:
                    tracks.append({
                        "id": track_info["id"]
                    })
                else:
                    print(f"Error or missing track info: {item}")
    except urllib.error.HTTPError as e:
        print("Failed to get access token: {}".format(e))

    # the following loop uses the Get Track API to get info on each track in the above list of tracks
    total_time = 0
    for track in tracks:
        # put the url together for the API call:
        track_id = track["id"]
        track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
        # make request to get track info
        request2 = urllib.request.Request(track_url, headers=headers)
        # data = request2.json()

        try:
            with urllib.request.urlopen(request2) as res:
                res_data = res.read()
                track_data = json.loads(res_data)
                # add the length of the track to the total playlist duration
                track_duration = track_data.get("duration_ms", 0)
                total_time += track_duration

        except urllib.error.HTTPError as e:
            print("Failed to get access token: {}".format(e))
    return total_time / 60000


# TODO: make a function for making the playlist longer or shorter
    # should this be two functions?? one function: pass in a playlist and it removes the last track, another function: pass in playlist, adds one track
        # but what track would it add?? maybe the first song that pops up when you do a search query for the search term (ex: "walking" songs)
    # step 1: Get Current User's Profile API to get the Spotify User ID (in order to create a playlist on their account)
    # step 2: save the recommended playlist to the user's account using Create Playlist API --> this creates an empty playlist
    # step 2: use loops to copy each track item into new playlist using Add Items to Playlist API
        # step 2.5: each time you add one of the tracks, check the new playlist length. Stop adding songs when you reach the desired length (ex: 15 min)
    # step 3: account for short playlists: if new playlist never reaches desired length --> use Search For Item API again
    # step 4: search for and return a song that fits the original query (ex: walking)
    # step 5: add this song to the short playlist and continue until you reach desired length
    # todo: find out if you can change hte travel_type to walking for the openroute service api
    # todo: consider allowing users to enter one word to describe the type of playlist they want


def get_users_profile(access_token):
    # Get Current User's Profile API to get the Spotify User ID (in order to create a playlist on their account)
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as res:
            res_data = res.read()
            data = json.loads(res_data)

            user_id = str(data["id"])
            return user_id

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTPError {e.code}: {error_body}")
        return jsonify({"error": f"HTTPError {e.code}", "details": error_body}), e.code
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def copy_playlist_into_library(access_token, user_id, rec_playlist):
    # save the recommended playlist to the user's account using Create Playlist API --> this creates an empty playlist
    body = urllib.parse.urlencode({
        "name": "Your New Perfect Length Playlist",
        "description": "A playlist corresponding to the length of your travel time.",
        "public": False
    })
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as res:
            res_data = res.read()
            data = json.loads(res_data)
            # get the playlist ID from the new playlist
            playlist_id = data["id"]

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

    # get each track id from rec_playlist to add to new playlist:
    playlist_id = rec_playlist[0]["id"]
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    req2 = urllib.request.Request(playlist_url, headers=headers)
    try:
        with urllib.request.urlopen(req2) as res:
            res_data = res.read()
            playlists = json.loads(res_data)
            # get the tracks from the track list in playlist:
            tracks = []
            for item in playlists.get("items", []):
                track_info = item.get("track")
                if track_info and "id" in track_info:
                    tracks.append({
                        "id": track_info["id"]
                    })
                else:
                    print(f"Error or missing track info: {item}")
    except urllib.error.HTTPError as e:
        print("Failed to get access token: {}".format(e))

    for track in tracks:
        # add track to new playlist using add items API

    # use loops to copy each track item into new playlist using Add Items to Playlist API
         # call get_length_tracks() each time you add one of the tracks. Stop adding songs when you reach the desired length (ex: 15 min)
    # account for short playlists: if new playlist never reaches desired length --> use Search For Item API again
        # add this song to the playlist and continue until you reach desired length
    # return playlist uri/id
    return None

def search_songs_to_extend_playlist(access_token):
    # search for and return a song that fits the original query (ex: walking)
    return None


def main():
    # get_lat_lon(projectsecrets.openroute_service_key, "University of Washington, Seattle", "340 NW 47th St, Seattle, WA, 98107")

    print(get_travel_duration(projectsecrets.openroute_service_key, "driving-car", "575 Bellevue Square, Bellevue", "340 NW 47th St, Seattle, WA, 98107"))

if __name__ == "__main__":
    try:
        main()
    except (NameError, SyntaxError):
        pass
