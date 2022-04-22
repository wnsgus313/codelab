import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Problem, Code, Expected, Input, Post, Role, Permission, Solve

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Problem=Problem, Code=Code, Expected=Expected, Input=Input, Post=Post, Role=Role, Permission=Permission, Solve=Solve)