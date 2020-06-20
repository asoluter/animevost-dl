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
        number_str = name.split(" ")[0]
        number = int(number_str) if number_str.isnumeric() else 1
        vod_urls = []
        hd_vod = episode.get("hd")
        if hd_vod:
            vod_urls.append(hd_vod)
        std_vod = episode.get("std")
        if std_vod:
            vod_urls.append(std_vod)
        if not vod_urls:
            continue
        playlist.append((number, vod_urls))

    return sorted(playlist)


def download_video(name, vod_urls, save_location):
    if not (os.path.exists(save_location) and os.path.isdir(save_location)):
        os.mkdir(save_location)

    file_name = name+os.path.splitext(vod_urls[0])[1]
    file_path = os.path.join(save_location, file_name)

    if os.path.exists(file_path):
        print("Video exists, skipping download")
        return

    for vod_url in vod_urls:
        try:
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
        except requests.HTTPError:
            print(f"Failed loading {vod_url}, retrying with lower quality")
    sys.stdout.write("\n")


def download_playlist(id):
    title = get_title(id)
    playlist = get_playlist(id)
    save_location = os.path.join(os.getcwd(), title)

    print(f"\nPlaylist name: {title}\n")
    n_vods = len(playlist)
    for n, vod_urls in playlist:
        print(f"Downloading video {n} of {n_vods}")
        download_video(f"{n:04}", vod_urls, save_location)


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
