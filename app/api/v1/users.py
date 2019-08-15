from flask import abort, current_app, g, jsonify, request, url_for

from app import db
from app.api.v1 import bp
from app.api.v1.auth import token_auth
from app.api.v1.errors import bad_request
from app.models import User


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    """Retrieve a JSON list of all users who's account isn't private."""
    if g.current_user.username == 'guest':
        abort(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page,
            'api.v1.get_users')
    return jsonify(data)


@bp.route('/users/<public_id>', methods=['GET'])
@token_auth.login_required
def get_user(public_id):
    """Retrieve a user's profile. If it's the user's own profile, inlcude
    their email."""
    if g.current_user.username == 'guest':
        abort(403)
    query_results = User.query.filter_by(public_id=public_id).first()
    if g.current_user.public_id == public_id:
        return jsonify(query_results.to_dict(include_email=True))
    return jsonify(query_results.to_dict())


@bp.route('/users/<public_id>/follow', methods=['POST'])
@token_auth.login_required
def follow_user(public_id):
    if g.current_user.username == 'guest':
        abort(403)
    follow_user = User.query.filter_by(public_id=public_id).first()
    g.current_user.follow(follow_user)
    #query_results = User.query.filter_by(public_id=public_id).first()
    #return jsonify(query_results.to_dict())
    return '', 200


@bp.route('/users/<public_id>/follow', methods=['DELETE'])
@token_auth.login_required
def unfollow_user(public_id):
    if g.current_user.username == 'guest':
        abort(403)
    follow_user = User.query.filter_by(public_id=public_id).first()
    g.current_user.unfollow(follow_user)
    db.session.commit()
    return '', 204


@bp.route('/users/<public_id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(public_id):
    if g.current_user.username == 'guest':
        abort(403)
    user = User.query.filter_by(public_id=public_id).first()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
            'api.v1.get_followers', public_id=public_id)
    return jsonify(data)


@bp.route('/users/<public_id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(public_id):
    if g.current_user.username == 'guest':
        abort(403)
    user = User.query.filter_by(public_id=public_id).first()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
            'api.v1.get_followed', public_id=public_id)
    return jsonify(data)


@bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user. Requires a json with username, email, name, and
    password.
    """
    data = request.get_json() or {}     # ensure data is always a dict
    if 'username' not in data or 'email' not in data or 'name' not in data or \
            'password' not in data:
        return bad_request('must include username, email, name, and password '
                'fields')
    data['username'] = data['username'].lower().strip()
    data['email'] = data['email'].lower().strip()
    data['name'] = data['name'].strip()
    if User.query.filter_by(username=data['username']).first() or \
            data['username'] in current_app.config['BLOCKED_USERNAMES']:
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    if data['email'] in current_app.config['ADMINS']:
        data['group'] = 'admin'
    else:
        data['group'] = 'user'
    user = User()
    user.from_dict(data, new_user=True)     # Import and add user data
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict(include_email=True))
    response.status_code = 201  # Code to indicate new entity was created
    response.headers['Location'] = url_for('api.v1.get_user',
            public_id=user.public_id)
    return response


@bp.route('/users/<public_id>', methods=['PUT'])
@token_auth.login_required
def update_user(public_id):
    """Edit an existing user. Each data field is optional, so check if the
    field is provided before cleaning and verifying the value."""
    # Restrict user edits to the current user or admins
    if g.current_user.public_id == public_id or g.current_user.group == 'admin' \
            or g.current_user.username != 'guest':
        pass
    else:
        abort(403)
    user = User.query.filter_by(public_id=public_id).first()
    data = request.get_json() or {}
    if 'username' in data:
        data['username'] = data['username'].lower().strip()
        if data['username'] != user.username and \
                (User.query.filter_by(username=data['username']).first() or
                data['username'] in current_app.config['BLOCKED_USERNAMES']):
            # If username is different and either username exists or is blocked
            return bad_request('please use a different username')
    if 'email' in data:
        data['email'] = data['email'].lower().strip()
        if data['email'] != user.email and \
                User.query.filter_by(email=data['email']).first():
            # If email is different and already exists
            return bad_request('please use a different email address')
    if 'name' in data:
        data['name'] = data['name'].strip()
    user.from_dict(data, new_user=False)    # Import and update user data
    db.session.commit()
    return jsonify(user.to_dict(include_email=True))


@bp.route('/users/<public_id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(public_id):
    """Delete an existing user. DO NOT delete oneself."""
    if g.current_user.group != 'admin' or g.current_user.public_id == public_id:
        abort(403)
    user = User.query.filter_by(public_id=public_id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return '', 204
