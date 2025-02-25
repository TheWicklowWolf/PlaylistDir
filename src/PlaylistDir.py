import os
import time
import datetime
import threading
import logging
import requests
from flask import Flask, render_template, request


class Data_Handler:
    def __init__(self):
        self.media_server_addresses = os.environ.get("media_server_addresses", "Plex: http://192.168.1.2:32400, Jellyfin: http://192.168.1.2:8096")
        self.media_server_tokens = os.environ.get("media_server_tokens", "Plex: abc, Jellyfin: xyz")
        self.plex_library_section_id = os.environ.get("plex_library_section_id", "0")
        self.path_to_parent = os.environ.get("path_to_parent", "")
        self.path_to_playlists = os.environ.get("path_to_playlists", "")
        sync_hours_str = os.environ.get("sync_schedule", "")
        self.playlist_sorting_method = os.environ.get("playlist_sorting_method", "alphabetically")
        self.include_subdir = os.environ.get("include_subdir", "no")

        self.playlist_folder = "playlists"
        self.parent_folder = "parent"
        self.playlists = []
        self.sync_start_times = []

        try:
            if sync_hours_str:
                sync_hours = [int(x) for x in sync_hours_str.split(",")]
                self.sync_start_times = sorted(list(set(sync_hours)))

        except Exception as e:
            logger.error(f"Error Updating schedule: {str(e)}")
            logger.error(f"Setting it to 12am")
            self.sync_start_times = [0]

        task_thread = threading.Thread(target=self.schedule_checker)
        task_thread.daemon = True
        task_thread.start()

    def schedule_checker(self):
        logger.info("Starting periodic checks every 10 minutes to monitor sync start times.")
        logger.info(f"Current scheduled hours to start sync (in 24-hour format): {self.sync_start_times}")

        while True:
            current_time = datetime.datetime.now().time()
            within_sync_window = any(datetime.time(t, 0, 0) <= current_time <= datetime.time(t, 59, 59) for t in self.sync_start_times)

            if within_sync_window:
                logger.info("Time to Generate Playlists")
                raw_data = self.create_playlists()
                logger.info("Big sleep for 1 Hour - " + raw_data["Status"])
                time.sleep(3600)
                logger.warning("Checking every 10 minutes as not in sync time window " + str(self.sync_start_times))

            else:
                time.sleep(600)

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
                logger.error(f"Jellyfin Error: {response.status_code}, {response.text}")
                return "Failed to Refresh Jellyfin"

        except Exception as e:
            logger.error(f"Jellyfin Library scan failed: {str(e)}")
            return "Error Refreshing Jellyfin"

    def add_playlist_to_plex(self, subfolder):
        try:
            m3u_path = os.path.join(self.path_to_playlists, subfolder + ".m3u")
            url = f"{self.plex_server_ip}/playlists/upload?sectionID={self.plex_library_section_id}&path={m3u_path}&X-Plex-Token={self.x_plex_token}"
            response = requests.post(url)
            if response.status_code == 200:
                logger.info(f"M3U playlist '{self.playlist_file}' imported successfully.")
                return "Success"
            else:
                logger.error(f"Error importing M3U playlist '{self.playlist_file}'. Status Code: {str(response.status_code)}")
                logger.warning(f"Path for M3U playlist: {m3u_path}")
                return "Failed to add to Plex"

        except Exception as e:
            logger.error(f"Error importing M3U playlist '{self.playlist_file}'")
            logger.warning(f"Path for M3U playlist: {m3u_path}")
            logger.error(f"Plex Playlist Addition Failed: {str(e)}")
            return "Error adding to Plex"

    def create_playlists(self):
        try:
            self.playlists = []
            overall_status = "Starting"
            self.media_servers = self.convert_string_to_dictionary(self.media_server_addresses)
            self.media_tokens = self.convert_string_to_dictionary(self.media_server_tokens)
            logger.info("Media Servers: " + str(self.media_servers))
            plex_update_req = False
            jellyfin_update_req = False

            if "Plex" in self.media_servers and "Plex" in self.media_tokens:
                self.plex_server_ip = self.media_servers.get("Plex")
                self.x_plex_token = self.media_tokens.get("Plex")
                plex_update_req = True
                logger.info(f"Plex address-> {self.plex_server_ip} and Plex Token Found")
            else:
                logger.warning("No Plex Info")

            if "Jellyfin" in self.media_servers and "Jellyfin" in self.media_tokens:
                self.jellyfin_token = self.media_tokens.get("Jellyfin")
                self.jellyfin_address = self.media_servers.get("Jellyfin")
                jellyfin_update_req = True
                logger.info(f"Jellyfin address-> {self.jellyfin_address} and Jellyfin Token Found")
            else:
                logger.warning("No Jellyfin Info")

            playlist_generated_flag = False

            if not os.path.exists(self.parent_folder):
                overall_status = "Folder Doesn't Exist"
                logger.info(f"Folder Doesn't Exist - Check Mounted Volumes")
                return

            if self.include_subdir == "yes":
                subfolders = [
                    os.path.relpath(os.path.join(root, d), self.parent_folder)
                    for root, dirs, _ in os.walk(self.parent_folder)
                    for d in dirs
                ]
            else:
                subfolders = [f for f in os.listdir(self.parent_folder) if os.path.isdir(os.path.join(self.parent_folder, f))]

            if not subfolders:
                overall_status = "Parent Folder Empty"
                logger.info(f"Parent Folder Empty")
                return

            sorted_subfolders = sorted(subfolders, key=lambda x: x.casefold())
            logger.info(f"Folder Count: {len(sorted_subfolders)}")

            for subfolder in sorted_subfolders:
                try:
                    folder_with_music_files = os.path.join(self.parent_folder, subfolder)
                    music_files = [f for f in os.listdir(folder_with_music_files) if f.endswith((".mp3", ".flac", ".m4a", ".aac", ".wav", ".opus"))]
                    logger.info(f"Music File Count: {len(music_files)} in Sub-Folder: {subfolder}")

                    if self.playlist_sorting_method == "modified":
                        music_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_with_music_files, x)), reverse=True)
                    elif self.playlist_sorting_method == "modified-ascending":
                        music_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_with_music_files, x)))
                    else:
                        music_files.sort(key=lambda x: x.casefold())

                    if not music_files:
                        continue
                    
                    if self.include_subdir == "yes":
                        self.playlist_file = os.path.join(self.playlist_folder, f"{subfolder.split('/')[-1]}.m3u")
                    else:
                        self.playlist_file = os.path.join(self.playlist_folder, f"{subfolder}.m3u")
                    
                    playlist_info = {"Name": subfolder, "Count": len(music_files), "Status": "Created m3u"}

                    with open(self.playlist_file, "w") as file:
                        playlist_generated_flag = True
                        for music_item in music_files:
                            m3u = os.path.join(self.path_to_parent, subfolder, music_item)
                            file.write(m3u + "\n")

                except Exception as e:
                    logger.error(f"Playlist Creation Failed: {str(e)}")
                    overall_status = f"Playlist Creation Failed: {type(e).__name__}"

                else:
                    overall_status = "Playlists Generated"
                    if plex_update_req:
                        if self.include_subdir == "yes":
                            ret = self.add_playlist_to_plex(subfolder.split('/')[-1])
                        else:
                            ret = self.add_playlist_to_plex(subfolder)

                        if ret == "Success":
                            playlist_info["Status"] += ", Added to Plex"
                        else:
                            playlist_info["Status"] += ", " + ret

                    self.playlists.append(playlist_info)

            if subfolders and playlist_generated_flag and jellyfin_update_req:
                ret = self.refresh_jellyfin()
                if ret == "Success":
                    for x in self.playlists:
                        x["Status"] += ", Added to Jellyfin"
                else:
                    for x in self.playlists:
                        x["Status"] += ", Failed to refresh Jellyfin"

        except Exception as e:
            logger.error(f"Playlist Creation Failed: {str(e)}")
            overall_status = f"Playlist Creation Failed: {type(e).__name__}"

        finally:
            logger.info(f"Status - {overall_status}")
            return {"Data": self.playlists, "Status": overall_status}

    def save_settings(self, data):
        if data["sync_start_times"]:
            self.sync_start_times = [int(start_time.strip()) for start_time in data["sync_start_times"].split(",")]
        self.media_server_addresses = data["media_server_addresses"]
        self.media_server_tokens = data["media_server_tokens"]
        self.plex_library_section_id = data["plex_library_section_id"]
        self.path_to_parent = data["path_to_parent"]
        self.path_to_playlists = data["path_to_playlists"]


app = Flask(__name__)
app.secret_key = "any_secret_key"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger()

app_name_text = os.path.basename(__file__).replace(".py", "")
release_version = os.environ.get("RELEASE_VERSION", "unknown")
logger.warning(f"{'*' * 50}\n")
logger.warning(f"{app_name_text} Version: {release_version}\n")
logger.warning(f"{'*' * 50}")


data_handler = Data_Handler()


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("base.html")


@app.route("/get_playlists", methods=["GET"])
def get_playlists():
    return {"Data": data_handler.playlists, "Status": ""}


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
        "sync_start_times": data_handler.sync_start_times,
        "media_server_addresses": data_handler.media_server_addresses,
        "media_server_tokens": data_handler.media_server_tokens,
        "plex_library_section_id": data_handler.plex_library_section_id,
        "path_to_parent": data_handler.path_to_parent,
        "path_to_playlists": data_handler.path_to_playlists,
    }
    return data


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000)
