var config_modal = document.getElementById('config-modal');
var save_message = document.getElementById("save-message");
var save_changes_button = document.getElementById("save-changes-button");
var media_server_addresses = document.getElementById("media_server_addresses");
var media_server_tokens = document.getElementById("media_server_tokens");
var plex_library_section_id = document.getElementById("plex_library_section_id");
var path_to_parent = document.getElementById("path_to_parent");
var path_to_playlists = document.getElementById("path_to_playlists");
var generate_playlist = document.getElementById("generate_playlist");
var generate_playlist_spinner = document.getElementById("generate_playlist_spinner");
var generate_playlist_status = document.getElementById('status_text');


generate_playlist.addEventListener('click', function () {
    generate_playlist.disabled = true;
    generate_playlist_spinner.classList.add('spinner-border');
    fetch('/create_playlists', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    })
        .then(response => response.json())
        .then(data => {
            var playlists = data.Data;
            var tableBody = document.getElementById("playlistsTable").getElementsByTagName('tbody')[0];

            tableBody.innerHTML = '';

            playlists.forEach(function (playlist) {
                var row = document.createElement('tr');
                ['Name', 'Count', 'Status'].forEach(function (property) {
                    var cell = document.createElement('td');
                    cell.appendChild(document.createTextNode(playlist[property]));
                    row.appendChild(cell);
                });
                tableBody.appendChild(row);
            });
            generate_playlist.disabled = false;
            generate_playlist_spinner.classList.remove('spinner-border');
            generate_playlist_status.innerText = 'Status: ' + data.Status;
        })
        .catch(error => {
            console.error('Error:', error);
            generate_playlist.disabled = false;
            generate_playlist_status.innerText = 'Status: ' + error;
        });
});

config_modal.addEventListener('show.bs.modal', function (event) {
    fetch('/load_settings', {
        headers: {
            'Content-Type': 'application/json'
        },
        method: 'GET'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            media_server_addresses.value = data.media_server_addresses;
            media_server_tokens.value = data.media_server_tokens;
            plex_library_section_id.value = data.plex_library_section_id;
            path_to_parent.value = data.path_to_parent;
            path_to_playlists.value = data.path_to_playlists;
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
});

save_changes_button.addEventListener("click", () => {
    fetch('/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "media_server_addresses": media_server_addresses.value,
            "media_server_tokens": media_server_tokens.value,
            "plex_library_section_id": plex_library_section_id.value,
            "path_to_parent": path_to_parent.value,
            "path_to_playlists": path_to_playlists.value,
        }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            save_message.style.display = "block";
            setTimeout(function () {
                save_message.style.display = "none";
            }, 1500);
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
});

const themeSwitch = document.getElementById('themeSwitch');
const savedTheme = localStorage.getItem('theme');
const savedSwitchPosition = localStorage.getItem('switchPosition');

if (savedSwitchPosition) {
    themeSwitch.checked = savedSwitchPosition === 'true';
}

if (savedTheme) {
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
}

themeSwitch.addEventListener('click', () => {
    if (document.documentElement.getAttribute('data-bs-theme') === 'dark') {
        document.documentElement.setAttribute('data-bs-theme', 'light');
    } else {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    }
    localStorage.setItem('theme', document.documentElement.getAttribute('data-bs-theme'));
    localStorage.setItem('switchPosition', themeSwitch.checked);
});
