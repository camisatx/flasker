from flask import abort, jsonify

from app.api.v1 import bp

"""Example file showing how to create API routes for data"""


data = {
    '737': {'name': 'Boeing 737', 'manufacturer': 'Boeing', 'model': '737',
        'type': 'short haul', 'uses': ['passenger']},
    '747': {'name': 'Boeing 747', 'manufacturer': 'Boeing', 'model': '747',
        'type': 'long haul', 'uses': ['passenger', 'cargo']},
    '757': {'name': 'Boeing 757', 'manufacturer': 'Boeing', 'model': '757',
        'type': 'long haul', 'uses': ['passenger']},
    '777': {'name': 'Boeing 777', 'manufacturer': 'Boeing', 'model': '777',
        'type': 'long haul', 'uses': ['passenger', 'cargo']},
    '787': {'name': 'Boeing 787', 'manufacturer': 'Boeing', 'model': '787',
        'type': 'long haul', 'uses': ['passenger']},
    'A320': {'name': 'Airbus A320', 'manufacturer': 'Airbus', 'model': 'A320',
        'type': 'short haul', 'uses': ['passenger']},
    'A380': {'name': 'Airbus A380', 'manufacturer': 'Airbus', 'model': 'A380',
        'type': 'long haul', 'uses': ['passenger', 'cargo']},
}


@bp.route('/planes', methods=['GET'])
def get_planes():
    """Retrieve a JSON list of many planes."""
    return jsonify(data)


@bp.route('/planes/<model>', methods=['GET'])
def get_plane(model):
    if data.get(model):
        return jsonify(data[model])
    else:
        abort(404)
