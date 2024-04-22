from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask_sqlalchemy import SQLAlchemy
import os
from flask import session
from flask_login import LoginManager,current_user,logout_user,login_user,login_required,UserMixin
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import outerjoin

app = Flask(__name__)
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['SECRET_KEY'] = '123456789'
app.app_context().push()

class User(db.Model,UserMixin):
    __tablename__ = 'user'
    user_ID = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(), unique = True, nullable = False)
    creator_ID = db.Column(db.Boolean, nullable = False, default = False)
    password = db.Column(db.String, nullable = False)
    is_admin = db.Column(db.Boolean, nullable = False, default = False)
    is_flagged = db.Column(db.Boolean, nullable = True, default = False)
    
    def get_id(self):
        return str(self.user_ID)


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

#usermanagemnent
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('userdashboard'))
    return render_template('home.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == '' or password == '':
            flash ('Username or password should not be empty!','danger')
            return redirect(url_for('login'))
        user = User.query.filter_by(username = username).first()
        if not user:
            flash ('User not found. Please register first!','danger')
            return redirect(url_for('register'))
        if user.password != password:
            flash ('Incorrect password','danger')
            return redirect(url_for('login'))
        if user.is_admin == True:
            login_user(user)
            return redirect(url_for('admindashboard'))
        login_user(user)
        return redirect(url_for('userdashboard'))
    return render_template('login.html')

@app.route('/register', methods=[ 'GET','POST'])
def register():
    if request.method == 'POST': 
        username = request.form.get('username')
        password = request.form.get('password') 
        if username == "" or password == "":
            flash('Username or password should not be empty!','danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash ('User already exists. Please try a different username! Or else, login','danger')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('You are now registered. Welcome to GroovyGrid!','success')
        return redirect(url_for('login'))
    return render_template ('register.html')

@app.route('/registerforcreator', methods=[ 'GET','POST'])
@login_required
def creator():
    if request.method == 'POST': 
        username = request.form.get('username')
        password = request.form.get('password')
        if username == '' or password == '':
            flash('Username or password should not be empty!','danger')
            return redirect(url_for('creator'))
        user = User.query.filter_by(username = username).first()
        if not user and session.get('user_id') != username:
            flash('Username not found. Please try a different username or register now!','danger')
            return redirect(url_for('creator'))
        if user.password != password:
            flash ('Incorrect password','danger')
            return redirect(url_for('creator'))
        #login successful
        user.creator_ID = True
        db.session.commit()
        return redirect(url_for('creatordashboard'))
    return render_template('register_creator.html')


@app.route('/userdashboard', methods = ['GET', 'POST'])
@login_required
def userdashboard():
    query = db.session.query(
        Song.song_ID,
        Song.song_name,
        Song.lyrics,
        Song.duration,
        Song.is_flagged,
        Song.date_created,
        Album.album_ID,
        Album.album_name,
        Album.genre,
        Album.artist,
        Song.user_ID,
        User.username
    ).join(
        Song, User.user_ID == Song.user_ID
    ).outerjoin(
        AlbumSongs,
        Song.song_ID == AlbumSongs.song_ID
    ).outerjoin(
        Album,
        AlbumSongs.album_ID == Album.album_ID
    ).all()
    return render_template('user/user_dashboard.html', songs = query)

@app.route('/creatordashboard', methods = ['GET', 'POST'])
@login_required
def creatordashboard():
       if current_user.creator_ID:
            query = db.session.query(
            Song.song_ID,
            Song.song_name,
            Song.lyrics,
            Song.duration,
            Song.is_flagged,
            Song.date_created,
            Album.album_ID,
            Album.album_name,
            Album.genre,
            Album.artist,
            AlbumSongs.ID
        ).outerjoin(
            AlbumSongs,
            Song.song_ID == AlbumSongs.song_ID
        ).outerjoin(
            Album,
            AlbumSongs.album_ID == Album.album_ID
        ).filter(Song.user_ID == current_user.user_ID).all()
            if current_user.is_flagged:
                flash ('ATTENTION! You have been blacklisted from GroovyGrid. Please contact the admin for more details!','danger')
                return redirect(url_for('userdashboard'))
            return render_template('/creator/creator_dashboard.html', songs = query)
       return render_template ('login.html')

@app.route('/user/createplaylist', methods = ['GET', 'POST'])
@login_required
def createplaylist():
    if request.method=='POST':
        playlist = request.form.get('playlist')
        newplaylist = Playlist(playlist_name = playlist, user_ID = current_user.user_ID)
        db.session.add(newplaylist)
        db.session.commit()
        return redirect(url_for('playlist'))
    return render_template('/user/new_playlist.html')

@app.route('/user/playlist', methods = ['GET', 'POST'])
@login_required
def playlist():
    query = db.session.query(
    Song.song_ID,
    Song.song_name,
    Song.lyrics,
    Song.duration,
    Song.is_flagged,
    Song.date_created,
    Playlist.playlist_ID,
    Playlist.playlist_name,
    PlaylistSongs.ID
).outerjoin(
    PlaylistSongs,
    PlaylistSongs.playlist_ID == Playlist.playlist_ID
).outerjoin(
    Song,
    Song.song_ID == PlaylistSongs.song_ID
).filter(Playlist.user_ID == current_user.user_ID).all()
    return render_template('user/playlist.html',songs=query)

@app.route('/user/readlyrics<int:id>', methods = ['GET', 'POST'])
@login_required
def readlyrics(id):
        newSong = Song.query.filter_by(song_ID = id).first()
        return render_template('user/read_lyrics.html', newSong = newSong)

@app.route('/user/addsong<int:id>', methods = ['GET', 'POST'])
@login_required
def addsong(id):
    if request.method == 'POST': 
        playlist_id = request.form.get('playlist') 
        if playlist_id == "":
            flash('Playlist should not be empty! Please create a playlist first!', 'danger')
            return redirect(url_for('addsong',id = id))
        myplaylist = PlaylistSongs(playlist_ID=playlist_id, song_ID=id)
        db.session.add(myplaylist)
        db.session.commit()
        flash('Song is now added to your playlist!', 'success')
        return redirect (url_for('playlist'))
    if Playlist.query.filter_by(user_ID = current_user.user_ID).all():
        playlist=Playlist.query.filter_by(user_ID = current_user.user_ID).all()
        song = Song.query.filter_by(song_ID=id).first()
        return render_template ('user/add_song.html',playlists=playlist,song=song)
    else:
        return redirect(url_for('createplaylist'))

@app.route('/user/deletesong<int:id>', methods = ['GET', 'POST'])
@login_required
def deletesong(id):
    playlist_entry = PlaylistSongs.query.filter_by(ID=id).first()
    db.session.delete(playlist_entry)
    db.session.commit()
    flash('Song is now deleted from your playlist!', 'success')
    return redirect (url_for('playlist'))

@app.route('/user/deleteplaylist<int:id>', methods=['GET', 'POST'])
@login_required
def deleteplaylist(id):
    playlist_entry = Playlist.query.filter_by(playlist_ID=id).first()
    db.session.delete(playlist_entry)
    db.session.commit()
    flash('Playlist is now deleted!', 'success')
    return redirect (url_for('userdashboard'))

@app.route('/user/ratesong<int:id>', methods = ['GET', 'POST'])
@login_required
def ratesong(id):
    song = Song.query.filter_by(song_ID=id).first()
    if request.method == 'POST':
        song_rating = int(request.form.get('songr'))
        rating = SongRating.query.filter_by(song_ID = id).first()    
        if rating:
            newRating = ((rating.song_count*rating.song_rating) + song_rating)/(rating.song_count+1)
            newRating = round(newRating, 1)
            rating.song_rating = newRating
            rating.song_count = rating.song_count + 1
            db.session.commit()
        else:
            rating = SongRating(song_ID = id, song_rating = song_rating, song_count = 1)
            db.session.add(rating)
            db.session.commit()
        flash('Rating submitted successfully!', 'success')
        return redirect(url_for('userdashboard', id = id))
    return render_template('user/rate_song.html', song = song)

@app.route('/creator/createalbum', methods = ['GET', 'POST'])
@login_required
def createalbum():
    if current_user.creator_ID == True:
        if request.method=='POST':
            album = request.form.get('album')
            genre = request.form.get('genre')
            newAlbum = Album(album_name = album, genre = genre, artist = current_user.username)
            db.session.add(newAlbum)
            db.session.commit()
            return redirect(url_for('creatordashboard'))
        return render_template('creator/new_album.html')
    return render_template ('user/user_dashboard.html')

@app.route('/creator/addlyrics', methods = ['GET', 'POST'])
@login_required
def addlyrics():
    if current_user.creator_ID == True:
        if request.method == 'POST': 
            sname = request.form.get('sname')
            duration = request.form.get('duration')
            lyrics = request.form.get('lyrics')
            date_created = request.form.get('date')
            date_created=datetime.strptime(date_created, "%Y-%m-%d").date()
            mp3 = request.files['mp3']
            if  date_created == "" or sname == "" or duration == "" or lyrics == "":
                flash('Please fill all values!','danger')
                return redirect(url_for('addlyrics'))
            if Song.query.filter_by(song_name = sname).all():
                flash('Song already exists. Please try a different song!','danger')
                return redirect(url_for('addlyrics'))
            song = Song(song_name=sname, lyrics=lyrics, duration=duration, date_created=date_created, user_ID = current_user.user_ID) 
            db.session.add(song)
            db.session.commit()
            flash('Your song has been uploaded successfully!','success')
            mp3.save("static/songs/" + (sname) + ".mp3")
            return redirect(url_for('addlyrics'))
        return render_template ('creator/add_lyrics.html')
    return render_template ('creator/add_lyrics.html')

@app.route('/creator/editsong<int:id>', methods = ['GET', 'POST'])
@login_required
def editsong(id):
    if current_user.creator_ID == True:
        if request.method == 'POST': 
            sname = request.form.get('sname')
            duration = request.form.get('duration')
            lyrics = request.form.get('lyrics')
            date_created = request.form.get('date')
            date_created=datetime.strptime(date_created, "%Y-%m-%d").date()
            if  date_created == "" or sname == "" or duration == "" or lyrics == "":
                flash('Please fill all values!','danger')
                return redirect(url_for('editsong',id = id))
            song = Song.query.filter_by(song_ID = id).first()
            if current_user.user_ID == song.user_ID:
                song.song_name = sname
                song.duration = duration
                song.lyrics = lyrics
                song.date_created = date_created
                db.session.commit()
                flash('Your song has been edited successfully!','success')
                return redirect(url_for('editsong',id = id))
            flash('You are not the owner of this song!','danger')
            return redirect(url_for('editsong',id = id))
        song = Song.query.filter_by(song_ID = id).first()
        return render_template ('creator/edit_lyrics.html',song = song)
    return render_template ('creator/edit_lyrics.html')

@app.route('/creator/removesong<int:id>', methods = ['GET', 'POST'])
@login_required 
def removesong(id):
    if current_user.creator_ID == True:
        album = Song.query.filter_by(song_ID=id).first()
        mp3 = "static/songs/" + (album.song_name) + ".mp3"
        os.remove(mp3)
        song_rating = SongRating.query.filter_by(song_ID=id).all()
        if current_user.user_ID == album.user_ID:
            album_entry = AlbumSongs.query.filter_by(song_ID=id).all()
            for entry in album_entry:
                db.session.delete(entry)
            playlist_entry = PlaylistSongs.query.filter_by(song_ID=id).all()
            for entry in playlist_entry:
                db.session.delete(entry)
            for rating in song_rating:
                db.session.delete(rating)
            db.session.delete(album)
            db.session.commit()
            flash('Song is now deleted!', 'success')
            return redirect (url_for('creatordashboard'))
        flash('You are not the owner of this song!','danger')
        return redirect (url_for('creatordashboard'))
    return redirect (url_for('creatordashboard'))

@app.route('/creator/assignsong<int:id>', methods = ['GET', 'POST'])
@login_required
def assignsong(id):
    song = Song.query.filter_by(song_ID=id).first()
    if current_user.creator_ID == True:
        if request.method == 'POST':
            if current_user.user_ID == song.user_ID:
                album_id = request.form.get('album_id')
                myalbum = AlbumSongs(album_ID=album_id, song_ID = id)
                db.session.add(myalbum)
                db.session.commit()
                flash('Song is now assigned to your selected album!','success')
                return redirect(url_for('creatordashboard'))
            flash('You are not the owner of this song!','danger')
            return redirect(url_for('creatordashboard'))
    myAlbums=Album.query.filter_by(artist = current_user.username).all()
    if not myAlbums:
        flash ('No album found. Please create an album first!','danger')
        return redirect (url_for('createalbum'))
    return render_template ('creator/assign_song.html',myAlbums=myAlbums,song=song)

@app.route('/creator/creatoralbums', methods = ['GET', 'POST'])
@login_required
def creatoralbums():
        if current_user.creator_ID:    
            query = db.session.query(
                    Song.song_ID,
                    Song.song_name,
                    Song.lyrics,
                    Song.duration,
                    Song.is_flagged,
                    Song.date_created,
                    Album.album_ID,
                    Album.album_name,
                    AlbumSongs.ID
                ).outerjoin(
                    AlbumSongs,
                    AlbumSongs.album_ID == Album.album_ID
                ).outerjoin(
                    Song,
                    Song.song_ID == AlbumSongs.song_ID).filter(Album.artist == current_user.username).all()
            return render_template('creator/albums.html', songs = query)
            # return render_template('creator/albums.html')
        return render_template ('creator/albums.html')

@app.route('/creator/editalbum<int:id>', methods = ['GET', 'POST'])
@login_required 
def editalbum(id):
    if current_user.creator_ID == True:
        if request.method == 'POST':
            aname = request.form.get('aname')
            if  aname == "":
                flash('Please fill all values!','danger')
                return redirect(url_for('editalbum',id = id))
            album = Album.query.filter_by(album_ID = id).first()
            album.album_name = aname
            db.session.commit()
            flash('Your album has been edited successfully!','success')
            return redirect(url_for('editalbum',id = id))
        album = Album.query.filter_by(album_ID = id).first()
        return render_template ('creator/edit_album.html', album = album)
    return render_template ('creator/edit_album.html')    

@app.route('/creator/deletefromalbum<int:id>/<int:id1>', methods = ['GET', 'POST'])
@login_required 
def deletefromalbum(id, id1):
    if current_user.creator_ID == True:
        song = AlbumSongs.query.filter_by(song_ID = id, album_ID = id1).first()
        db.session.delete(song)
        db.session.commit()
        flash('Your song has been deleted successfully from your album!','success')
        return redirect(url_for('creatordashboard'))
    return redirect(url_for('creatordashboard'))

@app.route('/creator/deletealbum<int:id>', methods=['GET', 'POST'])
@login_required
def deletealbum(id):
    if current_user.creator_ID == True:
        album_entry = AlbumSongs.query.filter_by(album_ID=id).all()
        for entry in album_entry:
            db.session.delete(entry)
        album = Album.query.filter_by(album_ID=id).first()
        db.session.delete(album)
        db.session.commit()
        flash('Album is now deleted!', 'success')
        return redirect (url_for('creatordashboard'))
    return redirect (url_for('creatordashboard'))

@app.route('/admindashboard')
@login_required
def admindashboard():
    if current_user.is_admin == True:
        result = db.session.query(
        Song.song_ID,
        Song.song_name,
        Song.lyrics,
        Song.duration,
        Song.is_flagged,
        Song.date_created,
        Album.album_ID,
        Album.album_name,
        Album.genre,
        Album.artist,
        User.user_ID,
        User.username
    ).join(
        Song, User.user_ID == Song.user_ID
    ).outerjoin(
        AlbumSongs,
        Song.song_ID == AlbumSongs.song_ID
    ).outerjoin(
        Album,
        AlbumSongs.album_ID == Album.album_ID
    ).all()
        user_count = db.session.query(User).count()
        creator_count = db.session.query(User).filter(User.creator_ID == True).count()
        song_count = db.session.query(Song).count()
        album_count = db.session.query(Album).count()
        highest_rated_song = db.session.query(Song, SongRating).filter(Song.song_ID == SongRating.song_ID).order_by(SongRating.song_rating.desc()).first()
        highest_count_song = db.session.query(Song, SongRating).filter(Song.song_ID == SongRating.song_ID).order_by(SongRating.song_count.desc()).first()
        return render_template('admin/admin_dashboard.html', user_count = user_count - 1, 
                           creator_count = creator_count,
                           song_count = song_count,
                           album_count = album_count,
                            highest_rated_song = highest_rated_song,
                            highest_count_song = highest_count_song, 
                           result = result)
    return redirect(url_for('home'))

@app.route('/flagsong<int:id>', methods = ['GET', 'POST'])
@login_required
def flagsong(id):
    if current_user.is_admin == True:
        song = Song.query.filter_by(song_ID = id).first()
        if request.method == 'POST':
            reason = request.form.get('reason')
            song.is_flagged = True
            db.session.commit()
            flash('Song is now flagged!', 'success')
            return redirect(url_for('admindashboard', id = id, reason = reason))
        return render_template('admin/flag_song.html', song = song)
    return redirect(url_for('admindashboard'))

@app.route('/flagcreator<string:id>', methods = ['GET', 'POST'])
@login_required
def flagcreator(id):
    if current_user.is_admin == True:
        user = User.query.filter_by(username = id).first()
        if request.method == 'POST':
            user.is_flagged = True
            db.session.commit()
            flash('Creator is now flagged!', 'success')
            return redirect(url_for('admindashboard'))
        return render_template('admin/flag_creator.html', user = user)
    return redirect(url_for('admindashboard'))

@app.route('/flagalbum<int:id>', methods = ['GET', 'POST'])
@login_required
def flagalbum(id):
    if current_user.is_admin == True:
        album = Album.query.filter_by(album_ID = id).first()
        if request.method == 'POST':
            album.is_flagged = True
            db.session.commit()
            flash('Album is now flagged!', 'success')
            return redirect(url_for('admindashboard'))
        return render_template('admin/flag_album.html', album = album)
    return redirect(url_for('admindashboard'))

@app.route('/removesong<int:id>', methods = ['GET', 'POST'])
@login_required 
def adminremovesong(id):
    if current_user.is_admin == True:
        song = Song.query.filter_by(song_ID=id).first()
        album_entry = AlbumSongs.query.filter_by(song_ID=id).all()
        for entry1 in album_entry:
            db.session.delete(entry1)
        playlist_entry = PlaylistSongs.query.filter_by(song_ID=id).all()
        for entry2 in playlist_entry:
            db.session.delete(entry2)
        song_rating = SongRating.query.filter_by(song_ID=id).all()
        for rating in song_rating:
            db.session.delete(rating)
        db.session.delete(song)
        db.session.commit()
        flash('Song is now deleted!', 'success')
        return redirect (url_for('admindashboard'))
    return redirect (url_for('admindashboard'))

@app.route('/removealbum<int:id>', methods=['GET', 'POST'])
@login_required 
def adminremovealbum(id):
    if current_user.is_admin == True:
        album = Album.query.filter_by(album_ID=id).first()
        album_entry = AlbumSongs.query.filter_by(album_ID=id).all()
        for entry in album_entry:
            db.session.delete(entry)
            db.session.commit()
        if album:
            db.session.delete(album)
            db.session.commit()
            flash('Album is now deleted!', 'success')
            return redirect(url_for('admindashboard'))
        return redirect(url_for('admindashboard'))
    return redirect(url_for('admindashboard'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    q = request.args.get('query')
    result = db.session.query(
    Song.song_ID,
    Song.song_name,
    Song.lyrics,
    Song.duration,
    Song.is_flagged,
    Song.date_created,
    User.username,
    Album.album_ID,
    Album.album_name,
    Album.genre,
    Album.artist,   
    Album.is_flagged,
    SongRating.rating_ID,
    SongRating.song_rating
).\
join(User, Song.user_ID == User.user_ID).\
outerjoin(AlbumSongs, Song.song_ID == AlbumSongs.song_ID).\
outerjoin(Album, AlbumSongs.album_ID == Album.album_ID).\
outerjoin(SongRating, Song.song_ID == SongRating.song_ID).\
filter((User.username.ilike('%' + q + '%')) | (SongRating.song_rating.ilike('%' + q + '%')) | (Album.artist.ilike('%' + q + '%')) | (Album.genre.ilike('%' + q + '%')) | (Song.song_name.ilike('%' + q + '%')))
    results = result.all()
    return render_template('user/search.html', results = results, q=q)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

db.create_all()
if __name__ == '__main__':
    app.run(debug = True)