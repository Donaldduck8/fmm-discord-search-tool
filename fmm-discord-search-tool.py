import os
import re
import sys
import time
import json
import requests
import datetime
import traceback

import html
import urllib

from pytimeparse.timeparse import timeparse
from tabulate import tabulate
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))

RESULTS_DIR = os.path.join(HERE, "results")
if not os.path.isdir(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

RESULTS = []

sc_session = requests.Session()
sc_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    'Referer': 'https://soundcloud.com/',
}

sc_session.headers.update(sc_headers)

sc_client_id = "aG2FjTwcYv7xe1bZELqpOtGOTMSDQ1Bj" # Yes, I made sure this is anonymous, thank you :)
sc_app_version = "1644847185"

#################################################################### ACTUAL CODE


def retry_net(func, retry_amount=3, sleep_amount=2, valid_status_codes=[200], **kwargs):
    for x in range(retry_amount):
        try:
            r = func(**kwargs)

            if len(valid_status_codes) > 0:
                if r.status_code not in valid_status_codes:
                    print(r.status_code)
                    print(r.text)
                    raise Exception('Request in retry_net failed!')

            return r
        except requests.exceptions.ConnectionError as e:
            print("Bandcamp has reset the connection. You may have to restart this program if this keeps happening.")
            time.sleep(sleep_amount)
            sleep_amount *= 2
        except Exception as e:
            print(kwargs)
            print(traceback.print_exc())
            time.sleep(sleep_amount)
            sleep_amount *= 2

    raise Exception


def dedup_results(results):
    results_dedup = []
    urls = []

    for x in results:
        if x["permalink_url"] not in urls:
            results_dedup.append(x)
            urls.append(x["permalink_url"])

    return results_dedup


def search_soundcloud(query_string, duration=None, genre=None):
    offset = 0
    keep_going = True

    results = []

    while keep_going:
        fields = {
            "filter.duration": duration,
            "filter.genre_or_tag": genre,
            "q": query_string,
            "client_id": sc_client_id,
            "app_version": sc_app_version,
            "offset": offset,
            "limit": 20
        }

        fields = {k:v for k,v in fields.items() if v is not None}

        url_param_string = urllib.parse.urlencode(fields)
        url = f'https://api-v2.soundcloud.com/search/tracks?{url_param_string}'

        data = retry_net(sc_session.get, url=url).json()

        results += data["collection"]

        if len(data["collection"]) == 0:
            keep_going = False

        offset += len(data["collection"])

        if offset >= 8000:
            keep_going = False

        time.sleep(0.1)

    return results


def get_song_bandcamp(id):
    url = f'https://bandcamp.com/EmbeddedPlayer/v=2/track={id}/size=large/tracklist=false/artwork=small/'

    page = retry_net(sc_session.get, url=url).text
    soup = BeautifulSoup(page, "html.parser")

    # Get player data:
    data_player_data = soup.find("script", src=re.compile(".*player.*"))["data-player-data"]
    data_player_data = html.unescape(data_player_data)
    data = json.loads(data_player_data)
    data = data["tracks"][0]

    # Get artist
    artist = data["artist"]

    # Get title
    title = data["title"]

    # Get duration
    try:
        duration = int(data["duration"] * 1000)
    except Exception as e:
        print("Track has no duration:", artist, title, data["title_link"])
        duration = 0

    song = {
        "user": {
            "username": artist
        },
        "title": title,
        "duration": duration,
        "permalink_url": data["title_link"]
    }

    return song


def search_bandcamp(query_string):
    page_number = 1
    keep_going = True

    results = []

    while keep_going:
        print("Page", page_number)

        fields = {
            "from": "results",
            "item_type": "t",
            "page": page_number,
            "q": query_string
        }

        fields = {k:v for k,v in fields.items() if v is not None and v != ""}

        url_param_string = urllib.parse.urlencode(fields)
        url = f'https://bandcamp.com/search?{url_param_string}'

        page = retry_net(sc_session.get, url=url).text
        soup = BeautifulSoup(page, "html.parser")

        result_items_div = soup.find("ul", {"class": "result-items"})

        if result_items_div == None:
            break

        result_items = result_items_div.find_all("li", {"class": "searchresult data-search"})

        for track_div in result_items:
            track_id = json.loads(track_div["data-search"])["id"]

            try:
                song = get_song_bandcamp(track_id)

                results.append(song)
            except Exception as e:
                traceback.print_exc()


            time.sleep(0.5)

        if len(result_items) == 0:
            keep_going = False

        page_number += 1

        time.sleep(0.5)

    return results


def save_results():
    if len(RESULTS) == 0:
        print("The results object is currently empty.")
        return

    results_name = input("Please input the file name: ") + ".json"

    results_p = os.path.join(RESULTS_DIR, results_name)

    with open(results_p, "w+", encoding="utf-8") as results_f:
        results_f.write(json.dumps(RESULTS))


def load_results():
    results_files = [x for x in os.listdir(RESULTS_DIR) if x.endswith(".json")]

    for i, results_name in enumerate(results_files):
        print(i, " | ", results_name)

    file_index = int(input("Please select the result you would like to load (-1 to exit): "))

    if file_index == -1:
        return

    results_name = results_files[file_index]
    results_p = os.path.join(RESULTS_DIR, results_name)

    with open(results_p, "r", encoding="utf-8") as results_f:
        global RESULTS

        RESULTS = json.loads(results_f.read())


def save_search_results_formatted(search_results):
    rows = [[song["user"]["username"], song["title"][:101], str(datetime.timedelta(milliseconds=int((song["duration"] - (song["duration"] % 1000))))), song["permalink_url"]] for song in search_results]
    rows_tabulated = tabulate(rows)

    with open(os.path.join(RESULTS_DIR, "search_results.txt"), "w+", encoding="utf-8") as search_results_f:
        search_results_f.write(rows_tabulated)


def search_by_duration_exact(duration):
    # It is assumed duration is in seconds
    search_results = []

    duration = int(duration)

    for song in RESULTS:
        song_duration_seconds = int((song["duration"] - (song["duration"] % 1000)) / 1000)

        if song_duration_seconds == duration:
            search_results.append(song)

    print(f"Found {len(search_results)} songs, written to /results/search_results.txt")

    return search_results


def search_by_duration_range(duration_minimum, duration_maximum):
    # It is assumed duration is in seconds
    search_results = []

    for song in RESULTS:
        try:
            song_duration_seconds = int((song["duration"] - (song["duration"] % 1000)) / 1000)
        except Exception as e:
            traceback.print_exc()
            print(song)

        if song_duration_seconds >= duration_minimum and song_duration_seconds <= duration_maximum:
            search_results.append(song)

    print(f"Found {len(search_results)} songs, written to /results/search_results.txt")

    return search_results


def search_by_duration():
    if len(RESULTS) == 0:
        print("The results object is currently empty.")
        return


    duration = input("Please input the duration you're looking for (\"X:XX\" or \"X:XX X:XX\"): ")

    search_results = []

    if " " in duration:
        durations = duration.split(" ")[:2]

        search_results = search_by_duration_range(timeparse(durations[0]), timeparse(durations[1]))
    else:
        search_results = search_by_duration_exact(timeparse(duration))

    search_results = dedup_results(search_results)

    save_search_results_formatted(search_results)


def multiple_choice(options, message):
    keys = list(options.keys())

    for i, k in enumerate(keys):
        print(f'{i}  |  {k}')

    choice_index = int(input(message))

    return options[keys[choice_index]]


def main():
    global RESULTS

    print("This is a small tool to search by duration on Soundcloud and Bandcamp, written by Donald.")

    while True:
        print("==========================================================")
        print(f"There are currently {len(RESULTS)} songs in memory")
        print("==========================================================")

        options = [
            "Search Soundcloud",
            "Search Bandcamp",
            "Save search results",
            "Load search results",
            "Search songs in memory by duration",
        ]

        for i, option in enumerate(options):
            print(i, " | ", option)

        try:
            option_index = int(input("Please input what you would like to do: "))

            print("==========================================================")

            if option_index == 0:
                search_query = input("Please input your search query: ")

                durations = {
                    "Any": None,
                    "Short (<2 minutes)": "short",
                    "Medium (2-10 minutes)": "medium"
                }

                duration = multiple_choice(durations, "Please choose the duration: ")
                genre = input("Please input the genre (leave empty if none): ")

                print("Searching...")

                RESULTS = search_soundcloud(search_query)
            elif option_index == 1:
                search_query = input("Please input your search query: ")

                print("Searching...")

                RESULTS = search_bandcamp(search_query)
            elif option_index == 2:
                save_results()
            elif option_index == 3:
                load_results()
            elif option_index == 4:
                search_by_duration()
        except Exception as e:
            traceback.print_exc()
            pass

if __name__ == "__main__":
    main()
