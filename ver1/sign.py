from logging import log
import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Problem, Code, Role, Permission, Comment, Log, Room, Regist, TA, Video, Token

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Problem=Problem, Code=Code, Role=Role, Permission=Permission, Comment=Comment, Log=Log, Room=Room, Regist=Regist, TA=TA, Video=Video, Token=Token)