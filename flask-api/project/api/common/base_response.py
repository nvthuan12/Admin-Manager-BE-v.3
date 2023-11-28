from flask import jsonify
from werkzeug.exceptions import HTTPException
class BaseResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        response = {
            "status": status_code,
            "message": message,
            "data": data
        }
        return jsonify(response)

    @staticmethod
    def error(e):
        description = e.description if e.description else str(e)
        response = {
        "error_type": e.__class__.__name__,
        "message": description
        }
        return jsonify(response), e.code