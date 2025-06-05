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
    print("Access Token:", access_token)
    playlist = search_playlists(access_token, search)
    print(playlist)

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
            for item in playlists.get("playlists", {}).get("items", []):
                # print("inside loop")
                if item and "track" in item:
                    tracks.append({
                        "id": item["track"]["id"]
                    })
                    # print("Went inside for loop")
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
    return total_time



def main():
    # get_lat_lon(projectsecrets.openroute_service_key, "University of Washington, Seattle", "340 NW 47th St, Seattle, WA, 98107")

    print(get_travel_duration(projectsecrets.openroute_service_key, "driving-car", "575 Bellevue Square, Bellevue", "340 NW 47th St, Seattle, WA, 98107"))

if __name__ == "__main__":
    try:
        main()
    except (NameError, SyntaxError):
        pass
