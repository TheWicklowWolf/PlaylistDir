![Build Status](https://github.com/TheWicklowWolf/PlaylistDir/actions/workflows/main.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/thewicklowwolf/playlistdir.svg)

<img src="https://raw.githubusercontent.com/TheWicklowWolf/PlaylistDir/main/src/static/playlistdir.png" alt="logo">


Make playlists from a directory of audio files.


## Run using docker-compose

```yaml
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
      - sync_schedule=3
    ports:
      - 5000:5000
    volumes:
      - /path/to/parent:/playlistdir/parent:ro
      - /path/to/playlists:/playlistdir/playlists
      - /etc/localtime:/etc/localtime:ro
    restart: unless-stopped
```

## Configuration via environment variables

Certain values can be set via environment variables:

* __PUID__: The user ID to run the app with. Defaults to `1000`. 
* __PGID__: The group ID to run the app with. Defaults to `1000`.
* __media_server_addresses__: Addresses for media servers, remove where not needed. Format: `Plex:http://192.168.1.2:32400, Jellyfin:http://192.168.1.2:8096`.
* __media_server_tokens__: The API keys for media servers, remove where not needed. Format: `Plex: abc, Jellyfin: xyz`.
* __plex_library_section_id__: Library section ID for Plex. Defaults to `0`.
* __path_to_parent__:  Raw path to the parent directory. Defaults to ` `.
* __path_to_playlists__: Raw path to the playlists directory. Defaults to ` `.
* __sync_schedule__: Schedule hours to run. Defaults to ` `
* __playlist_sorting_method__: Sorting method, options are `modified` (sort by the modified timestamp of the files, with latest files at the top) or `alphabetically`. Defaults to `alphabetically`.


## Sync Schedule

Use a comma-separated list of hours to start sync (e.g. `2, 20` will initiate a sync at 2 AM and 8 PM).
> Note: There is a deadband of up to 10 minutes from the scheduled start time.


# Example Folder Structure


```
/data/media/music/singles
├── playlists
│   ├── playlist1.m3u
│   ├── playlist2.m3u
│   └── ...
├── playlist1
│   ├── song_a.mp3
│   └── song_b.mp3
├── playlist2
│   ├── song_x.mp3
│   └── song_y.mp3
└── ...

```

### Explanation

- **/data/media/music/singles**: This is the parent directory containing your sub-folders. It is mapped to `/playlistdir/parent` in the container and should contain all your sub-folders.  
Set environmental variable: **path_to_parent=/data/media/music/singles**



- **/data/media/music/singles/playlists**: This directory contains your playlist files. It is mapped to `/playlistdir/playlists` in the container and will contain all your `.m3u` playlist files.  
Set environmental variable: **path_to_playlists=/data/media/music/singles/playlists**

---

<img src="https://raw.githubusercontent.com/TheWicklowWolf/PlaylistDir/main/src/static/light.png" alt="light">

---

<img src="https://raw.githubusercontent.com/TheWicklowWolf/PlaylistDir/main/src/static/dark.png" alt="dark">

---

https://hub.docker.com/r/thewicklowwolf/playlistdir
