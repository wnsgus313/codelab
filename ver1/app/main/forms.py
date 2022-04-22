from flask_wtf import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo
from wtforms import ValidationError
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from flask import flash
from ..models import Role, User, Permission
from sqlalchemy import desc

# class CodeForm(FlaskForm):
#     code = StringField('Roomcode', validators=[
#         DataRequired(), Length(1, 64),
#         Regexp('^[A-Za-z0-9_.]*$', 0, 'Room code must have only letters, numbers, dots or underscores')])
#     roomname = StringField('Roomname', validators=[
#         DataRequired(), Length(1, 64),
#         Regexp('^[A-Za-z0-9_.\sㄱ-ㅣ가-힣]*$', 0, 'Room name must have only letters, numbers, dots or underscores')])
#     submit = SubmitField('만들기')
    
#     def validate_code(self, field):
#         if Room.query.filter_by(room_code = field.data).first():
#             flash('Code already in used.')
#             raise ValidationError("Code already in used.")

class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

class EditProfileAdminForm(FlaskForm):
    # email = StringField('Email', validators=[DataRequired(), Length(1, 64),
    #                                          Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    # def validate_email(self, field):
    #     if field.data != self.user.email and \
    #             User.query.filter_by(email=field.data).first():
    #         raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class EditProfileProfForm(FlaskForm):
    # email = StringField('Email', validators=[DataRequired(), Length(1, 64),
    #                                          Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileProfForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).offset(1).all()]
        self.user = user

    # def validate_email(self, field):
    #     if field.data != self.user.email and \
    #             User.query.filter_by(email=field.data).first():
    #         raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class EditProfileModeratorForm(FlaskForm):
    # email = StringField('Email', validators=[DataRequired(), Length(1, 64),
    #                                          Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileModeratorForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(desc(Role.id)).offset(2).all()]
        self.user = user

    # def validate_email(self, field):
    #     if field.data != self.user.email and \
    #             User.query.filter_by(email=field.data).first():
    #         raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')