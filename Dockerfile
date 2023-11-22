FROM python:3.11-alpine

ARG UID=1001
ARG GID=1001
RUN addgroup -g $GID general_user && \
    adduser -D -u $UID -G general_user -s /bin/sh general_user

COPY . /folder2playlist
WORKDIR /folder2playlist
RUN mkdir -p /folder2playlist/playlists
RUN chown -R $UID:$GID /folder2playlist/playlists
RUN chmod -R 777 /folder2playlist/playlists

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
USER general_user
CMD ["gunicorn","src.PlaylistDir:app", "-c", "gunicorn_config.py"]