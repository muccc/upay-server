from flask import Flask, make_response, jsonify

app = Flask(__name__)
app.config.from_envvar('UPAY_SERVER_CONFIG', True)

# utilities
from .utils import initialize_logging
initialize_logging()

# import implementation modules
import api_v1

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'} ), 404)

