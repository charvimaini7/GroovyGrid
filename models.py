from flask_login import UserMixin
from app import db
#models

class User(db.Model,UserMixin):
    __tablename__ = 'user'
    user_ID = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(), unique = True, nullable = False)
    creator_ID = db.Column(db.Boolean, nullable = False, default = False)
    password = db.Column(db.String, nullable = False)
    is_admin = db.Column(db.Boolean, nullable = False, default = False)
    is_flagged = db.Column(db.Boolean, nullable = True, default = False)   

class Album(db.Model):
    __tablename__ = 'album'
    album_ID = db.Column(db.Integer, primary_key = True)
    album_name = db.Column(db.String, nullable = False)
    genre = db.Column(db.String(), nullable = True)
    artist = db.Column(db.String(), nullable = True)
    is_flagged = db.Column(db.Boolean,nullable = False, default = False)

class Song(db.Model):
    __tablename__ = 'song'
    song_ID = db.Column(db.Integer, primary_key = True)
    song_name = db.Column(db.String(), nullable = False)
    lyrics = db.Column(db.String(), nullable = False)
    duration = db.Column(db.Integer, nullable = False)
    is_flagged = db.Column(db.Boolean,nullable = False, default = False)
    date_created = db.Column(db.Date, nullable=True)
    user_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'))

class AlbumSongs(db.Model):
    __tablename__ = 'albumsongs'
    ID = db.Column(db.Integer, primary_key = True)
    album_ID = db.Column(db.Integer, db.ForeignKey('album.album_ID'))
    song_ID = db.Column(db.Integer, db.ForeignKey('song.song_ID'))


class Playlist(db.Model):
    __tablename__ = 'playlist'
    playlist_ID = db.Column(db.Integer, primary_key = True)
    playlist_name = db.Column(db.String, primary_key = False)
    user_ID = db.Column(db.Integer, db.ForeignKey('user.user_ID'))


class PlaylistSongs(db.Model):
    __tablename__ = 'playlistsongs'
    ID =  db.Column(db.Integer, primary_key = True)
    playlist_ID = db.Column(db.Integer, db.ForeignKey('playlist.playlist_ID'))
    song_ID = db.Column(db.Integer, db.ForeignKey('song.song_ID'))

class SongRating(db.Model):
    __tablename__ = 'songrating'
    rating_ID = db.Column(db.Integer, primary_key = True)
    song_ID = db.Column(db.Integer, db.ForeignKey('song.song_ID'))
    song_rating = db.Column(db.Float, nullable = True)
    song_count = db.Column(db.Integer, nullable = True)  

db.create_all()