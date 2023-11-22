FROM python:3.12-alpine

ARG UID=1000
ARG GID=1000
RUN addgroup -g $GID general_user && \
    adduser -D -u $UID -G general_user -s /bin/sh general_user

COPY . /playlistdir
WORKDIR /playlistdir
RUN mkdir -p /playlistdir/playlists
RUN chown -R $UID:$GID /playlistdir/playlists
RUN chmod -R 777 /playlistdir/playlists

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
USER general_user
CMD ["gunicorn","src.PlaylistDir:app", "-c", "gunicorn_config.py"]