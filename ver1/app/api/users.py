from fileinput import filename
from flask import jsonify, request, current_app, url_for, g
from sqlalchemy import true
from . import api
from ..models import User, Problem, Solve
import os
from werkzeug.utils import secure_filename
from flask import send_file, send_from_directory, flash
import shutil
from flask_login import current_user, login_required
from .decorators import admin_required_vs, permission_required_vs, prof_required_vs, moderator_required_vs
import subprocess
from .. import db

path = os.path.dirname(os.path.abspath(__file__))  # /home/codelab/ver1/app/api
# /home/codelab/ver1/app/api/problems
problems_path = os.path.join(path, "problems")
codes_path = os.path.join(path, "codes")  # /home/codelab/ver1/app/api/codes
grading_path = os.path.join(path, "grading")


@api.route('/temp', methods=['GET'])  # 수정바람
def grading():
    filepath = os.path.join(path, "grading/")
    username = g.current_user.username
    id = g.current_user.id
    problem_id = Problem.query.filter_by(title='B001')  # 수정바람
    error = None

    sourcecode = 1  # 수정바람
    if not sourcecode:
        error = 'Sourcecode is required'

    if error is not None:
        flash(error)
    else:
        filename = 'bracket'

        subprocess.call(filepath + "compile.sh " +
                        filename + " " + str(id), shell=True)
        # resf = open(filepath + "results/result_" + filename + ".txt", 'r')
        # result = resf.readline().strip()
        # print(result + "Aa")

    return '', 200


@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    print(path)
    return jsonify(user.to_json())


@api.route('problems/<id>', methods=['GET'])  # 문제 file list 반납
def get_filenames(id):
    problem_path = os.path.join(problems_path, id, '')

    file_list = os.listdir(problem_path)

    if len(file_list) >= 1:
        return {'file_list': file_list}, 200
    else:
        return '', 404

# 문제 파일 다운로드


@api.route('problems/<id>/<filename>', methods=['GET'])
def get_problem(id, filename):
    problem_path = os.path.join(problems_path, id)

    file = os.path.join(problems_path, id, secure_filename(filename))

    if file:
        return send_file(file, download_name=filename, as_attachment=True, attachment_filename=filename)
    else:
        return '', 404


ALLOWED_EXTENSIONS = set(
    ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'c', 'md', 'h'])

STUDENT_ALLOWED_EXTENSIONS = set(['c', 'h'])


def allowed_file(filename):
    return ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS) or 'Makefile'
def student_allowed_file(filename):
    return ('.' in filename and filename.rsplit('.', 1)[1].lower() in STUDENT_ALLOWED_EXTENSIONS)


# 교수 문제 제출
@api.route('problems/<problem_title>', methods=['POST'])
@prof_required_vs
def upload_problem(problem_title):
    problem_path = os.path.join(problems_path, problem_title)
    grading_problem_path = os.path.join(grading_path, problem_title)
    data = request.get_json()
    
    filenames = data['files']['filename'] # file명
    filedatas = data['files']['file'] # file 데이터

    print(filenames)
    
    for idx, filename in enumerate(filenames):
        filenames[idx] = secure_filename(filename)
    
    if not os.path.isdir(problem_path):
        os.mkdir(problem_path)
        os.chmod(problem_path, 0o777)
        
        os.mkdir(grading_problem_path)
        os.mkdir(os.path.join(grading_problem_path, 'cases'))
        os.mkdir(os.path.join(grading_problem_path, 'results'))
        os.mkdir(os.path.join(grading_problem_path, 'src'))
        os.mkdir(os.path.join(grading_problem_path, 'cases', 'programs'))
    
    prof_filelist = ['input.txt', 'output.txt', 'makefile', problem_title.lower()] # 교수가 제출하면 grading으로 갈 파일리스트

    flag = False
    for filename, filedata in zip(filenames, filedatas):
        txtfilename = None
        
        if allowed_file(filename):
            if filename.lower() in prof_filelist:
                if filename == 'input.txt':
                    txtfilename = os.path.join(grading_problem_path, 'cases', 'input.txt')
                elif filename == 'Makefile':
                    # 학생도 받을 수 있도록
                    txtfilename = os.path.join(problem_path, filename)
                    f = open(txtfilename, "w+", encoding='utf-8')
                    f.write(filedata)
                    f.close()  
                    
                    txtfilename = os.path.join(grading_problem_path, 'src', 'Makefile')
                elif filename.lower() == problem_title.lower() or 'output.file':
                    txtfilename = os.path.join(grading_problem_path, 'cases', 'programs', filename.lower())
            else: # 학생에게 줄 파일들
                txtfilename = os.path.join(problem_path, filename)
        
            f = open(txtfilename, "w+", encoding='utf-8')
            f.write(filedata)
            f.close()              
            flag = True  
            
            if filename.lower() == problem_title.lower(): # 실행파일 권한 주기
                os.chmod(txtfilename, 0o777)
                

    if flag:
        # db 문제 등록
        problem = Problem(title=problem_title)
        db.session.add(problem)
        
        problem_id = Problem.query.filter_by(title=problem_title).first().id
        users = User.query.all()
        for user in users:
            solve = Solve(problem_id=problem_id, user_id=user.id)
            db.session.add(solve)
        db.session.commit()
        
        resp = jsonify({'message': 'Problem successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(
            {'message': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif, c, md'})
        resp.status_code = 400
        return resp


# 교수 문제 삭제
@api.route('problems/<problem_title>', methods=['DELETE'])
@prof_required_vs
def delete_problem(problem_title):
    problem_path = os.path.join(problems_path, problem_title)
    grading_problem_path = os.path.join(grading_path, problem_title)

    if os.path.isdir(problem_path):
        shutil.rmtree(problem_path)
        shutil.rmtree(grading_problem_path)
        resp = jsonify({'message': 'Problem successfully delete'})
        resp.status_code = 200
        return resp
    else:
        resp = jsonify({'message': 'Not exist problem ID'})
        resp.status_code = 200
        return resp

# 학생코드 삭제
@api.route('student_codes/<username>/<problem_title>', methods=['DELETE'])
@moderator_required_vs
def delete_code(username, problem_title):
    user_id = str(g.current_user.id)
    problem_path = os.path.join(codes_path, problem_title)
    student_code_path = os.path.join(problem_path, user_id)
    grading_src_path = os.path.join(path, "grading", problem_title, "src")


    if os.path.isdir(student_code_path):
        shutil.rmtree(student_code_path)
        
        if os.path.isdir(grading_src_path):
            grading_src_list = os.listdir(grading_src_path)
            for file in grading_src_list:
                if file != 'Makefile':
                    os.remove(os.path.join(grading_src_path, file))
        
        resp = jsonify({'message': 'Code successfully delete'})
        resp.status_code = 200
        return resp
    else:
        resp = jsonify({'message': 'Not exist Code'})
        resp.status_code = 200
        return resp

# 학생코드 제출
@api.route('student_codes/<username>/<problem_title>', methods=['POST'])
@moderator_required_vs
def upload_code(username, problem_title):
    
    data = request.get_json()
    filenames = data['files']['filename'] # file명
    filedatas = data['files']['file'] # file 데이터
    user_id = str(g.current_user.id)
    username = g.current_user.username
    executable_file = None
    
    # /home/codelab/ver1/app/api/codes/<problem_title>
    problem_path = os.path.join(codes_path, problem_title)
    # /home/codelab/ver1/app/api/codes/<problem_title>/<username>
    student_code_path = os.path.join(problem_path, user_id)
    grading_src_path = os.path.join(path, "grading", problem_title, "src")


    # dir없으면 생성
    if not os.path.isdir(problem_path):
        os.mkdir(problem_path)
        os.chmod(problem_path, 0o777)
    if not os.path.isdir(student_code_path):
        os.mkdir(student_code_path)
        os.chmod(student_code_path, 0o777)

    for filename, filedata in zip(filenames, filedatas):
        if allowed_file(filename):
            if student_allowed_file(filename):
                # grading에 저장
                txtfilename = os.path.join(grading_src_path, filename)
                f = open(txtfilename, "w+", encoding='utf-8')
                f.write(filedata)
                f.close()      

                # code에 저장
                txtfilename = os.path.join(student_code_path, filename)
                f = open(txtfilename, "w+", encoding='utf-8')
                f.write(filedata)
                f.close()
                
        else:
            resp = jsonify(
                {'message': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif, c, h'})
            resp.status_code = 400
            return resp

    # 채점
    filepath = os.path.join(path, "grading/")

    error = None
    sourcecode = 1  # 수정바람
    if not sourcecode:
        error = 'Sourcecode is required'

    if error is not None:
        flash(error)
    else:
        executable_file = problem_title.lower() + '_' + user_id
        subprocess.call("make -C " + grading_src_path, shell=True) # 학생 코드 makefile 실행
        os.rename(os.path.join(grading_src_path, problem_title.lower()), os.path.join(grading_src_path, problem_title.lower()) + '_' + user_id)
        subprocess.call(filepath + "compile.sh " +
                        executable_file + " " + user_id + " " + problem_title, shell=True)
    
    
    out = os.system("diff -bZ {} {}".format(os.path.join(grading_path, problem_title, "results", "result_" + user_id + ".txt"), os.path.join(grading_path, problem_title, "cases", "programs", "output.txt")))
    
    message = None
    if out != 0:
        print("Wrong Answer\n")
        message = "Wrong Answer"
    else:
        print("맞았습니다\n")
        message = "Correct Answer"
    
    resp = jsonify({'message': message})
    resp.status_code = 200
    return resp


    # if file and allowed_file(filename):
    #     txtfilename = os.path.join(student_code_path, filename)
    #     f = open(txtfilename, "w+", encoding='utf-8')
    #     f.write(file)
    #     f.close()
    #     resp = jsonify({'message': 'Problem successfully uploaded'})
    #     resp.status_code = 201
    #     return resp
    # else:
    #     resp = jsonify(
    #         {'message': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif, c'})
    #     resp.status_code = 400
    #     return resp


# 문제 리스트 가져오기


@api.route('problems/list', methods=['GET'])
@moderator_required_vs
def problem_list():
    problems = Solve.query.filter_by(user_id=g.current_user.id).all()

    unresolved_list = []
    resolved_list = []
    print(g.current_user.id)
    for problem in problems:
        title = Problem.query.filter_by(id=problem.problem_id).first().title
        if (problem.resolved == False):
            unresolved_list.append(title)
        elif (problem.resolved == True):
            resolved_list.append(title)

    return jsonify({"Solved_Problems": unresolved_list, "Resolved_Problems": resolved_list}), 200

