import json

import cachetools
from flask import Flask, redirect
import pandas as pd
import sqlalchemy
from sqlalchemy import sql
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS


app = Flask(__name__, static_folder='crypto-opportunity-front-end/dist', static_url_path='')
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour", "30 per minute"],
    storage_uri="memory://",
)
CORS(app)

secret_sauce = json.load(open('secret_sauce.json',))


@app.route('/')
def status():
    return "ok"


if __name__ == '__main__':
    app.run(port=5000, debug=True)
