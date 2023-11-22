import os
import logging
import requests
from flask import Flask, render_template, request


class Data_Handler:
    def __init__(self, media_server_addresses, media_server_tokens, plex_library_section_id, path_to_parent, path_to_playlists):
        self.media_server_addresses = media_server_addresses
        self.media_server_tokens = media_server_tokens
        self.plex_library_section_id = plex_library_section_id
        self.path_to_parent = path_to_parent
        self.path_to_playlists = path_to_playlists
        self.playlists = "playlists"
        self.parent = "parent"

    def convert_string_to_dictionary(self, raw_string):
        result = {}
        if not raw_string:
            return result

        pairs = raw_string.split(",")
        for pair in pairs:
            key_value = pair.split(":", 1)
            if len(key_value) == 2:
                key, value = key_value
                result[key.strip()] = value.strip()

        return result

    def refresh_jellyfin(self):
        try:
            logger.info("Attempting Jellyfin Sync")
            url = f"{self.jellyfin_address}/Library/Refresh?api_key={self.jellyfin_token}"
            response = requests.post(url)
            if response.status_code == 204:
                logger.info("Jellyfin Library refresh request successful.")
                return "Success"
            else:
                logger.warning(f"Jellyfin Error: {response.status_code}, {response.text}")
                return "Failed to Refresh Jellyfin"
        except Exception as e:
            logger.error(f"Jellyfin Library scan failed: {str(e)}")
            return "Error Refreshing Jellyfin"

    def add_playlist_to_plex(self, subfolder):
        try:
            m3u_path = os.path.join(self.path_to_playlists, self.playlists, subfolder + ".m3u")
            url = f"http://{self.plex_server_ip}/playlists/upload?sectionID={self.plex_library_section_id}&path={m3u_path}&X-Plex-Token={self.x_plex_token}"
            response = requests.post(url)
            if response.status_code == 200:
                logger.info(f"M3U playlist '{self.playlist_file}' imported successfully.")
                return "Success"
            else:
                logger.warning(f"Error importing M3U playlist '{self.playlist_file}'. Status Code:", response.status_code)
                return "Failed to add to Plex"
        except Exception as e:
            logger.error(f"Error importing M3U playlist '{self.playlist_file}'")
            logger.error(f"Plex Playlist Addition Failed: {str(e)}")
            return "Error adding to Plex"

    def create_playlists(self):
        try:
            playlists = []
            overall_status = "Start"
            self.media_servers = self.convert_string_to_dictionary(self.media_server_addresses)
            self.media_tokens = self.convert_string_to_dictionary(self.media_server_tokens)
            logger.info("Media Servers: " + str(self.media_servers))
            plex_update_req = False
            jellyfin_update_req = False

            if "Plex" in self.media_servers and "Plex" in self.media_tokens:
                self.plex_server_ip = self.media_servers.get("Plex")
                self.x_plex_token = self.media_tokens.get("Plex")
                plex_update_req = True
                logger.info("Plex Token Found")
            else:
                logger.warning("No Plex Info")

            if "Jellyfin" in self.media_tokens and "Jellyfin" in self.media_tokens:
                self.jellyfin_token = self.media_tokens.get("Jellyfin")
                self.jellyfin_address = self.media_servers.get("Jellyfin")
                jellyfin_update_req = True
                logger.info("Jellyfin Token Found")
            else:
                logger.warning("No Jellyfin Info")

            playlist_generated_flag = False
            subfolders = [f for f in os.listdir(self.parent) if os.path.isdir(os.path.join(self.parent, f))]

            for subfolder in subfolders:
                try:
                    mp3_folder = os.path.join(self.parent, subfolder)
                    mp3_files = [f for f in os.listdir(mp3_folder) if f.endswith(".mp3")]
                    file_creation_times = [(f, os.path.getctime(os.path.join(mp3_folder, f))) for f in mp3_files]
                    file_creation_times.sort(key=lambda x: x[1], reverse=True)
                    mp3_files = [file for file, _ in file_creation_times]

                    if mp3_files:
                        self.playlist_file = os.path.join(self.playlists, f"{subfolder}.m3u")
                        playlist_info = {"Name": subfolder, "Count": len(mp3_files), "Status": "Created m3u"}

                        with open(self.playlist_file, "w") as file:
                            playlist_generated_flag = True
                            for mp3 in mp3_files:
                                m3u = os.path.join(self.path_to_parent, subfolder, mp3)
                                file.write(m3u + "\n")
                    else:
                        continue
                except Exception as e:
                    logger.error(f"Playlist Creation Failed: {str(e)}")
                    overall_status = f"Playlist Creation Failed: {type(e).__name__}"
                else:
                    overall_status = "Playlists Generated"
                    if plex_update_req:
                        ret = self.add_playlist_to_plex(subfolder)
                        if ret == "Success":
                            playlist_info["Status"] += ", Added to Plex"
                        else:
                            playlist_info["Status"] += ", " + ret

                    playlists.append(playlist_info)

            if subfolders and playlist_generated_flag and jellyfin_update_req:
                ret = self.refresh_jellyfin()
                if ret == "Success":
                    for x in playlists:
                        x["Status"] += ", Added to Jellyfin"
                else:
                    for x in playlists:
                        x["Status"] += ", Failed to refresh Jellyfin"

        except Exception as e:
            logger.error(f"Playlist Creation Failed: {str(e)}")
            overall_status = f"Playlist Creation Failed: {type(e).__name__}"

        finally:
            return {"Data": playlists, "Status": overall_status}

    def save_settings(self, data):
        self.media_server_addresses = data["media_server_addresses"]
        self.media_server_tokens = data["media_server_tokens"]
        self.plex_library_section_id = data["plex_library_section_id"]
        self.path_to_parent = data["path_to_parent"]
        self.path_to_playlists = data["path_to_playlists"]


app = Flask(__name__)
app.secret_key = "any_secret_key"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger()

media_server_addresses = os.environ.get("media_server_addresses", "Plex: http://192.168.1.2:32400, Jellyfin: http://192.168.1.2:8096")
media_server_tokens = os.environ.get("media_server_tokens", "Plex: abc, Jellyfin: xyz")
plex_library_section_id = os.environ.get("plex_library_section_id", "0")
path_to_parent = os.environ.get("path_to_parent", "")
path_to_playlists = os.environ.get("path_to_playlists", "")

data_handler = Data_Handler(media_server_addresses, media_server_tokens, plex_library_section_id, path_to_parent, path_to_playlists)


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("base.html")


@app.route("/create_playlists", methods=["POST"])
def req_create_playlists():
    ret = data_handler.create_playlists()
    return ret


@app.route("/save_settings", methods=["POST"])
def save_settings():
    try:
        data = request.get_json()
        data_handler.save_settings(data)
    except Exception as e:
        logger.error(str(e))
        return {"Status": "Error: Check Logs"}
    else:
        return {"Status": "Success: Settings Saved"}


@app.route("/load_settings", methods=["GET"])
def load_settings():
    data = {
        "media_server_addresses": data_handler.media_server_addresses,
        "media_server_tokens": data_handler.media_server_tokens,
        "plex_library_section_id": data_handler.plex_library_section_id,
        "path_to_parent": data_handler.path_to_parent,
        "path_to_playlists": data_handler.path_to_playlists,
    }
    return data


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000)
