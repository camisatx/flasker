import base64
from datetime import datetime, timedelta
import json
import os
from time import time

from flask import current_app, url_for
from flask_login import UserMixin
import jwt
from passlib.hash import argon2
import redis
import rq

from app import db


class IdMixin():
    id = db.Column(db.Integer, primary_key=True)


class TimestampMixin():
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)


class PaginatedApiMixin():
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        """Produces a dictionary representing a collection, including the
        items, _meta, and _links. Useful for returning collection of user
        followers."""
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total,
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                        **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                        **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                        **kwargs) if resources.has_prev else None
            },
        }
        return data


followers = db.Table(
        'followers',
        db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, IdMixin, TimestampMixin, PaginatedApiMixin, db.Model):
    public_id = db.Column(db.String(24), index=True, unique=True, nullable=False)
    # Username: lowercase and strip
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    # Email: lowercase and strip
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime, nullable=True)
    password_hash = db.Column(db.String(512), nullable=False)
    group = db.Column(db.String(100), index=True, nullable=False)   # user, admin
    # Name: Strip
    name = db.Column(db.String(100), nullable=True)
    about_me = db.Column(db.String(200), nullable=True)
    points = db.Column(db.Integer, nullable=True)
    privacy = db.Column(db.Boolean, default=False, nullable=True)
    token = db.Column(db.String(128), index=True, unique=True, nullable=True)
    token_expiration = db.Column(db.DateTime, nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    followed = db.relationship('User', secondary=followers,
            primaryjoin='User.id == followers.c.follower_id',
            secondaryjoin='User.id == followers.c.followed_id',
            backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    notifications = db.relationship('Notification', backref='user',
            lazy='dynamic', cascade='all,delete')
    tasks = db.relationship('Task', backref='user', lazy='dynamic',
            cascade='all,delete')
    # Add relationships to other user related tables here

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = argon2.using(rounds=10, digest_size=32,
                salt_size=32, memory_cost=128000).hash(password)

    def check_password(self, password):
        return argon2.verify(password, self.password_hash)

    def get_confirmation_token(self, expired_in=60*60*24*7):
        return jwt.encode(
            {'confirm_email': self.id, 'exp': time() + expired_in},
            current_app.config['SECRET_KEY'], algorithm='HS512').decode('utf-8')

    @staticmethod
    def verify_confirmation_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                    algorithms=['HS512'])['confirm_email']
        except Exception:   # invalid or expired
            return None
        return User.query.get(id)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS512').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                    algorithms=['HS512'])['reset_password']
        except Exception:   # invalid or expired
            return None
        return User.query.get(id)

    def add_notification(self, name, data):
        """Add a notification for the user. If the same notification already
        exists in the database, delete it first then add it again.

        :param name: String of the name of the notification
        :data: Dictionary (json) type data
        """
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        """Submits a task to the RQ queue and adds it to the database

        :param name: String of the function name
        :param description: String of the task description
        :return: Model object of the task
        """
        # Send the job to the rq worker (task_queue setup in __init__)
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,
                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        """Return a list of all tasks outstanding for this user"""
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        """Returns a specific task that has not yet been completed. Can be
        used to prevent a user from launching two or more of the same task
        concurrently."""
        return Task.query.filter_by(name=name, user=self, complete=False).\
                first()

    def is_following(self, user):
        return self.followed.filter(
                followers.c.followed_id == user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def to_dict(self, include_email=False):
        """Convert the user object into a JSON object"""
        data = {
            'public_id': self.public_id,
            'username': self.username,
            'group': self.group,
            'name': self.name,
            'about_me': self.about_me,
            'points': self.points,
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.v1.get_user', public_id=self.public_id),
                'followers': url_for('api.v1.get_followers',
                    public_id=self.public_id),
                'followed': url_for('api.v1.get_followed',
                    public_id=self.public_id),
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        """Convert a data object into a user object"""
        for field in ['username', 'email', 'group', 'name', 'about_me',
                'privacy', 'points']:
            if field in ['username', 'email']:
                # Make username and email case insensitive
                data[field] = data[field].lower().strip()
            elif field == 'name':
                data[field] = data[field.strip()]
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
            public_id = base64.b64encode(os.urandom(18)).decode('utf-8')
            self.public_id = public_id.replace('/', 'J')    # replace /

    def get_token(self, expires_in=3600):
        """Return a token to the user. If there is an existing token that has
        at least a minute left before expiration, return that token. Otherwise,
        generate a new token that is 128 characters long."""
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        # Create a token with 128 random characters (96 bytes -> 128 char)
        self.token = base64.b64encode(os.urandom(96)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        """Immediately invoke the token via the expiration date"""
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        """Return the user the provided token belongs to."""
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Notification(IdMixin, db.Model):
    public_id = db.Column(db.String(24), index=True, unique=True, nullable=False)
    name = db.Column(db.String(128), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.Float, index=True, default=time, nullable=True)
    payload_json = db.Column(db.Text, nullable=True)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(TimestampMixin, db.Model):
    """Maintain state of what tasks each user is running"""
    # Special text ID
    id = db.Column(db.String(36), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), index=True, nullable=False)
    description = db.Column(db.String(128), nullable=True)
    complete = db.Column(db.Boolean, default=False, nullable=True)

    def get_rq_job(self):
        """Loads the RQ Job instance using the given task id"""
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        """Returns the progress percentage for the task.

        Assumes a progress of 0 if the job is scheduled but hasn't run yet,
        and a progress of 100 if the job id doesn't exist in the RQ queue (job
        already finished and data expired)."""
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
