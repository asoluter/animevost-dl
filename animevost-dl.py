#!python3
import requests
import os
import sys
from slugify import slugify


API_URL = "https://api.animevost.org/v1/"
PROGRESS_BAR_LENGTH = 100


def __post_request(type, id):
    response = requests.post(API_URL + type, data={"id": id}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return response.json()


def get_title(id):
    response = __post_request("info", id)

    if response.get("state", {}).get("status") != "ok":
        return None

    data = response.get("data", [])
    if not data:
        return None

    title = data[0].get("title")
    index_part = title.rfind(" [")
    return slugify(title[:index_part])


def get_playlist(id):
    response = __post_request("playlist", id)

    playlist = []
    for episode in response:
        name = episode.get("name")
        if not name:
            continue
        number = int(name.split(" ")[0])
        vod_url = episode.get("hd", episode.get("std", None))
        if not vod_url:
            continue
        playlist.append((number, vod_url))

    return sorted(playlist)


def download_video(name, vod_url, save_location):
    if not (os.path.exists(save_location) and os.path.isdir(save_location)):
        os.mkdir(save_location)

    file_name = name+os.path.splitext(vod_url)[1]
    file_path = os.path.join(save_location, file_name)

    if os.path.exists(file_path):
        print("Video exists, skipping download")
        return

    with requests.get(vod_url, stream=True) as r:
        r.raise_for_status()
        total_length = r.headers.get('content-length')
        dl = 0
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=4096):
                f.write(chunk)
                if total_length:
                    dl += len(chunk)
                    done = int(PROGRESS_BAR_LENGTH * dl / int(total_length))
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (PROGRESS_BAR_LENGTH - done)))
                    sys.stdout.flush()


def download_playlist(id):
    title = get_title(id)
    playlist = get_playlist(id)
    save_location = os.path.join(os.getcwd(), title)

    print(f"Playlist name: {title}")
    n_vods = len(playlist)
    for n, vod_url in playlist:
        print(f"\nDownloading video {n} of {n_vods}")
        download_video(f"{n:04}", vod_url, save_location)


def get_id_from_url(web_url):
    full_name = web_url.split('/')[-1]
    id_str = full_name.split('-')[0]
    return int(id_str)


def main():
    for url in sys.argv[1:]:
        id = get_id_from_url(url)
        download_playlist(id)


if __name__ == "__main__":
    main()
