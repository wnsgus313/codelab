from xml.etree.ElementTree import tostring
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, jsonify, g
from flask.wrappers import Response
from . import main
from .. import db
from ..models import User, Problem, Code, Expected, Input, Post, Permission, Role, Comment, Log
from flask_login import current_user, login_required
import json, time
import subprocess
import time
import os.path
from sys import stderr
import os
from filecmp import cmp
from .forms import EditProfileForm, EditProfileAdminForm, EditProfileProfForm, EditProfileModeratorForm, LoginForm

import io
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

from werkzeug.utils import secure_filename
from ..decorators import admin_required, permission_required, prof_required

path = os.path.dirname(os.path.abspath(__file__))

@main.route('/problem/<title>', methods = ['GET', 'POST'])
@login_required
def problem(title):
    user = User.query.filter_by(id = current_user.id).first()
    problem = Problem.query.filter_by(title = title).first()
    input_db = Input.query.filter_by(problem_id=problem.id).first()
    expected_db = Expected.query.filter_by(problem_id=problem.id).first()

    code = "#include <stdio.h>\n\nint main()\n{\n\n\treturn 0;\n}"

    inputs = []
    outputs = []
    pfs = []
    expecteds = []

    inputs_print = [input_db.input1, input_db.input2, input_db.input3, input_db.input4]
    expecteds_print = [expected_db.expected1, expected_db.expected2, expected_db.expected3, expected_db.expected4]

    if request.method == 'POST':

        # 실행
        if request.form['submit-button'] == 'play':
            code = request.form['code']
            question = request.form['question']
            inputs_list = ['input1', 'input2', 'input3', 'input4']
            outputs = []
            pfs = []
            for i in inputs_list:
                if request.form.get(i) is not None:
                    inputs.append(request.form[i])

            temp_path = os.path.join(path, 'code', title, user.student_id)
            if not os.path.isdir(temp_path):
                os.mkdir(temp_path)
                os.chmod(temp_path, 0o777)


            real_path = os.path.join(temp_path, '')

            mode = ['c']
            cfilename = real_path + mode[0] + "file.c"
            file = open(cfilename, "wb")
            file.write(request.form['code'].encode('utf-8'))
            file.close()
            
            for i in range(len(inputs)):
                txtfilename = real_path + inputs_list[i] + ".txt" 
                file = open(txtfilename, "w+", encoding='utf-8')
                file.write(request.form[inputs_list[i]])
                file.close()

            for i in range(len(inputs)):
                txtfilename = real_path + "expecteds" + str(i+1) + ".txt" 
                file = open(txtfilename, "w+", encoding='utf-8')
                file.write(request.form['expected'+str(i+1)])
                file.close()


            out = ""
            err = ""

            first = '/home/KOJ3/app/file/file'
            if os.path.isfile(first):
                os.remove(first)

            cmd = f'bash /home/KOJ3/app/compile.sh {real_path}'.split()

            
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
            out, err = p.communicate()

            # if p.returncode == 124: # timeout
            #     for i in range(len(inputs)):
            #         txtfilename = real_path + "output" + str(i+1) + ".txt" 
            #         file = open(txtfilename, "w+", encoding='utf-8')
            #         file.write("Time out!!")
            #         file.close()

            ## compile error
            for i in range(len(inputs)):
                if os.path.getsize(real_path + 'compile_error.txt'):
                    txtfilename = real_path + "output" + str(i+1) + ".txt" 
                    file = open(txtfilename, "w+", encoding='utf-8')
                    file2 = open(real_path + 'compile_error.txt', "r")
                    data = file2.read()
                    file.write(data)
                    file.close()
                    file2.close()
            
            ## timeout
            for i in range(len(inputs)):
                if os.path.isfile(real_path + 'Timeout' + str(i+1) + '.txt'):
                    txtfilename = real_path + "output" + str(i+1) + ".txt" 
                    file = open(txtfilename, "w+", encoding='utf-8')
                    file2 = open(real_path + 'Timeout' + str(i+1) + '.txt')
                    data = file2.read()
                    file.write(data)
                    file.close()
                    file2.close()

            ## floating error
            for i in range(len(inputs)):
                if os.path.isfile(real_path + 'SIGFPE' + str(i+1) + '.txt'):
                    txtfilename = real_path + "output" + str(i+1) + ".txt" 
                    file = open(txtfilename, "w+", encoding='utf-8')
                    file2 = open(real_path + 'SIGFPE' + str(i+1) + '.txt')
                    data = file2.read()
                    file.write(data)
                    file.close()
                    file2.close()

            # segment fault
            for i in range(len(inputs)):
                if os.path.isfile(real_path + 'SIGSEGV' + str(i+1) + '.txt'):
                    txtfilename = real_path + "output" + str(i+1) + ".txt" 
                    file = open(txtfilename, "w+", encoding='utf-8')
                    file2 = open(real_path + 'SIGSEGV' + str(i+1) + '.txt')
                    data = file2.read()
                    file.write(data)
                    file.close()
                    file2.close()
            
            # make outputs
            for i in range(len(inputs)):
                txtfilename = real_path + "output" + str(i+1) + ".txt" 
                with open(txtfilename, "r+", encoding='utf-8') as file:
                    outputs.append(file.read())
                    file.close()


            for i in range(len(inputs)):
                # print(request.form['expected'+str(i+1)].replace("\r",""), type(request.form['expected'+str(i+1)].replace("\r","")))
                expecteds.append(request.form['expected'+str(i+1)].replace("\r",""))


            for i in range(len(inputs)):
                if expecteds[i] == outputs[i]:
                    pfs.append("Pass")
                else:
                    pfs.append("Fail")
            

            # remove files
            for i in range(len(inputs)):
                filename = real_path + "input" + str(i+1) + ".txt"
                filename2 = real_path + "output" + str(i+1) + ".txt"
                filename3 = real_path + "expecteds" + str(i+1) + ".txt"
                filename4 = real_path + "SIGFPE" + str(i+1) + ".txt"
                filename5 = real_path + "SIGSEGV" + str(i+1) + ".txt"
                filename6 = real_path + "Timeout" + str(i+1) + ".txt"
                os.system(f'rm {filename}')
                os.system(f'rm {filename2}')
                os.system(f'rm {filename3}')
                if os.path.isfile(filename4):
                    os.system(f'rm {filename4}')
                if os.path.isfile(filename5):
                    os.system(f'rm {filename5}')
                if os.path.isfile(filename6):
                    os.system(f'rm {filename6}')

    
            return render_template('main/1st.html', title=title, user=user, output=out, code=code, inputs=inputs, outputs=outputs, pfs=pfs, expecteds=expecteds, question=problem.body, problem_id=problem.id)

        # 저장
        elif request.form['submit-button'] == 'save':
            code = request.form['code']
            inputs_list = ['input1', 'input2', 'input3', 'input4']
            expecteds_list = ['expected1', 'expected2', 'expected3', 'expected4']
            question = request.form['question']

            for i in inputs_list:
                if request.form.get(i) is not None:
                    inputs.append(request.form[i])

            for i in expecteds_list:
                if request.form.get(i) is not None:
                    expecteds.append(request.form[i])

            for i in range(len(inputs)):
                if i == 0:
                    input_db.input1 = request.form[inputs_list[i]]
                    pfs.append("")
                    outputs.append("")
                elif i == 1:
                    input_db.input2 = request.form[inputs_list[i]]
                    pfs.append("")
                    outputs.append("")
                elif i == 2:
                    input_db.input3 = request.form[inputs_list[i]]
                    pfs.append("")
                    outputs.append("")
                elif i == 3:
                    input_db.input4 = request.form[inputs_list[i]]
                    pfs.append("")
                    outputs.append("")
                db.session.commit()

            for i in range(len(inputs)):
                if i == 0:
                    expected_db.expected1 = request.form['expected'+str(i+1)].replace("\r","")
                elif i == 1:
                    expected_db.expected2 = request.form['expected'+str(i+1)].replace("\r","")
                elif i == 2:
                    expected_db.expected3 = request.form['expected'+str(i+1)].replace("\r","")
                elif i == 3:
                    expected_db.expected4 = request.form['expected'+str(i+1)].replace("\r","")
                db.session.commit()

            problem.body = question
            db.session.commit()
            
            return render_template('main/1st.html', user=user, code=code, inputs=inputs, outputs=outputs, pfs=pfs, expecteds=expecteds, question=problem.body, title=title, problem_id=problem.id)

    for input in inputs_print:
        if input is not None:
            inputs.append(input)
            pfs.append("")
            outputs.append("")

    for expected in expecteds_print:
        if expected is not None:
            expecteds.append(expected)
    

    return render_template('main/1st.html', user=user, code=code, inputs=inputs, outputs=outputs, pfs=pfs, expecteds=expecteds, question=problem.body, title=title, problem_id=problem.id)


@main.route('/', methods = ['GET', 'POST'])
@login_required
def index():
    user = User.query.filter_by(id = current_user.id).first()
    if request.method == 'POST':
        title = request.form['title']
        if Problem.query.filter_by(title = title).first() is None:
            new_problem = Problem(title = title)
            db.session.add(new_problem)
            db.session.commit()

            problem = Problem.query.filter_by(title = title).first()
            input = Input(problem_id=problem.id)
            expected = Expected(problem_id=problem.id)
            db.session.add(input)
            db.session.add(expected)
            db.session.commit()

            # make title dir
            if not os.path.isdir(os.path.join(path, 'code', title)):
                os.mkdir(os.path.join(path, 'code', title))
                os.chmod(os.path.join(path, 'code', title), 0o777)

        else:
            flash("Title alreaey exist!")

    problems = Problem.query.all()
    return render_template('main/problem_list.html', problems=problems, user=user)

@main.route('/user/<email>')
def user(email):
    user = User.query.filter_by(email=email).first_or_404()
    # page = request.args.get('page', 1, type=int)
    # pagination = User.query.order_by(User.last_seen.desc()).paginate(
    #     page, per_page=current_app.config['FLASKY_USERS_PER_PAGE'], error_out=False
    # )
    return render_template('main/user.html', user=user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.student_id = form.name.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', email=current_user.email))
    form.name.data = current_user.student_id
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@prof_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    if user.role.name == 'Administrator':
        form = EditProfileAdminForm(user=user)
    elif user.role.name == 'Prof':
        form = EditProfileProfForm(user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.student_id = form.name.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', email=user.email))
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.student_id
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/find-student', methods=['GET', 'POST'])
@login_required
@prof_required
def findStudent():
    students = User.query.all()
    return render_template('find_student.html', students=students)

# 검색한 학생 이메일 받음
@main.route('/find-student/submit', methods=['GET', 'POST'])
@login_required
@prof_required
def findStudent_change():
    student_email = request.form['up']
    all_user = User.query.all()
    print(student_email)
    if User.query.filter_by(email=student_email).first(): 
        student = User.query.filter_by(email=student_email).first()
    else:
        flash("Unregistered student.")
        return render_template('find_student.html', students=all_user)
        # user = current_user     
        # return render_template('main/user.html', user=user)
    if student.role == Role.query.filter_by(name='Administrator').first() or student.role == Role.query.filter_by(name='Prof').first():
        flash("This person is not student. Administrator or Professor.")
        # user = current_user     
    elif student.role == Role.query.filter_by(name='Moderator').first():
        flash("This person is already Permitted as Moderator")
    else:
        student.role = Role.query.filter_by(name='Moderator').first()
        db.session.add(student)
        db.session.commit()
        flash(student.email + "'s Permission has changed to Moderator")
        return render_template('find_student.html', students=all_user)
    return render_template('find_student.html', students=all_user)

@main.route('/find-prof', methods=['GET', 'POST'])
@login_required
@prof_required
def findProf():
    students = User.query.all()
    return render_template('find_prof.html', students=students)

# 검색한 학생 이메일 받음
@main.route('/find-prof/submit', methods=['GET', 'POST'])
@login_required
@prof_required
def findProf_change():
    student_email = request.form['up']
    all_user = User.query.all()
    print(student_email)
    if User.query.filter_by(email=student_email).first(): 
        student = User.query.filter_by(email=student_email).first()
    else:
        flash("Unregistered person.")
        return render_template('find_prof.html', students=all_user)
        # user = current_user     
        # return render_template('main/user.html', user=user)
    if student.role == Role.query.filter_by(name='Administrator').first() or student.role == Role.query.filter_by(name='Prof').first():
        flash("This person is already Administrator or Professor.")
        # user = current_user     
    else:
        student.role = Role.query.filter_by(name='Prof').first()
        db.session.add(student)
        db.session.commit()
        flash(student.email + "'s Permission has changed to Professor")
        return render_template('find_prof.html', students=all_user)
    return render_template('find_prof.html', students=all_user)

    
@main.route('/saveCode', methods = ['GET','POST'])
@login_required
def saveCode():
    data = request.get_json()
    code_db = Code.query.filter_by(user_id=current_user.id, problem_id=data['problem_id']).first()

    if code_db is None:
        code_db = Code(user_id=current_user.id, problem_id=data['problem_id'])

    code_db.source = data['code']
    db.session.commit()
    return make_response(jsonify(data), 200)

@main.route('/getCode', methods=['POST'])
@login_required
def getCode():
    data = request.get_json()
    code_db = Code.query.filter_by(user_id=current_user.id, problem_id=data['problem_id']).first()

    if code_db is None:
        code_db = Code(user_id=current_user.id, problem_id=data['problem_id'])

    db.session.commit()

    code = dict(code=code_db.source)

    return make_response(jsonify(code), 200)


@main.route('/problems/list')
@login_required
def problem_list():
    problems = Problem.query.all()

    return render_template('main/problems.html', problems=problems)

@main.route('/problems/<title>')
def problem_content(title):
    problem = Problem.query.filter_by(title=title).first()

    return render_template('main/problem_view.html', problem=problem)    

@main.route('/problems/submit', methods = ['GET'])
@login_required
def problem_submit_get():
    user = User.query.filter_by(id = current_user.id).first()
    if user.role == 1:
        return render_template('main/problem_submit.html')

    return render_template('main/problem_view.html')

@main.route('/problems/submit', methods = ['POST'])
@login_required
def problem_submit():
    name = request.form['name']
    title = request.form['title']
    body = request.form['body']

    problem = Problem(name=name, title=title, body=body)
    db.session.add(problem)
    db.session.commit()

    return render_template('main/problem_submit.html')

@main.route('/enterChatroom', methods=['GET', 'POST'])
def enterChatroom():
    form = LoginForm()
    if form.validate_on_submit():
        user = form.username.data
        if user is not None:
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.chatroom',)
            return redirect(next)
        flash('Invalid username or password.')

    return render_template('main/enterChatroom.html', form=form)

@main.route('/chatroom', methods=['GET', 'POST'])
def chatroom():
    if request.method == 'POST':
        error = None    
        jsonData = request.get_json(force = True)
        body = jsonData['body']
        comment = None
        username = request.args.get('nickname', default="Anonymous")

        if not body:
            error = 'Comment is required'
        
        if error is not None:
            flash(error)
        else:
            comment = Comment(username = username, body = body)
            db.session.add(comment)
            db.session.commit()

            data = {
                "body": comment.body, 
                "username": comment.username, 
                "time": comment.timestamp,
            }
            
            return make_response(jsonify(data), 200)
        
    comments = Comment.query.filter_by().all()
    return render_template('main/chatroom.html', comments = comments)

@main.route('/get_comments', methods=['POST'])
def get_comments():
    data = request.get_json()
    comments = Comment.query.all()
    # comments = Comment.query.filter_by(room_id = room_id, group = group).all()
    comments_dict = [] 
    for comment in comments:
        comments_dict.append(
            {
                "body": comment.body, 
                "username": comment.username, 
                "time": comment.timestamp,
            }
        )
    return make_response(jsonify(comments_dict), 200)


@main.route('/find-problem', methods=['GET', 'POST'])
@login_required
@prof_required
def findProblem():
    problems = Problem.query.all()
    return render_template('find_problem.html', problems=problems)

# 검색한 학생 이메일 받음
@main.route('/find-problem/submit', methods=['GET', 'POST'])
@login_required
@prof_required
def findProblem_change():
    problem_title = request.form['up']
    all_problem = Problem.query.all()
    if Problem.query.filter_by(title=problem_title).first(): 
        problem = Problem.query.filter_by(title=problem_title).first()
    else:
        flash("Unregistered problem.")
        return render_template('find_prof.html', problems=all_problem)
        # user = current_user     
        # return render_template('main/user.html', user=user)
    if problem.permission == True:
        flash("This problem already has permission.")
        # user = current_user     
    else:
        problem.permission = True
        db.session.commit()
        flash(problem.title + "'s Permission has changed")
        return render_template('find_problem.html', problems=all_problem)
    return render_template('find_problem.html', problems=all_problem)



# vscode 채팅
@main.route('/chat', methods=['GET', 'POST'])
def chatrooms():
    token = request.args.get('token')
    username = request.args.get('username')
    user_id = None
    if token is not None and username is not None:
        user_id = User.verify_auth_token(token)
        
    if request.method == 'POST':
        error = None    
        jsonData = request.get_json(force = True)
        body = jsonData['body']
        username = jsonData['username']
        user_id = jsonData['user_id']

        comment = None

        if not body:
            error = 'Comment is required'
        
        if error is not None:
            flash(error)
        else:
            comment = Comment(user_id = user_id, username = username, body = body)
            db.session.add(comment)
            db.session.commit()

            data = {
                "body": comment.body, 
                "username": comment.username, 
                "time": comment.timestamp,
                "username": username,
            }
            
            return make_response(jsonify(data), 200)
        
    if user_id is None:
        return render_template('403.html')

    comments = Comment.query.filter_by().all()
    return render_template('main/chat.html', comments = comments, user_id=user_id, username=username)

@main.route('/comments_get', methods=['POST'])
def comments_get():
    data = request.get_json()
    comments = Comment.query.all()
    # comments = Comment.query.filter_by(room_id = room_id, group = group).all()
    comments_dict = [] 
    for comment in comments:
        comments_dict.append(
            {
                "body": comment.body, 
                "username": comment.username, 
                "time": comment.timestamp,
            }
        )
    return make_response(jsonify(comments_dict), 200)


# 프로그래밍 실습 평균데이터 전송
@main.route('/practice/<username>', methods=['POST'])
def get_practice_codes_data(username):
    jsonData = request.get_json(force = True)
    username = jsonData['username']
    user_id = jsonData['user_id']
    
    user = User.query.filter_by(username=username).first()
    users = Log.query.group_by(Log.user_id).all()
    log = Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).first()
    
    ones = [Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).first() for user in users]
    threes = [Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).limit(3).all() for user in users]
    tens = [Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).limit(10).all() for user in users]
    
    threes_length = [[i.length for i in three] for three in threes] # [[50, 25, 25], [25]]
    tens_length = [[i.length for i in ten] for ten in tens]
    
    ones_minute = [one.length for one in ones]
    threes_minute = [round(sum(three_length)/3) for three_length in threes_length]
    tens_minute = [round(sum(ten_length)/10) for ten_length in tens_length]
    
    
    users = [user.username for user in users]
    data = {'users': users, 'code':log.code, 'ones_minute': ones_minute, 'threes_minute': threes_minute, 'tens_minute': tens_minute};
    
    return make_response(jsonify(data), 200)

# 프로그래밍 실습 학생 코드 받기
@main.route('/practice/<username>', methods=['GET'])
def get_practice_codes(username):
    # token = request.args.get('token')
    # username = request.args.get('username')
    # user_id = None
    # if token is not None and username is not None:
    #     user_id = User.verify_auth_token(token)
    # if user_id is None:
    #     return render_template('403.html')
    
    user_id=1#temp
    
    user = User.query.filter_by(username=username).first()
    users = Log.query.group_by(Log.user_id).all()
    log = Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).first()
    
    ones = [Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).first() for user in users]
    threes = [Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).limit(3).all() for user in users]
    tens = [Log.query.filter_by(username=user.username).order_by(Log.timestamp.desc()).limit(10).all() for user in users]
    
    threes_length = [[i.length for i in three] for three in threes] # [[50, 25, 25], [25]]
    tens_length = [[i.length for i in ten] for ten in tens]
    
    ones_minute = [one.length for one in ones]
    threes_minute = [round(sum(three_length)/3) for three_length in threes_length]
    tens_minute = [round(sum(ten_length)/10) for ten_length in tens_length]

    return render_template('main/programming_practice.html', user_id=user_id, code=log.code, username=username, users=users, ones_minute=ones_minute, threes_minute=threes_minute, tens_minute=tens_minute, zip=zip)

@main.route('/practice/matplot/<username>.png', methods=['GET'])
def matplot(username):
    logs = Log.query.filter_by(username=username).all()
    num_x_points = len(logs)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = [i for i in range(1, num_x_points+1)]
    axis.plot(x_points, [i.length for i in logs])
    
    
    output = io.BytesIO()
    FigureCanvasSVG(fig).print_svg(output)
    
    return Response(output.getvalue(), mimetype="image/svg+xml")