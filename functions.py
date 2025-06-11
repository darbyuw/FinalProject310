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
    call = requests.get(url, headers=headers)

    query2 = urllib.parse.urlencode({
        "api_key": key,
        "text": end_destination,
    })

    url2 = f"https://api.openrouteservice.org/geocode/search?{query2}"
    headers2 = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    call2 = requests.get(url2, headers=headers2)

    return [call.json()['features'][0]['geometry']['coordinates'], call2.json()['features'][0]['geometry']['coordinates']]

# Returns the duration in minutes of the travel time from the start destination to the end destination. Rounds down.
def get_travel_duration(key, start_destination, end_destination, travel_type_user):

    if travel_type_user == "Driving":
        travel_type = "driving-car"
    elif travel_type_user == "Walking":
        travel_type = "foot-walking"
    elif travel_type_user == "Biking":
        travel_type = "cycling-regular"


    locations = get_lat_lon(key, start_destination, end_destination)

    body = {"locations": locations,
            "metrics": ["duration"]}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    call = requests.post('https://api.openrouteservice.org/v2/matrix/' + travel_type, json=body, headers=headers)

    seconds = call.json()['durations'][0][1]
    minutes = int(seconds) // 60

    return minutes


# --------------------------------------------------- SPOTiFY API FUNCTIONS --------------------------------------------

# This function returns a list of dictionaries of playlists on Spotify from the query: walking.
def search_playlists(access_token, user_id, search="walking"):

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

            playlists = []
            for item in data.get("playlists", {}).get("items", []):
                if item and "name" in item and "owner" in item and "external_urls" in item:
                    if not item["owner"].get("id") == user_id:
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
        print(f"HTTPError during search for rec_playlist: {e.code}: {error_body}")
        return jsonify({"error": f"HTTPError {e.code}", "details": error_body}), e.code
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error during search for rec playlist: ": str(e)}), 500



# This function gets the length in ms of each song within the playlist
# and then adds up the total length of the playlist and returns the value in seconds.
def get_length_tracks(access_token, playlist):
    if not playlist:
        print("No playlists found.")
        return 0

    # put the url together for the API call:
    playlist_id = playlist[0]["id"]
    base_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    # get the list of tracks:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    total_time = 0
    next_url = base_url

    while next_url:
        request = urllib.request.Request(next_url, headers=headers)
        try:
            with urllib.request.urlopen(request) as res:
                res_data = res.read()
                data = json.loads(res_data)

                for item in data.get("items", []):
                    track = item.get("track")
                    if track and track.get("duration_ms") is not None:
                        total_time += track["duration_ms"]
                    else:
                        print(f"Skipped item with missing track or duration: {item}")

                # follow pagination
                next_url = data.get("next")

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"Rate limited. Retrying...")
                continue  # retry same request
            else:
                print(f"Failed to fetch playlist tracks: {e}")
                break
        except json.JSONDecodeError:
            print("Failed to parse JSON response.")
            break
    return total_time / 60000

# Use the Get Current User's Profile endpoint to get the Spotify User ID (in order to create a playlist on their account)
def get_users_profile(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as res:
            res_data = res.read()
            data = json.loads(res_data)
            return data["id"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"Error getting user_id: {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Error getting user_id: {str(e)}")


def copy_playlist_into_library(access_token, user_id, rec_playlist, travel_duration, search="walking"):
    # save the recommended playlist to the user's account using Create Playlist API --> this creates an empty playlist
    if not rec_playlist:
        print("No recommended playlist found.")

    body = {
        "name": "Your New Perfect Length Playlist",
        "description": "A playlist corresponding to the length of your travel time.",
        "public": False
    }
    body_encoded = json.dumps(body).encode("utf-8")
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_encoded)

    if response.status_code == 201:
        playlist = response.json()
        # print(f"Playlist created: {playlist['name']} (ID: {playlist['id']})")
        new_playlist_id = str(playlist["id"])
        new_playlist = [{
                    "name": playlist["name"],
                    "url": playlist["external_urls"].get("spotify", ""),
                    "tracks": playlist["tracks"],
                    "id": playlist["id"]
                }]
        print(new_playlist)
    else:
        print(f"Failed to create playlist. Status code: {response.status_code}")
        print("Response:", response.json())
        return None


    # print("playlsit is is this: ", new_playlist_id)
    # get each track id from recommended playlist to add to new playlist:
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
                        "id": track_info["id"] # with track id we will copy into new playlist
                    })
                else:
                    print(f"Error or missing track info when getting tracks from rec_playlist: {item}")
    except urllib.error.HTTPError as e:
        print("Failed to get access token when getting tracks from rec_playlist: {}".format(e))
    # get list of first 25 track ID's from rec playlist
    track_uris = []
    count = 0
    for track in tracks:
        if count < 25:
            track_uris.append("spotify:track:" + track["id"])
        else:
            break
    # copy all tracks into new playlist using Add Items to Playlist API:
    body = {
        "uris": track_uris
    }
    body_encoded = json.dumps(body).encode("utf-8")
    url_add_tracks = "https://api.spotify.com/v1/playlists/" + new_playlist_id + "/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    req3 = urllib.request.Request(url_add_tracks, headers=headers, data=body_encoded, method="POST")
    try:
        with urllib.request.urlopen(req3) as res:
            res_data = res.read()
            snap = json.loads(res_data)
            snapshot_id = snap["snapshot_id"]  # get the playlist snapshot to reflect new changes
    except Exception as e:
        print("Error during copy all tracks into new playlist: {}".format(e))

    # ADD AND REMOVE SONGS FROM NEW PLAYLIST IN LIBRARY (UNTIL WITHIN 3 MIN (was 15 sec) OF TRAVEL TIME):
    length = get_length_tracks(access_token, playlist=new_playlist)
    max_attempts = 0
    while length < (travel_duration - 2) or length > (travel_duration + 2) and max_attempts < 50:
        print("we've entered the loop!! attempt: " + str(max_attempts) + ". length: " + str(length))
        if length < (travel_duration - 2): # if playlist is too short
            count = 0 # keep track of the number of songs that you add so that you can add a different one each time
            # call search_song_to_extend
            add_track_uri = search_song_to_extend_playlist(access_token, count, search) #TODO: test this with a short playlist
            # use Add Item to Playlist to add the URI to the playlist
            body = {
                "uris": [add_track_uri] # no position, so it will add to the end of the playlist
            }
            body_encoded = json.dumps(body).encode("utf-8")
            url_add_track = "https://api.spotify.com/v1/playlists/" + new_playlist_id + "/tracks"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            req4 = urllib.request.Request(url_add_track, headers=headers, data=body_encoded, method="POST")
            # open the request so the changes are made
            try:
                with urllib.request.urlopen(req4) as res:
                    res_data = res.read()
                    snap = json.loads(res_data)
                    snapshot_id = snap["snapshot_id"] # update the playlist snapshot to reflect new changes
                    length = get_length_tracks(access_token, playlist=new_playlist)
            except Exception as e:
                print("Error during add track: {}".format(e))
                break
            # check if the length has changed:
            max_attempts += 1

            # use the Remove Item from Playlist API
        elif length > (travel_duration + 10): # if length is super long
            # get the last song from the list of URIs
            remove_uri1 = track_uris.pop() # This also removes it from the list
            remove_uri2 = track_uris.pop()
            remove_uri3 = track_uris.pop()
            remove_uri4 = track_uris.pop()
            remove_uri5 = track_uris.pop()
            body = {
                "tracks": [
                    {
                        "uri": remove_uri1,
                    },
                    {
                        "uri": remove_uri2,
                    },
                    {
                        "uri": remove_uri3,
                    },
                    {
                        "uri": remove_uri4,
                    },
                    {
                        "uri": remove_uri5,
                    }
                ],
                "snapshot_id": snapshot_id # get this from above
            }
            body_encoded = json.dumps(body).encode("utf-8")
            url_remove_track = "https://api.spotify.com/v1/playlists/" + new_playlist_id + "/tracks"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            req5 = urllib.request.Request(url_remove_track, headers=headers, data=body_encoded, method="DELETE")
            try:
                with urllib.request.urlopen(req5) as res:
                    res_data = res.read()
                    snap = json.loads(res_data)
                    snapshot_id = snap["snapshot_id"]  # update the playlist snapshot to reflect new changes
                    # Now update the length only after successful removal
                    length = get_length_tracks(access_token, playlist=new_playlist)
            except Exception as e:
                print("Error during remove track: {}".format(e))
                break
            max_attempts += 1
        # when close to desired length, go down my one song length at a time:
        elif length > (travel_duration + 2) and length < (travel_duration + 10):
            remove_uri1 = track_uris.pop()
            body = {
                "tracks": [
                    {
                        "uri": remove_uri1,
                    },
                ],
                "snapshot_id": snapshot_id
            }
            body_encoded = json.dumps(body).encode("utf-8")
            url_remove_track = "https://api.spotify.com/v1/playlists/" + new_playlist_id + "/tracks"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            req5 = urllib.request.Request(url_remove_track, headers=headers, data=body_encoded, method="DELETE")
            try:
                with urllib.request.urlopen(req5) as res:
                    res_data = res.read()
                    snap = json.loads(res_data)
                    snapshot_id = snap["snapshot_id"]  # update the playlist snapshot to reflect new changes
                    # Now update the length only after successful removal
                    length = get_length_tracks(access_token, playlist=new_playlist)
            except Exception as e:
                print("Error during remove track: {}".format(e))
                break
            max_attempts += 1
        else:
            max_attempts += 1

    # get playlist images, name, owner, uri, description(can be null) in a json dict
    url_get_title = f"https://api.spotify.com/v1/playlists/{new_playlist_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    req3 = urllib.request.Request(url_get_title, headers=headers)
    try:
        with urllib.request.urlopen(req3) as res:
            result = res.read()
            data = json.loads(result)
            playlist_info = [{
                "title": data["name"],
                "owner": data["owner"].get("display_name", "Unknown"),
                "description": data["description"],
                "url": data["external_urls"].get("spotify", ""),
                "images": data["images"],
                "id": data["id"]
            }]
    except Exception as e:
        print("Error during get title and info from playlist: {}".format(e))

    return playlist_info



# Search for and return one track URI corresponding to the search term. Takes in a number corresponding to which track
# to return. For example, if the first track has already been returned, enter 2 so that a different track is returned.
def search_song_to_extend_playlist(access_token, number, search="walking"):
    query = urllib.parse.urlencode({
        "q": search,
        "type": "track",
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
            # get the URI of the song to add
            returned_tracks = []
            for item in data.get("tracks", {}).get("items", []):
                if item and "uri" in item:
                    returned_tracks.append(item["uri"]) # now we have a list of 10 tracks returned from the search

            track_uri = str(returned_tracks[number])

            return track_uri

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTPError during search song to extend playlist {e.code}: {error_body}")
        return jsonify({"error": f"HTTPError {e.code}", "details": error_body}), e.code
    except Exception as e:
        print(f"Error during search song to extend playlist: {str(e)}")
        return jsonify({"error": str(e)}), 500



def main():
    # testing code for OpenRouteService API
    get_lat_lon(projectsecrets.openroute_service_key, "University of Washington, Seattle", "340 NW 47th St, Seattle, WA, 98107")
    print(get_travel_duration(projectsecrets.openroute_service_key, "driving-car", "575 Bellevue Square, Bellevue", "340 NW 47th St, Seattle, WA, 98107"))


if __name__ == "__main__":
    try:
        main()
    except (NameError, SyntaxError):
        pass
