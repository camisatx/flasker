from flask import abort, g, jsonify, request, url_for
from sqlalchemy import exc

from app import db
from app.api.v1 import bp
from app.api.v1.auth import token_auth
from app.models import Content


@bp.route('/content', methods=['GET'])
def get_all_content():
    """Retrieve all content."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 30, type=int), 100)
    text = request.args.get('text', False, type=bool)
    data = Content.content_to_collection_dict(
            Content.query \
                .filter(Content.status) \
                .order_by(Content.phase.asc(), Content.section.asc()),
            page, per_page, 'api.v1.get_all_content', text=text)
    return jsonify(data)


@bp.route('/content/<public_id>', methods=['GET'])
def get_content(public_id):
    """Retrieve a specified content."""
    query_results = Content.query.filter_by(public_id=public_id).first_or_404()
    return jsonify(query_results.to_dict(true=True))


@bp.route('/content', methods=['POST'])
@token_auth.login_required
def create_content():
    """Create a new content section."""
    if g.current_user.group not in ['admin']:
        abort(403)
    data = request.get_json() or {}

    # Add the content section
    content = Content()
    content.from_dict(data, new=True)
    try:
        db.session.add(content)
        db.session.commit()
    except exc.IntegrityError:
        db.session().rollback()
        return '', 400

    response = jsonify(content.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.v1.get_content',
            public_id=content.public_id)
    return response


@bp.route('/content/<public_id>', methods=['PUT'])
@token_auth.login_required
def update_content(public_id):
    """Update an existing content section"""
    if g.current_user.group not in ['admin']:
        abort(403)
    content = Content.query.filter_by(public_id=public_id).first_or_404()
    data = request.get_json() or {}

    # Update the main content data
    content.from_dict(data, new=False)

    db.session.commit()
    return jsonify(content.to_dict())


@bp.route('/content/<public_id>', methods=['DELETE'])
@token_auth.login_required
def delete_content(public_id):
    """Delete an existing content section. Does NOT retain history."""
    if g.current_user.group != 'admin':
        abort(403)
    content = Content.query.filter_by(public_id=public_id).first_or_404()

    db.session.delete(content)
    db.session.commit()
    return '', 204
