![Build Status](https://github.com/TheWicklowWolf/PlaylistDir/actions/workflows/main.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/thewicklowwolf/playlistdir.svg)


![logo](src/static/playlistdir.png)


Web GUI for making playlist out of files in a directory.


## Run using docker-compose

```yaml
version: "2.1"
services:
  playlistdir:
    image: thewicklowwolf/playlistdir:latest
    container_name: playlistdir
    environment:
      - media_server_addresses=Plex:http://192.168.1.2:32400, Jellyfin:http://192.168.1.2:8096
      - media_server_tokens=Plex:x-token, Jellyfin:api-token
      - plex_library_section_id=0
      - path_to_parent=/path/to/parent
      - path_to_playlists=/path/to/playlists
    ports:
      - 5000:5000
    volumes:
      - /path/to/parent:/playlistdir/parent:ro
      - /path/to/playlists:/playlistdir/playlists
    restart: unless-stopped
```

---

![image](https://github.com/TheWicklowWolf/PlaylistDir/assets/111055425/1fff3b0c-6eb1-4176-a383-c72797ea83c7)

---

![image](https://github.com/TheWicklowWolf/PlaylistDir/assets/111055425/cfc20676-0785-4617-ade5-d54c92fa226d)

---

https://hub.docker.com/r/thewicklowwolf/playlistdir
