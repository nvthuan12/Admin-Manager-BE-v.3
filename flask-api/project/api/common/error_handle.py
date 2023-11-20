from flask import jsonify

def handle_werkzeug_exception(e):
    description = e.description if e.description else str(e)
    response = {
        "error_type": e.__class__.__name__,
        "description": description
    }
    return jsonify(response), e.code
