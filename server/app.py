# Imports
import os

from flask import Flask
from flask_cors import CORS
from flask_graphql import GraphQLView

from server.database.db import db
from server.schema import schema

basedir = os.path.abspath(os.path.dirname(__file__))

# app initialization
app = Flask(__name__)
CORS(app)
app.debug = True

# Configs
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = "somesecret"

# Modules
db.init_app(app)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


@app.route('/')
def index():
    return '<p>Home page</p>'


if __name__ == '__main__':
    app.run()
