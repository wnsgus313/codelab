from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User, Room, Regist, TA, Token
from . import api
from .errors import unauthorized, forbidden
from datetime import datetime
from .. import db

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token.lower()).first()

    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/tokens/', methods=['POST', 'GET'])
def get_token():
    if g.token_used:
        return unauthorized('Invalid credentials')

    now = datetime.now()

    tokens_all = Token.query.all()
    if tokens_all is not None:
        for tokens in tokens_all:
            diff = now - tokens.timestamp
            if tokens.user_id == g.current_user.id:
                db.session.delete(tokens)
                db.session.commit()
            elif diff.seconds > 3600:
                db.session.delete(tokens)
                db.session.commit()

    token = Token(user_id=g.current_user.id)
    db.session.add(token)
    db.session.commit()

    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})

    