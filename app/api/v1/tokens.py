from flask import g, jsonify

from app import db
from app.api.v1 import bp
from app.api.v1.auth import basic_auth, token_auth


@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    """Generate a token for the user, but only after ensuring they have
    authenticated themselves via the basic auth login (providing a valid
    username and password).
    """
    token = g.current_user.get_token(expires_in=60*60*24*7)
    db.session.commit()
    return jsonify({
        'public_id': g.current_user.public_id,
        'username': g.current_user.username,
        'token': token
    })


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204
