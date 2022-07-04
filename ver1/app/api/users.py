from fileinput import filename
from flask import jsonify, request, current_app, url_for, g
from sqlalchemy import true
from . import api
from ..models import User, Problem, Code, Comment, Log, Room, Regist, TA, Video
import os
from werkzeug.utils import secure_filename
from flask import send_file, send_from_directory, flash
import shutil
from flask_login import current_user, login_required
from .decorators import admin_required_vs, permission_required_vs, prof_required_vs, moderator_required_vs
import subprocess
from .. import db
from io import BytesIO
from collections import OrderedDict

path = os.path.dirname(os.path.abspath(__file__))  # /home/codelab/ver1/app/api
# /home/codelab/ver1/app/api/problems
problems_path = os.path.join(path, "problems")
codes_path = os.path.join(path, "codes")  # /home/codelab/ver1/app/api/codes
grading_path = os.path.join(path, "grading")
videos_path = os.path.join(path, 'videos')


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


@api.route('problems/<lab>/<id>', methods=['GET'])  # 문제 file list 반납
def get_filenames(lab, id):
    problem_path = os.path.join(problems_path, lab, id, '')

    file_list = os.listdir(problem_path)

    if len(file_list) >= 1:
        return {'file_list': file_list}, 200
    else:
        return '', 404

# 문제 파일 다운로드
@api.route('problems/<labname>/<id>/<filename>', methods=['GET'])
def get_problem(id, filename, labname):
    problem_path = os.path.join(problems_path, labname, id)

    file = os.path.join(problems_path, labname, id, secure_filename(filename))

    if file:
        return send_file(file, download_name=filename, as_attachment=True, attachment_filename=filename)
    else:
        return '', 404

## pdf 다운로드
@api.route('problems/<lab>/<id>/<filename>.pdf', methods=['GET'])
def get_problem2(lab, id, filename):
    problem_path = os.path.join(problems_path, lab, id)

    file = os.path.join(problems_path, lab, id, secure_filename(filename))

    if file:
        return send_file(file, download_name=filename, as_attachment=True, attachment_filename=filename, mimetype="application/pdf")
    else:
        return '', 404

## 비디오 다운로드
@api.route('video/<lab>/<video_name>', methods=['GET'])
def get_video(lab, video_name):

    room = Room.query.filter_by(room_name=lab).first()

    student_id = str(Video.query.filter_by(video_name=video_name, room_id=room.id).first().id)

    video = Video.query.filter_by(video_name=video_name, room_id=room.id).first()

    problem_path = os.path.join(videos_path, lab)

    file = os.path.join(problem_path, secure_filename(video_name))

    is_ta = TA.query.filter_by(user_id=g.current_user.id, room_id=room.id).first()

    if file and is_ta is not None:
        video.flag = 1
        db.session.add(video)
        db.session.commit()
        return send_file(file, download_name=video_name, as_attachment=True, attachment_filename=video_name, mimetype="video/mp4")
    elif file and is_ta is None:
        video.flag = 2
        db.session.add(video)
        db.session.commit()
        return send_file(file, download_name=video_name, as_attachment=True, attachment_filename=video_name, mimetype="video/mp4")
    else:
        return '', 404

@api.route('video/<lab>', methods=['GET'])
def get_studentVideoList(lab):

    room_id = str(Room.query.filter_by(room_name=lab).first().id)

    video_path = os.path.join(videos_path, lab)

    file_list = os.listdir(video_path)

    print('file_list: ')
    print(file_list)

    if len(file_list) >= 1:
        return {'file_list': file_list}, 200
    else:
        return '', 404

# @api.route('video/<lab>/<id>', methods=['GET'])  # 문제 file list 반납
# def get_studentsVideo(lab, id):

#     code_path = os.path.join(videos_path, lab, id, '')

#     dir_list = os.listdir(code_path)

#     email_list = []

#     for i in range(len(dir_list)):
#         email = User.query.filter_by(id=int(dir_list[i])).first().email
#         email_list.append(email)

#     if len(dir_list) >= 1:
#         return {'dir_list': dir_list, 'email_list': email_list}, 200
#     else:
#         return '', 404

ALLOWED_EXTENSIONS = set(
    ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'c', 'md', 'h'])

STUDENT_ALLOWED_EXTENSIONS = set(['c', 'h'])


def allowed_file(filename):
    return ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS) or 'Makefile'
def student_allowed_file(filename):
    return ('.' in filename and filename.rsplit('.', 1)[1].lower() in STUDENT_ALLOWED_EXTENSIONS)


# 교수 문제 제출
@api.route('problems/<labname>/<problem_title>', methods=['POST'])
@prof_required_vs
def upload_problem(labname, problem_title):
    problem_path = os.path.join(problems_path, labname, problem_title)
    grading_problem_path = os.path.join(grading_path, labname, problem_title)
    data = request.get_json()

    room = Room.query.filter_by(room_name=labname).first().id
    
    filenames = data['files']['filename'] # file명
    filedatas = data['files']['file'] # file 데이터
    
    for idx, filename in enumerate(filenames):
        filenames[idx] = secure_filename(filename)

    if not os.path.isdir(os.path.join(problems_path, labname)):
        resp.status_code = 404
        return resp
    
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
        if Problem.query.filter_by(title=problem_title, room_id=room).first() is not None:
            db.session.delete(Problem.query.filter_by(title=problem_title, room_id=room).first())
            db.session.commit()

        problem = Problem(title=problem_title, room_id=room)
        db.session.add(problem)
        db.session.commit()
        
        problem_id = Problem.query.filter_by(title=problem_title, room_id=room).first().id
        code = Code(problem_id = problem_id, user_id=g.current_user.id)
        db.session.add(code)
        db.session.commit()
        # users = User.query.all()
        # for user in users:
        #     code = Code(problem_id=problem_id, user_id=user.id)
        #     db.session.add(code)
        # db.session.commit()
        
        resp = jsonify({'message': 'Problem successfully uploaded'})
        resp.status_code = 201
    else:
        resp = jsonify(
            {'message': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif, c, md'})
        resp.status_code = 400
    return resp

ALLOWED_PDF_EXTENSIONS = ['pdf']
def allowed_pdf(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXTENSIONS


## pdf 올리기
@api.route('problems/<labname>/<problem_title>/pdf', methods=['POST'])
@prof_required_vs
def upload_pdf(labname, problem_title):
    user_id = str(g.current_user.id)

    problem_path = os.path.join(problems_path, labname, problem_title)
    # student_path = os.path.join(problem_path, labname, user_id)
    
    if 'file' not in request.files:
        resp = jsonify({'message': 'Not video file'})
        resp.status_code = 404
        return resp
        
    if not os.path.isdir(problem_path):
        os.mkdir(problem_path)
        os.chmod(problem_path, 0o777)        
    # if not os.path.isdir(student_path):
    #     os.mkdir(student_path)
    #     os.chmod(student_path, 0o777)
    
    file = request.files['file']
    
    if file.filename == '':
        resp = jsonify({'message': 'Not video filename'})
        resp.status_code = 404
        return resp       
    
    if file and allowed_pdf(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(problem_path, filename))
                         
    resp = jsonify({'message': 'Success upload Pdf'})
    resp.status_code = 200
    return resp
    


# 교수 문제 삭제
@api.route('problems/<lab>/<problem_title>', methods=['DELETE'])
@prof_required_vs
def delete_problem(lab, problem_title):
    print('delete problem')
    problem_path = os.path.join(problems_path, lab, problem_title)
    grading_problem_path = os.path.join(grading_path, lab, problem_title)

    problem_code_path = os.path.join(codes_path, lab, problem_title)
    print(problem_code_path)
    
    room_id = Room.query.filter_by(room_name=lab).first().id
    # db 문제 삭제, problem
    problem = Problem.query.filter_by(title=problem_title, room_id=room_id).first()
    # print(problem.code) ## 이걸 해야지 삭제가 된다.... 중요!!!
    if problem:
        db.session.delete(problem)
        db.session.commit()

    if os.path.isdir(problem_code_path):
        shutil.rmtree(problem_code_path)
        codes = Code.query.filter_by(problem_id=problem.id).all()
        for code in codes:
            db.session.delete(code)
        db.session.commit()

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

    problem_id = Problem.query.filter_by(title=problem_title).first().id

    code = Code.query.filter_by(problem_id=problem_id, user_id=g.current_user.id).first()

    if os.path.isdir(student_code_path):
        shutil.rmtree(student_code_path)

    if code:
        db.session.delete(code)
        db.session.commit()
        
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
@api.route('student_codes/<lab>/<problem_title>', methods=['POST'])
def upload_code(lab, problem_title):
    data = request.get_json()
    filenames = data['files']['filename'] # file명
    filedatas = data['files']['file'] # file 데이터
    user_id = str(g.current_user.id)
    username = g.current_user.username
    executable_file = None

    room_id = Room.query.filter_by(room_name=lab).first().id
    
    # /home/codelab/ver1/app/api/codes/<lab>/<problem_title>
    problem_path = os.path.join(codes_path, lab, problem_title)
    # /home/codelab/ver1/app/api/codes/<lab>/<problem_title>/<username>
    student_code_path = os.path.join(problem_path, user_id)
    grading_src_path = os.path.join(path, "grading", lab, problem_title, "src")

    problem_id = Problem.query.filter_by(title=problem_title).first().id

    code = Code.query.filter_by(problem_id=problem_id, user_id=g.current_user.id).first()
    if code is None:
        code = Code(problem_id=problem_id, user_id=g.current_user.id)
        db.session.add(code)
        db.session.commit()

    problem_first_path = os.path.join(codes_path, lab)
    student_first_code_path = os.path.join(problem_first_path, lab)

    if not os.path.isdir(problem_first_path):
        os.mkdir(problem_first_path)
        os.chmod(problem_first_path, 0o777)

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
        print(grading_src_path, executable_file) ## /home/codelab/ver1/app/api/grading/DS/Bracket/src  bracket_1
        subprocess.call("make -C " + grading_src_path, shell=True) # 학생 코드 makefile 실행
        os.rename(os.path.join(grading_src_path, problem_title.lower()), os.path.join(grading_src_path, problem_title.lower()) + '_' + user_id)
        subprocess.call(filepath + "compile.sh " +
                        executable_file + " " + user_id + " " + problem_title + " " + lab, shell=True)
    
    out = os.system("diff -bZ {} {}".format(os.path.join(grading_path, lab, problem_title, "results", "result_" + user_id + ".txt"), os.path.join(grading_path, lab, problem_title, "cases", "programs", "output.txt")))
    
    message = None
    if out != 0:
        print("Wrong Answer\n")
        message = "Wrong Answer"
        body = g.current_user.email + '<br>' + problem_title + '<br>'  + message
        # comment_chat = Comment(username='Chat Bot', body=body)
        # db.session.add(comment_chat)
        # db.session.commit()
        code = Code.query.filter_by(problem_id=problem_id, user_id=g.current_user.id).first()
        code.pf = False
    else:
        print("맞았습니다\n")
        message = "Correct Answer"
        body = g.current_user.email + '<br>' + problem_title + '<br>' + message
        # comment_chat = Comment(username='Chat Bot', body=body)
        # db.session.add(comment_chat)
        # db.session.commit()
        code = Code.query.filter_by(problem_id=problem_id, user_id=g.current_user.id).first()
        code.pf = True
    db.session.commit()
    
    resp = jsonify({'message': message})
    resp.status_code = 200
    return resp


# 문제 리스트 가져오기
@api.route('info', methods=['GET'])
def problem_list():
    # return '',200 # 임시
    labs = []
    roles = []

    ## Regist에서 유저아이디가 current_user.id인거 다 가져와
    ## 그 중에서 룸 아이디 다 가져와
    ## 가져온 룸 아이디와 매칭된 룸 네임 다 가져와 -> lab이라는 리스트에 저장

    isRegist_all = Regist.query.filter_by(user_id=g.current_user.id).all()
    for i, room in enumerate(isRegist_all):
        room_name = Room.query.filter_by(id=room.room_id).first().room_name
        labs.append({"lab": room_name, "problems": [], "members": [], "videos": []})
        ## lab => DS
        # labs_lab.append(room_name)
        ## problem에서 룸 네임이 room_name인거 다 가져와 (일단 그냥 등록하자)
        problem_in_lab = Problem.query.filter_by(room_id=room.room_id).all()
        for j, problem in enumerate(problem_in_lab):
            ## title => Bracket
            labs[i]["problems"].append({"title":problem.title})

            code = Code.query.filter_by(problem_id=problem.id, user_id=g.current_user.id).first()
            if code is not None:
                if code.pf == True:
                    ## evaluation => correct
                    labs[i]["problems"][j]["evaluation"] = "correct"
                else:
                    labs[i]["problems"][j]["evaluation"] = "wrong"
            else:
                labs[i]["problems"][j]["evaluation"] = "not yet"

            ## 제출한놈들 가져오기
            code_all = Code.query.filter_by(problem_id=problem.id).all()
            # regist_all = Regist.query.filter_by(room_id=room.room_id).all()
            labs[i]["problems"][j]["submission"] = []
            for k, code_name in enumerate(code_all):
                user_name = User.query.filter_by(id=code_name.user_id).first().username
                print(user_name)
                labs[i]["problems"][j]["submission"].append({"name": user_name})
                code_submission = Code.query.filter_by(problem_id=problem.id, user_id=User.query.filter_by(id=code_name.user_id).first().id).first()
                if code_submission is not None:
                    if code_submission.pf == True:
                        labs[i]["problems"][j]["submission"][k]['evaluation'] = "correct"
                    elif code_submission.pf == False:
                        labs[i]["problems"][j]["submission"][k]['evaluation'] = "wrong"
                else:
                    labs[i]["problems"][j]["submission"][k]['evaluation'] = "not yet"

        ## member
        ## 이 방에 속한 아이들 전부 가져와야함
        ## 내가 들어있는 지금 이 방
        isRegist_all_members = Regist.query.filter_by(room_id=room.room_id).all()
        # isMember = []
        # isMember.append(Regist.query.filter_by(room_id=isRegist_all_members.room_id).first())
        for j, member in enumerate(isRegist_all_members):
            user_name = User.query.filter_by(id=member.user_id).first().username
            labs[i]["members"].append({"name": user_name})
            if User.query.filter_by(id=member.user_id).first().role_id == 3:
                labs[i]["members"][j]["role"] = "Professor"
            elif TA.query.filter_by(room_id=member.room_id, user_id=member.user_id).first():
                labs[i]["members"][j]["role"] = "TA"
            else:
                labs[i]["members"][j]["role"] = "Student"

        ## 비디오 목록 가져오기 (현재 내가 등록된 방에서)
        videos = Video.query.filter_by(room_id=room.room_id).all()
        ## 현재 내가 ta로 등록된 방
        tas = TA.query.filter_by(room_id=room.room_id, user_id=g.current_user.id).first()

        for j, video in enumerate(videos):
            if tas is not None:
                if video is not None and video.room_id == tas.room_id: 
                    ## 비디오가 현재 ta로 등록된 방에 있으면 다 가져와
                    print(video.video_name)
                    labs[i]["videos"].append({"name": video.video_name})
                    if video.flag == 0:
                        labs[i]["videos"][j]["status"] = "Waiting"
                    elif video.flag == 1:
                        labs[i]["videos"][j]["status"] = "Processing"
                    elif video.flag == 2:
                        labs[i]["videos"][j]["status"] = "Done"
            else:
                if video is not None and (video.user_id == g.current_user.id or video.target_id == g.current_user.id):
                    ## 내가 ta로 등록은 안되있는데 그 비디오 주인이 나거나 그 비디오 target_id가 나면 다 가져와
                    labs[i]["videos"].append({"name": video.video_name})
                    if video.flag == 0:
                        labs[i]["videos"][j]["status"] = "Waiting"
                    elif video.flag == 1:
                        labs[i]["videos"][j]["status"] = "Processing"
                    elif video.flag == 2:
                        labs[i]["videos"][j]["status"] = "Done"

    regists = Regist.query.filter_by(user_id=g.current_user.id).all()
    for regist in regists:
        room_id = regist.room_id
        if TA.query.filter_by(user_id=g.current_user.id, room_id=room_id).first():
            roles.append('admin')
        else:
            roles.append('student')
    
    return jsonify({"labs": labs, "roles": roles}), 200
    

    # codes = Code.query.filter_by(user_id=g.current_user.id).all()

    # all_list = []
    # unresolved_list = []
    # resolved_list = []
    # print(g.current_user.id)
    # for code in codes:
    #     title = Problem.query.filter_by(id=code.problem_id).first().title
    #     question = Problem.query.filter_by(id=code.problem_id).first()

    #     if g.current_user.role.name == 'Administrator' or g.current_user.role.name == 'Prof':
    #         all_list.append(title)
    #     elif question.permission == True:
    #         all_list.append(title)

    #     if code.pf == False and question.permission == True:
    #         unresolved_list.append(title)
    #     elif code.pf == True and question.permission == True:
    #         resolved_list.append(title)

    # return jsonify({"All_Problems": all_list, "Solved_Problems": unresolved_list, "Resolved_Problems": resolved_list}), 200



ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'zip']
def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

# video 업로드 학생
@api.route('video/<lab>', methods=['POST'])
def upload_video(lab):
    user_id = str(g.current_user.id)

    problem_video_path = os.path.join(videos_path, lab)
    # student_video_path = os.path.join(problem_video_path, user_id)

    room_id = Room.query.filter_by(room_name=lab).first().id
    
    if 'file' not in request.files:
        resp = jsonify({'message': 'Not video file'})
        resp.status_code = 404
        return resp

    if not os.path.isdir(problem_video_path):
        os.mkdir(problem_video_path)
        os.chmod(problem_video_path, 0o777)        
    # if not os.path.isdir(student_video_path):
    #     os.mkdir(student_video_path)
    #     os.chmod(student_video_path, 0o777)
    
    file = request.files['file']
    
    if file.filename == '':
        resp = jsonify({'message': 'Not video filename'})
        resp.status_code = 404
        return resp       
    
    if file and allowed_video_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(problem_video_path, filename))
        video = Video(user_id=g.current_user.id, video_name=filename, room_id=room_id, flag = 0)
        db.session.add(video)
        db.session.commit()
                         
    resp = jsonify({'message': 'Success upload video'})
    resp.status_code = 200
    return resp

# video 업로드 TA
@api.route('video/<lab>/<video_name>', methods=['POST'])
def upload_video_ta(lab, video_name):
    # user_id = str(User.query.filter_by(username=username).first().id)

    video_id = str(Video.query.filter_by(video_name=video_name).first().id)

    video_student = Video.query.filter_by(video_name=video_name).first()

    problem_video_path = os.path.join(videos_path, lab)
    # student_video_path = os.path.join(problem_video_path, user_id)

    room_id = Room.query.filter_by(room_name=lab).first().id
    user_id = str(User.query.filter_by(id=video_student.user_id).first().id)
    
    if 'file' not in request.files:
        resp = jsonify({'message': 'Not video file'})
        resp.status_code = 404
        return resp

    if not os.path.isdir(problem_video_path):
        os.mkdir(problem_video_path)
        os.chmod(problem_video_path, 0o777)        
    # if not os.path.isdir(student_video_path):
    #     os.mkdir(student_video_path)
    #     os.chmod(student_video_path, 0o777)
    
    file = request.files['file']
    
    if file.filename == '':
        resp = jsonify({'message': 'Not video filename'})
        resp.status_code = 404
        return resp       
    
    if file and allowed_video_file(file.filename):
        filename = secure_filename(file.filename)
        print(filename)
        file.save(os.path.join(problem_video_path, filename))
        video = Video(user_id=g.current_user.id, video_name=filename, room_id=room_id, target_id=user_id, flag=0)
        db.session.add(video)
        db.session.commit()
    
    video_student = Video.query.filter_by(video_name=video_name, room_id=room_id).first()
    video_student.flag = 2
    db.session.commit()

    # video_student = Video.query.filter_by()
                         
    resp = jsonify({'message': 'Success upload video'})
    resp.status_code = 200
    return resp

# video delete
@api.route('video/<lab>/<video_name>', methods=['DELETE'])
def delete_video(lab, video_name):

    user_id = str(User.query.filter_by(id=g.current_user.id).first().id)

    user_id_int = User.query.filter_by(id=g.current_user.id).first().id

    problem_video_path = os.path.join(videos_path, lab)
    student_video_path = os.path.join(problem_video_path, video_name)

    room_id = Room.query.filter_by(room_name=lab).first().id

    video = Video.query.filter_by(room_id=room_id, video_name=video_name).first()

    is_ta = TA.query.filter_by(user_id=g.current_user.id, room_id=room_id).first()

  
    if os.path.isfile(student_video_path) and (video.user_id == g.current_user.id or is_ta.user_id is not None):
        os.remove(student_video_path)

    if video.user_id == g.current_user.id or is_ta.user_id is not None:
        db.session.delete(video)
        db.session.commit()
                         
    resp = jsonify({'message': 'Success delete video'})
    resp.status_code = 200
    return resp

    

#학생 코드 받는거
@api.route('student_codes/<lab>/<id>/<student_id>/<filename>', methods=['GET'])
@prof_required_vs
def get_student_code(lab, id, student_id, filename):

    print(lab)
    print(id)
    print(student_id)
    print(filename)

    code_path = os.path.join(codes_path, lab, id, student_id)

    file = os.path.join(code_path, secure_filename(filename))

    if file:
        return send_file(file, download_name=filename, as_attachment=True, attachment_filename=filename)
    else:
        return '', 404


@api.route('student_codes/<lab>/<id>', methods=['GET'])  
def get_student_all(lab, id):
    code_path = os.path.join(codes_path, lab, id, '')

    dir_list = os.listdir(code_path)

    print(dir_list)

    email_list = []

    for i in range(len(dir_list)):
        email = User.query.filter_by(id=int(dir_list[i])).first().username
        email_list.append(email)

    if len(dir_list) >= 1:
        return {'dir_list': dir_list, 'email_list': email_list}, 200
    else:
        return '', 404

@api.route('student_codes/<lab>/<id>/<student_id>', methods=['GET'])  # 문제 file list 반납
def get_student_filelist(lab, id, student_id):
    code_path = os.path.join(codes_path, lab, id, student_id)

    file_list = os.listdir(code_path)

    if len(file_list) >= 1:
        return {'file_list': file_list}, 200
    else:
        return '', 404

# log 초기화
@api.route('logs/<lab>', methods=['DELETE'])
@prof_required_vs
def initialize_logs(lab):
    room_id = Room.query.filter_by(room_name=lab).first().id
    
    logs = Log.query.filter_by(room_id=room_id).all()

    for log in logs:
        db.session.delete(log)
    db.session.commit()

    resp = jsonify({'message': "success"})
    resp.status_code = 200
    return resp


# log 보내기
@api.route('logs/<lab>', methods=['POST'])
def post_logs(lab):
    student_id = str(g.current_user.id)
    data = request.get_json()
    flag = True if data['flag'] == 1 else False
    room = Room.query.filter_by(room_name=lab).first()
    code = data['code']
    length = data['length'] // 2
    username = User.query.filter_by(id=student_id).first().username
                
    log = Log(user_id=student_id, code=code, flag=flag, length=length, username=username, room_id=room.id)
    db.session.add(log)
    db.session.commit()
    print('-----------------------------------------------')
    print(log.length)
    print('-----------------------------------------------')
        
    resp = jsonify({'message': "success"})
    resp.status_code = 200
    return resp
    

# log 받기  
@api.route('logs/<lab>', methods=['GET'])
@prof_required_vs
def get_logs(lab):
    users = Log.query.group_by(Log.user_id).all()
    user_list = []
    log = []
    for user in users:
        user_list.append(user.user_id)
    
## 랩 이름 받아서 등록
@api.route('labs', methods=['POST'])
@prof_required_vs
def makeLab():
    user_id = User.query.filter_by(id=g.current_user.id).first().id
    data = request.get_json()
    labName = data['labName']
    if Room.query.filter_by(room_name=labName).first():
        return 'The same name lab is exist', 404

    lab_name = Room(room_name=labName, host_id=user_id)
    db.session.add(lab_name)
    db.session.commit()
    ## 룸 등록

    room_id = Room.query.filter_by(room_name=labName).first().id
    host_id = User.query.filter_by(id=g.current_user.id).first().id

    ta = TA(user_id=g.current_user.id, room_id=room_id)

    regist_room = Regist(room_id=room_id, user_id=host_id)
    db.session.add(regist_room)
    db.session.add(ta)
    db.session.commit()

    user = User.query.filter_by(id=g.current_user.id).first()

    log_init = Log(user_id=g.current_user.id, username=user.username, code='Init Log', length=0, total_length=0, room_id=room_id)

    problem_path = os.path.join(problems_path, labName)
    if not os.path.isdir(problem_path):
        os.mkdir(problem_path)
        os.chmod(problem_path, 0o777)
    
    grading_problem_path = os.path.join(grading_path, labName)
    if not os.path.isdir(grading_problem_path):
        os.mkdir(grading_problem_path)
        os.chmod(grading_problem_path, 0o777)
    

    resp = jsonify({'lab_name': labName})
    resp.status_code = 200
    return resp
    
## 등록된 랩 이름 보내주기, 전부 보내주면 될듯
@api.route('labs', methods=['GET'])
def postLab():

    user_id = g.current_user.id

    ## room id 전부
    room_ids = [regists.room_id for regists in  Regist.query.filter_by(user_id=user_id).all()]

    ## room_id 로 찾아야함
    labName = [Room.query.filter_by(id=room_id).first().room_name for room_id in room_ids]
        
    resp = jsonify({'lab_name': labName})
    resp.status_code = 200
    return resp

## 지울 랩이름 받기
@api.route('labs/delete', methods=['POST'])
@prof_required_vs
def get_deleteLab():

    user_id = User.query.filter_by(id=g.current_user.id).first().id
    data = request.get_json()
    labName = data['deleteLab']

    problem_path = os.path.join(problems_path, labName)
    grading_problem_path = os.path.join(grading_path, labName)

    video_path = os.path.join(videos_path, labName)
    code_path = os.path.join(codes_path, labName)
    
    room = Room.query.filter_by(room_name=labName).first()
    regists = Regist.query.filter_by(room_id=room.id).all()
    tas = TA.query.filter_by(room_id=room.id).all()
    problems = Problem.query.filter_by(room_id=room.id).all()

    comments = Comment.query.filter_by(room_id=room.id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.commit()

    if os.path.isdir(video_path):
        shutil.rmtree(video_path)
    
    if os.path.isdir(code_path):
        shutil.rmtree(code_path)

    # db 문제 삭제, problem
    if room:
        db.session.delete(room)
        for regist in regists:
            db.session.delete(regist)
        for ta in tas:
            db.session.delete(ta)
        for problem in problems:
            db.session.delete(problem)
            problem_code_path = os.path.join(codes_path, labName)
            if os.path.isdir(problem_code_path):
                shutil.rmtree(problem_path)
            codes = Code.query.filter_by(problem_id=problem.id).all()
            for code in codes:
                db.session.delete(code)
        db.session.commit()

    if os.path.isdir(problem_path):
        shutil.rmtree(problem_path)
        
        if os.path.isdir(grading_problem_path):
            shutil.rmtree(grading_problem_path)
        
        resp = jsonify({'message': 'Problem successfully delete'})
        resp.status_code = 200
        return resp
    else:
        resp = jsonify({'message': 'Not exist problem ID'})
        resp.status_code = 200
        return resp

## 학생 이메일 받아서 랩에 초대
@api.route('invite', methods=['POST'])
def inviteStudent():
    data = request.get_json()
    email = data['email']
    lab = data['lab']

    addStudent = User.query.filter_by(email=email).first().id
    addRoom = Room.query.filter_by(room_name=lab).first().id
    student = User.query.filter_by(email=email).first()

    ## Regist에 추가
    addStudent2Lab = Regist(room_id=addRoom, user_id=addStudent)
    db.session.add(addStudent2Lab)
    db.session.commit()

    addStudent2Log = Log(user_id=addStudent, username=student.username, code='', length=0, total_length=0, room_id=addRoom)
    db.session.add(addStudent2Log)
    db.session.commit()

    resp = jsonify({'Success': 'Success'})
    resp.status_code = 200
    return resp

## 학생 이메일 받아서 TA권한 주기 (랩에도 바로 추가)
@api.route('inviteTA', methods=['POST'])
def inviteTA():
    data = request.get_json()
    email = data['email']
    lab = data['lab']

    addStudent = User.query.filter_by(email=email).first().id
    addRoom = Room.query.filter_by(room_name=lab).first().id

    ## Regist에 추가
    if Regist.query.filter_by(room_id=addRoom, user_id=addStudent).first() is None:
        addStudent2Lab = Regist(room_id=addRoom, user_id=addStudent)
        db.session.add(addStudent2Lab)
        db.session.commit()

    addTA = TA(user_id=addStudent, room_id=addRoom)
    db.session.add(addTA)
    db.session.commit()

    resp = jsonify({'Success': 'Success'})
    resp.status_code = 200
    return resp

## 학생 이메일 받아서 랩에서 지우기
@api.route('deleteStudentFromLab', methods=['POST'])
def deleteStudentFromLab():
    data = request.get_json()
    username = data['username']
    lab = data['lab']

    ## 지울 학생 아이디
    deleteStudent = User.query.filter_by(username=username).first().id
    ## 지울 랩 아이디
    deleteRoom = Room.query.filter_by(room_name=lab).first().id
    ## 지울 학생 쿼리
    student = User.query.filter_by(username=username).first()

    ## Regist에 있는 거 지움
    ## 지울 학생의 regist (룸 아이디는 지울 랩 아이디, 유저 아이디는 지울 학생 아이디 => 지울 학생이 해당룸에 속해있다.)
    if Room.query.filter_by(room_name=deleteRoom, host_id=g.current_user.id).first():
        return 'He is Professor'

    if Regist.query.filter_by(room_id=deleteRoom, user_id=deleteStudent).first():
        deleteStudent2Lab = Regist.query.filter_by(room_id=deleteRoom, user_id=deleteStudent).first()
        db.session.delete(deleteStudent2Lab)
        db.session.commit()

    ## 해당 학생이 TA라면
    if TA.query.filter_by(user_id=deleteStudent, room_id=deleteRoom).first():
        deleteTA = TA.query.filter_by(user_id=deleteStudent, room_id=deleteRoom).first()
        db.session.delete(deleteTA)
        db.session.commit()

    deleteStudent2Log = Log.query.filter_by(user_id=deleteStudent, username=student.username, room_id=deleteRoom).first()
    if deleteStudent2Log is not None:
        db.session.delete(deleteStudent2Log)
        db.session.commit()

    resp = jsonify({'Success': 'Success'})
    resp.status_code = 200
    return resp

