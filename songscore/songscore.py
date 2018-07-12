from flask import Flask, render_template, flash, redirect, url_for, request, session, logging, g, Response, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_sslify import SSLify
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from hashlib import md5
from functools import wraps
import os

app = Flask(__name__) # creates an instance of flask
app.config.from_object(__name__) # load config from this file (songscore.py)
app.config.update({
    'SECRET_KEY' : os.environ['SECRET_KEY'],
    'SQLALCHEMY_DATABASE_URI' : os.environ['DATABASE_URL'],
    'SQLALCHEMY_TRACK_MODIFICATIONS' : 'false',
    'PREFERRED_URL_SCHEME' : 'https'
})
db = SQLAlchemy(app)

sslify = SSLify(app)
#app.debug = False
#########
# WRAPS #
#########

# Make a page so you need to be logged in by adding "@is_logged_in" after the @app.route
def is_logged_in(f):
    @wraps(f) #pass in 'f'
    def wrap(*args, **kwargs): #idk what this means tbh
        if 'logged_in' in session: #check they're logged into a session
            return f(*args, **kwargs)
        else:
            flash('Yo you dont have access for this get outta here', 'danger') #danger type of alert
            return redirect(url_for('login')) #prompt them to log in
    return wrap

#########
# INDEX #
#########

@app.route('/')
def index():
    if session.get('logged_in', False):
        return redirect(url_for('feed'))
    else:
        return redirect(url_for('register'))

###########################
# LOG IN / OUT / REGISTER #
###########################

@app.route('/register', methods=['GET', 'POST']) # needs to accept posts to collect data from the form
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate(): # need to make sure the request is post, and that it matches the validation
        db.session.add(User(
            username=form.username.data,
            email=form.email.data,
            name=form.name.data,
            password=sha256_crypt.encrypt(str(form.password.data)),
            picture = "https://www.gravatar.com/avatar/%s?d=https://songscore.herokuapp.com/static/images/profile.png" % md5(form.email.data.encode('utf-8')).hexdigest()
        ))
        db.session.commit()

        flash('You are now registered and can log in', 'success') # format this for a good message
        return redirect(url_for('login'))
    else:
        return render_template('register.html', form=form) # if not a POST, it must be a get. Serve the form.

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Not using WTForms cos there's no point
    if request.method == 'POST': # if they submit some data, catch it from the form
        user = User.query.filter_by(username = request.form['username']).one_or_none()

        if user != None: # user exists
            if sha256_crypt.verify(request.form['password'], user.password): # pass the password entered and the actual password found into sha256
                session['logged_in'] = True
                session['user_id'] = user.id
                session['username'] = user.username
                # flash('You will hopefully now be logged in (no promises lol)', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Password is incorrect'
                return render_template('login.html', error=error)
        else:
            error = 'Username does not exist'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html') # else, they're not submitting anything. Redirect to login page.

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#################
# NOTIFICATIONS #
#################

@app.route('/notifications')
@is_logged_in
def notifications():
    notifications = {}
    notifications['likes'] = [] # query_db(" SELECT users.username, subjects.name AS subject_name FROM likes JOIN users ON users.id = likes.user_id JOIN reviews ON reviews.id = likes.review_id JOIN subjects ON subjects.id = reviews.subject_id WHERE reviews.user_id = %s AND likes.seen = false ", (session['user_id'],))
    notifications['likes'] = [] # Likes.query.filter_by(
    notifications['dislikes'] = [] # query_db(" SELECT users.username, subjects.name AS subject_name FROM dislikes JOIN users ON users.id = dislikes.user_id JOIN reviews ON reviews.id = dislikes.review_id JOIN subjects ON subjects.id = reviews.subject_id WHERE reviews.user_id = %s AND dislikes.seen = false ", (session['user_id'],))
    notifications['comments'] = [] # query_db(" SELECT users.username, subjects.name AS subject_name, comments.text FROM comments JOIN users ON users.id = comments.user_id JOIN reviews ON reviews.id = comments.review_id JOIN subjects ON subjects.id = reviews.subject_id WHERE reviews.user_id = %s AND comments.seen = false ", (session['user_id'],))
    notifications['follows'] = [] # query_db(" SELECT users.username FROM follows JOIN users ON users.id = follows.follower_id WHERE following_id = %s AND seen = false ", (session['user_id'],))
    notifications['review_mentions'] = [] #query_db("SELECT * FROM review_mentions WHERE mentioned_id = %s AND seen = false", (session['user_id'],))
    notifications['comment_mentions'] = [] #query_db("SELECT * FROM comment_mentions WHERE mentioned_id = %s AND seen = false", (session['user_id'],))
    return render_template('notifications.html', notifications=notifications)

########
# FEED #
########

@app.route('/feed')
@is_logged_in
def feed():
    return redirect(url_for('feed_all'))

@app.route('/feed/all')
@is_logged_in
def feed_all():
    reviews = Review.query.order_by(db.desc(Review.datetime))[0:10]
    from datetime import datetime
    return render_template('feed.html', reviews=reviews)

@app.route('/feed/following')
@is_logged_in
def feed_following():
    ###############
    # BROKEN CODE #
    ###############
    #user = User.query.filter_by(id=session['user_id']).one()
    #reviews = []
    #holdreviews = []
    #for x in user.following:
    #holdreviews.append(x.reviews)
    #return render_template('feed.html', reviews=holdreviews)
    reviews = Review.query.order_by(db.desc(Review.datetime)).all()
    from datetime import datetime
    return render_template('feed.html', reviews=reviews, datetime=datetime, currenttime=datetime.now())

#################
# USER PROFILES #
#################

@app.route('/profile')
@is_logged_in
def profile():
    return redirect(url_for('user_page', username=session['username']))

@app.route('/user/<username>')
def user_page(username):
    if User.query.filter_by(username=username).one_or_none():
        return redirect(url_for('user_reviews', username=username))
    else:
        abort(404)

@app.route('/user/<username>/reviews')
def user_reviews(username):
    user = User.query.filter_by(username=username).one()
    if user:
        from datetime import datetime
        return render_template('reviews.html', user=user, reviews=user.reviews, datetime=datetime, currenttime=datetime.now())
    else:
        abort(404)

@app.route('/user/<username>/following')
def user_following(username):
    user = User.query.filter_by(username=username).one_or_none()
    if user:
        return render_template('following.html', user=user, following=user.following)
    else:
        abort(404)

@app.route('/user/<username>/followers')
def user_followers(username):
    user = User.query.filter_by(username=username).one()
    if user:
        return render_template('followers.html', user=user, followers=user.followers)
    else:
        abort(404)

@app.route('/user/<username>/likes')
def user_likes(username):
    user = User.query.filter_by(username=username).one_or_none()
    if user:
        return render_template('likes.html', user=user, likes=user.likes)
    else:
        abort(404)

@app.route('/user/<username>/dislikes')
def user_dislikes(username):
    user = User.query.filter_by(username=username).one_or_none()
    if user:
        return render_template('dislikes.html', user=user, dislikes=user.dislikes)
    else:
        abort(404)

@app.route('/user/<username>/comments')
def user_comments(username):
    user = User.query.filter_by(username=username).one()
    if user:
        return render_template('comments.html', user=user, comments=user.comments)
    else:
        abort(404)

###########
# ACTIONS #
###########

@app.route('/follow', methods=['POST'])
def follow():
    user = User.query.filter_by(id=session['user_id']).one()
    user.following.append(User.query.filter_by(id=request.form['user_id']).one())
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/submit', methods=['POST'])
def submit_review():
    subject = Subject.query.filter_by(
        name=request.form['subject_name'],
        artist_name=request.form['subject_artist_name'],
        type=request.form['subject_type']
    ).first()

    if subject == None: # not yet in the database
        db.session.add(Subject(
                name=request.form['subject_name'],
                artist_name=request.form['subject_artist_name'],
                type=request.form['subject_type'],
                art=request.form['subject_image']
        ))
        subject = Subject.query.filter_by(
            name=request.form['subject_name'],
            artist_name=request.form['subject_artist_name'],
            type=request.form['subject_type']
        ).first()

    db.session.add(Review(user_id=session['user_id'],stars=request.form['rating'],subject_id=subject.id,text=request.form['text']))
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/delete', methods=['POST'])
def delete():
    db.session.delete(Review.query.filter_by(id=request.form['review_id']).one())
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/like', methods=['POST'])
def like():
    user = User.query.filter_by(id=session['user_id']).one()
    user.likes.append(Review.query.filter_by(id=request.form['review_id']).one())
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/dislike', methods=['POST'])
def dislike():
    user = User.query.filter_by(id=session['user_id']).one()
    user.dislikes.append(Review.query.filter_by(id=request.form['review_id']).one())
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/comment', methods=['POST'])
def submit_comment():
    db.session.add(ReviewComment(user_id=session['user_id'], review_id=request.form['review_id'], text=request.form['text']))
    db.session.commit()
    return redirect(url_for("index"))

##########
# ERRORS #
##########

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

###############
# SQL ALCHEMY #
###############

class ReviewComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id', ondelete='CASCADE'), nullable=False)

    text = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    seen = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="comments") # ~
    review = db.relationship("Review", back_populates="comments")  # done

dislikes = db.Table('dislikes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('review_id', db.Integer, db.ForeignKey('review.id', ondelete='CASCADE')),
    db.Column('seen', db.Boolean, default=False, nullable=False)
)

follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('following_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('seen', db.Boolean, default=False, nullable=False)
)

likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('review_id', db.Integer, db.ForeignKey('review.id', ondelete='CASCADE')),
    db.Column('seen', db.Boolean, default=False, nullable=False)
)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)

    text = db.Column(db.Text)
    stars = db.Column(db.Integer, nullable=False) # db.Constraint("(stars >= 1) AND (stars <= 5)") TODO
    datetime = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    user = db.relationship('User', back_populates='reviews')
    subject = db.relationship('Subject', back_populates='reviews')

    comments = db.relationship('ReviewComment', back_populates='review') #, cascade="all, delete-orphan", single-parent=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, nullable=False) # db.Constraint("(type = 'album') OR (type ='song')" TODO

    name = db.Column(db.String, nullable=False)
    artist_name = db.Column(db.String, nullable=False)
    art = db.Column(db.String, nullable=False, default='/static/images/subject.png')

    reviews = db.relationship('Review', back_populates='subject') #, cascade="all, delete-orphan")#, single-parent=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    picture = db.Column(db.String, nullable=False)
    register_datetime = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    reviews = db.relationship('Review', back_populates='user', order_by='desc(Review.datetime)') #, cascade="all, delete-orphan", single-parent=True)
    comments = db.relationship('ReviewComment', back_populates='user', order_by='desc(ReviewComment.datetime)') #, cascade="all, delete-orphan") #, single-parent=True)
    likes = db.relationship('Review', secondary='likes', order_by='desc(Review.datetime)') #, cascade="all, delete-orphan", single-parent=True)
    dislikes = db.relationship('Review', secondary='dislikes', order_by='desc(Review.datetime)') #, cascade="all, delete-orphan", single-parent=True)
    following = db.relationship(
        'User', secondary=follows,
        primaryjoin=(follows.c.follower_id == id),
        secondaryjoin=(follows.c.following_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic') #, cascade="all, delete-orphan")

#########
# FORMS #
#########

class RegisterForm(Form):
    usernames = [ user.username for user in User.query.all() ]
    name = StringField(
        'Name',
        [ validators.DataRequired(), validators.Length(min=1, max=50) ]
    )
    username = StringField(
        'Username',
        [ validators.DataRequired(), validators.Length(min=4, max=25), validators.NoneOf(usernames, message="username taken!") ]
    )
    email = StringField(
        'Email', [ validators.DataRequired(), validators.Email(), validators.Length(min=6, max=100) ]
    )
    password = PasswordField (
        'Password',
        [
            validators.DataRequired(),
            validators.EqualTo('confirm', message='The passwords need to match yo'),
            validators.Length(min=8, max=100)
        ]
    )
    confirm = PasswordField('Confirm Password')
