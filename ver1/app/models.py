import datetime
from datetime import datetime, timedelta
from email.policy import default
import hashlib
from sqlalchemy import null
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin, current_user
from app.exceptions import ValidationError
from . import db, login_manager
import hashlib
from flask import g

class Regist(db.Model):
    __tablename__ = 'regist'
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class Permission:
    GENERAL = 1
    AFFILIATE = 2
    PROF = 4
    ADMIN = 8

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.GENERAL],
            'Moderator': [Permission.GENERAL, Permission.AFFILIATE],
            'Prof': [Permission.GENERAL, Permission.AFFILIATE, Permission.PROF],
            'Administrator': [Permission.GENERAL, Permission.AFFILIATE,
                              Permission.PROF,Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

        def __repr__(self):
            return '<Role %r>' % self.name

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm



class Code(db.Model):
    __tablename__ = "code"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id', ondelete="CASCADE"))
    problem = db.relationship(
        "Problem",
        back_populates="code"
    )
    
    pf = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'{self.user_id}, {self.problem_id}, {self.pf}'


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    student_id = db.Column(db.String(64), unique=True, index=True)
    # role = db.Column(db.Integer, default=0)
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow())
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow() + timedelta(hours=9))
    avatar_hash = db.Column(db.String(32))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def ping(self):
        self.last_seen = datetime.utcnow() + timedelta(hours=9)
        db.session.add(self)
        db.session.commit()

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    ## 간단한 password 때문에 등록, 구글로그인만 사용시 삭제
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration = 3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
        
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
        }
        return json_user
    ## 여기까지

    def __repr__(self):
        return '<User %r>' % self.username

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def is_prof(self):
        return self.can(Permission.PROF)

    def is_affiliate(self):
        return self.can(Permission.AFFILIATE)

    def is_user(self):
        return self.can(Permission.USER)
    

@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    print(User.query.get(int(user_id)))
    return User.query.get(int(user_id))

class Problem(db.Model):
    __tablename__ = 'problem'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), index=True)
    body = db.Column(db.String(10000))
    permission = db.Column(db.Boolean, default=False)
    
    code = db.relationship(
        "Code",
        back_populates="problem",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete="CASCADE"))
    room = db.relationship(
        "Room",
        back_populates="problem"
    )
    
    def __repr__(self):
        return '<Problem %r>' % self.title

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64)) # 닉네임
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(), index=True, default=datetime.utcnow() + timedelta(hours=9))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    def __repr__(self):
        return f'{self.user_id}, {self.body}, {self.timestamp}'
    
class Log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64), index=True)
    code = db.Column(db.Text)
    length = db.Column(db.Integer)
    total_length = db.Column(db.Integer)
    flag = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete="CASCADE"))
    room = db.relationship(
        "Room",
        back_populates="log"
    )
    def __repr__(self):
        return f'{self.user_id}, {self.code}, {self.timestamp}, {self.length}\n'


class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(128), unique=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ta = db.relationship(
        "TA",
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    problem = db.relationship(
        "Problem",
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    log = db.relationship(
        "Log",
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    video = db.relationship(
        "Video",
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class TA(db.Model):
    __tablename__ = "ta"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    room = db.relationship(
        "Room",
        back_populates="ta"
    )
    
    def __repr__(self):
        return f'{self.user_id}'

class Video(db.Model):
    __tablename__ = "video"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    video_name = db.Column(db.String(64), index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    flag = db.Column(db.Integer, default=False)
    room = db.relationship(
        "Room",
        back_populates="video"
    )
    
    def __repr__(self):
        return f'{self.user_id}'

class Token(db.Model):
    __tablename__ = "tokens"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime(), index=True, default= datetime.utcnow() + timedelta(hours=9))
    
    def __repr__(self):
        return f'{self.user_id}, {self.timestamp}'