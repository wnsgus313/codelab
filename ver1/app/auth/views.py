from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, \
    current_user
from . import auth
from .. import db, client
from ..models import User
from ..email import send_email
from .forms import LoginForm, RegistrationForm
import json, requests
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import check_password_hash, generate_password_hash
# from googleLogin.db import init_db_command
# from googleLogin.user import User

@auth.before_app_request
def before_request():
    #print("@@@@@ current_user.user_id")
    # if current_user is None:
    #     print("None!!!!!!!")
    #print(current_user.user_id)
    if current_user.is_authenticated():
        # current_user.ping()
        if not current_user.is_anonymous:
            if not current_user.confirmed \
                    and request.endpoint \
                    and request.blueprint != 'auth' \
                    and request.endpoint != 'static':
                return redirect(url_for('auth.unconfirmed'))
    # print("Not authenticated!!!!!")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


def get_google_provider_cfg():
    app = current_app._get_current_object()
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@auth.route('/google_login', methods=['GET', 'POST'])
def google_login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
 
    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    print("request_uri")
    print(request_uri)
    return redirect(request_uri) # request_uri는 로그인할 주소
    #return render_template('auth/googlelogin.html')

@auth.route("/google_login/callback")
def callback():
    # Get authorization code Google sent back to you
    app = current_app._get_current_object()
    code = request.args.get("code")
    print("code: ", code)
 
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    print(token_endpoint) # https://oauth2.googleapis.com/token

    url = request.url.replace('http://', 'https://', 1)
    base_url = request.base_url.replace('http://', 'https://', 1)
    print("replace")
    print(url)
    print(base_url) # https://siskin21.cafe24.com/13thweek/auth/google_login/callback

    # url = request.url
    # base_url = request.base_url

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=url,
        redirect_url=base_url.replace('https://', 'http://', 1),
        code=code
    )
    print("token_url")
    print(token_url)

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_OAUTH_CLIENT_ID'], app.config['GOOGLE_OAUTH_CLIENT_SECRET']),
    )
    print("body: ")
    print(body)
    
    print("token_response.url:")
    print(token_response.url)
    # Parse the tokens!
    print(token_response.json())
    print("json.dumps(token_response.json())")
    print(json.dumps(token_response.json()))
    client.parse_request_body_response(json.dumps(token_response.json()))
 
    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    print(userinfo_response.json())
    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["name"]
    else:
        return "User email not available or not verified by Google.", 400
 
    # Create a user in our db with the information provided
    # by Google
 
    # Doesn't exist? Add to database
    if not User.query.filter_by(email = users_email).first():
        user = User(
            username=users_name, email=users_email, student_id=users_email.split('@')[0]
        )
        db.session.add(user)
        db.session.commit()

    # Begin user session by logging the user in
    user = User.query.filter_by(email = users_email).first()
    login_user(user)
    
 
    # Send user back to homepage
    return redirect(url_for('main.index'))

@auth.route('/logout')
@login_required
def logout():
    current_user.ping()
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower(),
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def changePassword():
    if request.method == 'POST':
        #username = request.form['username']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        password_conf = request.form['password_conf']
        error = None
        user = User.query.filter_by(email=current_user.email).first()

        if not user.verify_password(old_password):
            error = 'Incorrect password.'
        else:
            error = None
            if new_password == password_conf:
                newp = generate_password_hash(new_password)
                user.password_hash = newp
                db.session.add(user)
                db.session.commit()
                flash('Password has changed.')
                return redirect(url_for('main.edit_profile'))
            else: 
                error = 'The password confirmation does not match.'
        flash(error)
    return render_template('change_password.html')

