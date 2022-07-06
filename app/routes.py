from re import error
from flask_migrate import current
from app import app, db, login
from flask_login import current_user, login_user, logout_user
from app.models import InstiAdmin, Recruiter, Student, Alumni, User, Message, Feedback, Notice, ToBeRead, Application, Profile
from flask import jsonify, request
import time
import datetime


# Utility Functions
def genuine_id(Id):
    # gen_code = '#<COMPANY_CODE>@<YEAR>'
    parts = Id.split('@')
    if (int(parts[1]) <= 2021) and (int(parts[1]) >= 1600):
        if len(parts[0][1:]) == 3:
            return True

    return False


# ------ API STARTS HERE ------
@app.route('/')
@app.route('/home')
def home():
    hello = "Welcome to the API"
    return hello


@app.route('/getuserdetails')
def getdetails():
    try:
        auth_token = request.json
        userid = User.decode_auth_token(auth_token)
        user = User.query.get(userid)

        if user is not None:
            response_obj = dict()
            response_obj = {
                'name': user.username,
                'email': user.email,
                'usertype': user.type,
                'status': 'success'
            }

        else:
            response_obj = None

        return jsonify(response_obj), 200

    except:

        response_obj = {
            'status': 'fail',
            'message': 'Unable to access user details'
        }

        return jsonify(response_obj), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        #get the data from the frontend
        user_data = request.json
        headers = request.headers.get('Authorization')

        #check if user is already logged in
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''

        # return jsonify(auth_token), 404
        if auth_token:
            response = {'status': 'invalid', 'message': 'User already logged in'}
            return jsonify(response), 404

        user = User.query.filter_by(username=user_data.get('username')).first()

        if user is None:
            response = {'status': 'invalid', 'message': 'User does not exist'}
            return jsonify(response), 404

        if user.check_password(user_data.get('password')):
            # login_user(user, remember=True)
            token = user.encode_auth_token(user.id)
            response = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'auth_token': token.decode(),
                'user_type': user.type
            }
            return jsonify(response), 200

        else:
            response = {'status': 'fail', 'message': 'Incorrect password entered'}
            return jsonify(response), 403

    except:
        response = {
            'status': 'fail',
            'message': 'Please try again',
        }
        return jsonify(response), 500


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''
    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        present_user = User.query.get(curr_userid)
        logout_user()
        response = {
            'status': 'success',
            'message': 'Succesfully logged out of the account'
        }
        return jsonify(response), 200
    else:
        response = {'status': 'invalid', 'message': 'User not logged in'}
        return jsonify(response), 401


@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        user_data = request.json
        response = dict()

        # check if the user is already logged in
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if auth_token:
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)
            response = {'status': 'invalid', 'message': 'User already logged in'}
            return jsonify(response), 403

        # check if any credentials match to that of existing users
        user = User.query.filter_by(username=user_data.get('username')).first()
        if user is not None:
            response = {
                'status': 'invalid',
                'message': 'Username has already been taken.'
            }
            return jsonify(response), 404

        user = User.query.filter_by(username=user_data.get('email')).first()
        if user is not None:
            response = {
                'status': 'invalid',
                'message': 'Email has already been registered.'
            }
            return jsonify(response), 404

        # check for the correct user type
        if user_data.get('usertype') == "student" or user_data.get(
                'usertype') == "alumni":
            response = {'status': 'success', 'message': 'User has been registered'}
            # add the user to the database
            if user_data.get('usertype') == "student":
                user = Student(
                    username=user_data['username'],
                    email=user_data['email'],
                    # roll_num=user_data['roll_num'],
                    # degree=user_data['degree'],
                    # dept=user_data['dept']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                db.session.commit()

            if user_data.get('usertype') == "alumni":
                user = Alumni(
                    username=user_data['username'],
                    email=user_data['email'],
                    #   degree=user_data['degree'],
                    #   dept=user_data['dept'],
                    #   year=user_data['year']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                db.session.commit()
            return jsonify(response), 200

        # if User is a recruiter, check for his/her genuine Id
        elif user_data.get('usertype') == "recruiter":
            if genuine_id(user_data.get('gen_id')):
                response = {
                    'status': 'success',
                    'message': 'User has been registered'
                }

                # add the user to the database
                user = Recruiter(username=user_data['username'],
                                email=user_data['email'],
                                gen_id=user_data['gen_id'])
                user.set_password(user_data['password'])
                db.session.add(user)
                db.session.commit()

                return jsonify(response), 200

            else:
                response = {
                    'status': 'invalid',
                    'message': 'Unverified recruiter Id'
                }
                return jsonify(response), 404

        else:
            response = {
                "asdas": user_data,
                "recieved": user_data.get('usertype'),
                "status": "invalid",
                "message": "Given Usertype is not valid"
            }
            return jsonify(response), 404

    except:
        response = dict()
        response = {
            "status": "fail",
            "message": "Registration not allowed, try again later"
        }
        return jsonify(response), 404


@app.route('/getdata', methods=['POST'])
def getdata():
    # try:
    fin_dict = dict()
    rec_data = request.json
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''
    
    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        present_user = User.query.get(curr_userid)
        
        # ----- Messages -----
        fin_dict['messages'] = []

        # recieved messages
        if rec_data['timestamp'] == 0:
            #extract all the messages
            messages = Message.query.all()

            # traverse through all messages of the current user and set the read status
            for msg in messages:
                if msg.recipient_id == curr_userid:
                    status = ToBeRead.query.filter_by(user_id=curr_userid,
                                                      entity_id=msg.id,
                                                      type="message").first()
                    setattr(msg, 'pending', status is not None)
                    if status is not None:
                        fin_dict['messages'].append({
                            'id':
                            msg.id,
                            'author':
                            msg.author.username,
                            'recipient':
                            msg.recipient.username,
                            'content':
                            msg.content,
                            'time':
                            msg.date_time,
                            'updateTime':
                            status.timestamp,
                            'read':
                            not msg.pending,
                        })
                    else:
                        fin_dict['messages'].append({
                            'id':
                            msg.id,
                            'author':
                            msg.author.username,
                            'recipient':
                            msg.recipient.username,
                            'content':
                            msg.content,
                            'time':
                            msg.date_time,
                            'updateTime':
                            msg.date_time,
                            'read':
                            not msg.pending,
                        })

                elif msg.author_id == curr_userid:
                    setattr(msg, 'pending', False)
                    fin_dict['messages'].append({
                        'id': msg.id,
                        'author': msg.author.username,
                        'recipient': msg.recipient.username,
                        'content': msg.content,
                        'time': msg.date_time,
                        'updateTime': msg.date_time,
                        'read': True,
                    })

        else:
            # extract the messages in the toberead table
            messages = ToBeRead.query.filter_by(type="message")

            for msg in messages:
                if msg.date_time > rec_data[
                        'timestamp'] and msg.reciever_id == curr_userid:
                    setattr(msg, 'pending', True)
                    fin_dict['messages'].append({
                        'id': msg.id,
                        'author': msg.author.username,
                        'recipient': msg.recipient.username,
                        'content': msg.content,
                        'time': msg.date_time,
                        'updateTime': msg.date_time,
                        'read': True,
                    })

        # ----- Notices -----
        #only for InstiAdmin, Student, Alumni
        fin_dict['notices'] = []
        if isinstance(present_user, Student) or isinstance(
                present_user, Alumni) or isinstance(present_user, InstiAdmin):
            if rec_data['timestamp'] == 0:
                notices = Notice.query.all()
                for tmp in notices:
                    status = ToBeRead.query.filter_by(user_id=curr_userid,
                                                      entity_id=tmp.id,
                                                      type="notice").first()
                    setattr(tmp, 'pending', status is not None)
                    if status is not None:
                        fin_dict['notices'].append({
                            'id': tmp.id,
                            'author': tmp.author.username,
                            'subject': tmp.subject,
                            'content': tmp.content,
                            'time': tmp.date_time,
                            'update_time': status.timestamp,
                            'read': False,
                        })
                    else:
                        fin_dict['notices'].append({
                            'id': tmp.id,
                            'author': tmp.author.username,
                            'subject': tmp.subject,
                            'content': tmp.content,
                            'time': tmp.date_time,
                            'update_time': tmp.date_time,
                            'read': True,
                        })
            else:
                pending_notices = ToBeRead.query.filter_by(
                    user_id=curr_userid, type="notice").all()
                for pending_notice in pending_notices:
                    tmp = Notice.query.get(pending_notice)
                    if tmp.date_time > rec_data['timestamp']:
                        setattr(tmp, 'pending', True)
                        fin_dict['messages'].append({
                            'id': tmp.id,
                            'author': tmp.author.username,
                            'subject': tmp.subject,
                            'content': tmp.content,
                            'time': tmp.date_time,
                            'update_time': status.date_time,
                            'read': False,
                        })

    # ----- Positions -----
        fin_dict['positions'] = []
        if rec_data['timestamp'] == 0:
            if isinstance(present_user, Recruiter):
                # extract all applications
                for prof in present_user.profiles:
                    status = ToBeRead.query.filter_by(user_id=curr_userid,
                                                      type="position").first()
                    if (status is not None):
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': status.timestamp,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': False
                        })
                    else:
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': prof.createDate,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': True
                        })

            elif (isinstance(present_user, InstiAdmin)):
                profiles = Profile.query.all()

                for prof in profiles:
                    status = ToBeRead.query.filter_by(entity_id=prof.id,
                                                      type="position").first()
                    if (status is not None):
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': status.timestamp,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': False
                        })
                    else:
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': prof.createDate,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': True
                        })

            else:
                profiles = Profile.query.all()

                for prof in profiles:
                    if prof.releaseDate is not None:
                        status = ToBeRead.query.filter_by(
                            entity_id=prof.id, type="position").first()
                        if (status is not None):
                            fin_dict['positions'].append({
                                'id':
                                prof.id,
                                'position_title':
                                prof.profileName,
                                'company':
                                prof.companyName,
                                'CTC':
                                prof.ctc,
                                'create_time':
                                prof.createDate,
                                'release_time':
                                prof.releaseDate,
                                'update_time':
                                status.timestamp,
                                'deadline':
                                prof.deadline,
                                'description':
                                prof.description,
                                'degrees':
                                prof.degree,
                                'depts':
                                prof.dept,
                                'recruiter_id':
                                prof.recruiter_id,
                                'read':
                                False
                            })
                        else:
                            fin_dict['positions'].append({
                                'id':
                                prof.id,
                                'position_title':
                                prof.profileName,
                                'company':
                                prof.companyName,
                                'CTC':
                                prof.ctc,
                                'create_time':
                                prof.createDate,
                                'release_time':
                                prof.releaseDate,
                                'update_time':
                                prof.createDate,
                                'deadline':
                                prof.deadline,
                                'description':
                                prof.description,
                                'degrees':
                                prof.degree,
                                'depts':
                                prof.dept,
                                'recruiter_id':
                                prof.recruiter_id,
                                'read':
                                True
                            })

        else:
            if isinstance(present_user, Recruiter):
                # extract all applications
                profiles = ToBeRead.query.filter_by(user_id=curr_userid,
                                                    type="position")

                for prof_id in profiles:
                    prof = Profile.query.get(prof_id.entity_id)
                    if prof.releaseDate > rec_data['timestamp']:
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': prof_id.timestamp,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': False
                        })

            elif (isinstance(present_user, InstiAdmin)):
                profiles = ToBeRead.query.filter_by(type="profile")

                for prof_id in profiles:
                    prof = Profile.query.get(prof_id.entity_id)
                    if prof.releaseDate > rec_data['timestamp']:
                        setattr(prof, 'pending', True)
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': prof_id.timestamp,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': False
                        })
            else:
                profiles = ToBeRead.query.filter_by(type="profile")

                for prof_id in profiles:
                    prof = Profile.query.get(prof_id.entity_id)
                    if prof.releaseDate is not None and prof.releaseDate > rec_data[
                            'timestamp']:
                        setattr(prof, 'pending', True)
                        fin_dict['positions'].append({
                            'id': prof.id,
                            'position_title': prof.profileName,
                            'company': prof.companyName,
                            'CTC': prof.ctc,
                            'create_time': prof.createDate,
                            'release_time': prof.releaseDate,
                            'update_time': prof_id.timestamp,
                            'deadline': prof.deadline,
                            'description': prof.description,
                            'degrees': prof.degree,
                            'depts': prof.dept,
                            'recruiter_id': prof.recruiter_id,
                            'read': False
                        })

        # ----- Student applications -----
        fin_dict['applications'] = []
        if rec_data['timestamp'] == 0:
            if isinstance(present_user, Student):
                appl = Application.query.all()
                for x in appl:
                    if x.student_id == curr_userid:
                        status = ToBeRead.query.filter_by(
                            entity_id=x.id, type="application").first()
                        if status is not None:
                            fin_dict['applications'].append({
                                'id':
                                x.id,
                                'position_id':
                                x.profile_id,
                                'company':
                                x.profile.companyName,
                                'status':
                                x.status,
                                'dept':
                                x.student.dept,
                                'degree':
                                x.student.degree,
                                'cgpa':
                                x.student.cgpa,
                                'time':
                                x.date_time,
                                'update_time':
                                status.timestamp,
                                'read':
                                False
                            })
                        else:
                            fin_dict['applications'].append({
                                'id':
                                x.id,
                                'position_id':
                                x.profile_id,
                                'company':
                                x.profile.companyName,
                                'status':
                                x.status,
                                'dept':
                                x.student.dept,
                                'degree':
                                x.student.degree,
                                'cgpa':
                                x.student.cgpa,
                                'time':
                                x.date_time,
                                'update_time':
                                x.date_time,
                                'read':
                                False
                            })
        else:
            if isinstance(present_user, Student):
                appl = ToBeRead.query.filter_by(user_id=curr_userid,
                                                type="application").all()
                for applcn_id in appl:
                    x = Application.query.get(applcn_id)
                    if x.date_time > rec_data['timestamp']:
                        setattr(x, 'pending', True)
                        fin_dict['applications'].append({
                            'id': x.id,
                            'position_id': x.profile_id,
                            'company': x.profile.companyName,
                            'status': x.status,
                            'dept': x.student.dept,
                            'degree': x.student.degree,
                            'cgpa': x.student.cgpa,
                            'time': x.date_time,
                            'update_time': x.date_time,
                            'read': True
                        })

        # ----- Timestamp -----
        fin_dict['timestamp'] = time.time()

        fin_dict['status'] = "success"
        fin_dict['message'] = "Extracted the data successfully"

    return jsonify(fin_dict), 200

    # else:
    #     response = {"status": "invalid", "message": "User not logged in"}
    #     return jsonify(response), 404

    # except:
    #     response = {"status": "fail", "message": "Could not fetch data"}
    #     return jsonify(response), 404


@app.route('/readreceipt', methods=['GET', 'POST'])
def readreciept():
    # try:
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''

    if auth_token:
        # if True:
        curr_userid = User.decode_auth_token(auth_token)
        present_user = User.query.get(curr_userid)
        receipt_data = request.json

        del_data = ToBeRead.query.filter_by(
            user_id=curr_userid,
            type=receipt_data['type'],
            entity_id=receipt_data['entity_id']).first()

        if del_data is not None:
            del_data.entity_id = "readalready"
            db.session.commit()

        response = {
            "status": "Success",
            "message": "Captured the read receipt"
        }
        return jsonify(response), 200

    else:
        response = {"status": "Invalid", "message": "User not logged in"}
        return jsonify(response), 401

    # except:
    #     response = {
    #         "status": "Fail",
    #         "message": "Error in accessing the database"
    #     }
    # return jsonify(response), 404


@app.route('/releaseposition', methods=['GET', 'POST'])
def release_position():
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''

        if auth_token:
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)
            post_data = request.json
            if (present_user.type == "instiadmin"):
                p = Profile.query.get(post_data['position_id'])
                p.releaseDate = time.time()
                db.session.commit()

                for student in Student.query.all():
                    t = ToBeRead(user_id=User.query.filter_by(
                        username=student.username).first().id,
                                 type='position',
                                 entity_id=p.id,
                                 timestamp=time.time())
                    db.session.add(t)

                for alumni in Alumni.query.all():
                    t = ToBeRead(user_id=User.query.filter_by(
                        username=alumni.username).first().id,
                                 type='position',
                                 entity_id=p.id,
                                 timestamp=time.time())
                    db.session.add(t)

                db.session.commit()
                response = {
                    'status': 'success',
                    'message': 'message and toberead entries added',
                    'position': {
                        'id': p.id,
                        'position_title': p.profileName,
                        'company': p.companyName,
                        'CTC': p.ctc,
                        'create_time': p.createDate,
                        'release_time': p.releaseDate,
                        'update_time': p.createDate,
                        'deadline': p.deadline,
                        'description': p.description,
                        'degrees': p.degree,
                        'depts': p.dept,
                        'recruiter_id': p.recruiter_id,
                        'read': False
                    }
                }
                return jsonify(response), 200
            else:
                return jsonify({
                    'status': 'invalid',
                    'message': "user isn't logged in"
                }), 401
    except:
        response = {'status': 'fail', 'message': 'Try again'}
        return jsonify(response), 404


@app.route('/fetchusernames', methods=['POST'])
def fetchnames_name():
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''

        if auth_token:
            # curr_userid = current_user.id
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)

            response = dict()
            data = request.json
            if '_' in data['string']:
                search_string = "%" + data['string'].replace('_', '__') + "%"
            else:
                search_string = '%{0}%'.format(data['string'])

            searchedUser = User.query.filter(
                User.username.ilike(search_string))
            ls = []
            for users in searchedUser:
                ls.append(users.username)

            response['names'] = ls
            response['status'] = "success"
            response['message'] = "Matching users found successfully"

            return jsonify(response), 200

        else:
            response = {
                "status": "Invalid",
                "message": "User is not logged in"
            }
            return jsonify(response), 401

    except:
        response = {
            "status": "Fail",
            "message": "Error in fetching matching usernames"
        }
        return jsonify(response), 404


@app.route('/positiondetails', methods=['GET', 'POST'])
def get_position_details():
    # try:
    fin_data = dict()
    rec_data = request.json
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''

    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        current_user = User.query.get(curr_userid)
        fin_profile = Profile.query.get(rec_data['positionId'])
        # fin_data['Profile'] = fin_profile
        if isinstance(current_user, Recruiter):
            fin_data['applications'] = []
            applications = Application.query.all()
            for appl in applications:
                if appl.profile_id == rec_data['positionId']:
                    fin_data['applications'].append({
                        'id': appl.id,
                        'name': appl.student.username,
                        'cgpa': appl.student.cgpa,
                        'degree': appl.student.degree,
                        'dept': appl.student.dept,
                        'status': appl.status
                    })

        elif isinstance(current_user, Student) or isinstance(
                current_user, Alumni):
            fin_data['Feedback'] = []
            feedbacks = Feedback.query.all()
            for fd in feedbacks:
                if fd.profile == rec_data['positionId']:
                    fin_data['applications'].append({
                        'author_name': fd.author.username,
                        'time': fd.date_time,
                        'content': fd.content
                    })

        return jsonify(fin_data), 200

    #     else:
    #         response = {
    #             "status": "Invalid",
    #             "message": "User is not logged in"
    #         }
    #         return jsonify(response), 401

    # except:
    #     response = {
    #         "status": "Fail",
    #         "message": "Unable to fetch position details"
    #     }
    #     return jsonify(response), 404


# ----BHARATH----- #


@app.route('/getprofile', methods=['POST'])
def get_profile():
    try:
        get_data = request.json

        auth_header = request.headers.get('Authorization')

        if auth_header:
            auth_token = auth_header.split(" ")[1]

        else:
            auth_token = ''

        if auth_token:
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)

            user_data = Student.query.filter_by(username=get_data['username']).first()
            if user_data is not None:
                if present_user.type == 'student':
                    return jsonify({
                        'status':
                        'invalid',
                        'message':
                        "Students cannot view other Students' profiles"
                    }), 500
                else:
                    return jsonify({
                        'profile': {
                            'username': user_data.username,
                            'usertype':"Student",
                            'email': user_data.email,
                            'degree': user_data.degree,
                            'dept': user_data.dept,
                            'description': user_data.description,
                            'resume_link': user_data.resume_link,
                            'cgpa': user_data.cgpa,
                            'roll_num': user_data.roll_num,
                        }
                    }), 200
            user_data = Alumni.query.filter_by(username=get_data['username']).first()
            if user_data != None:
                if present_user.type == 'alumni':
                    return jsonify({
                        'status':
                        'invalid',
                        'message':
                        "Alumni cannot view other alumni's profile"
                    })
                else:
                    return jsonify({
                        'profile': {
                            'username': user_data.username,
                            'usertype':"Alumni",
                            'email': user_data.email,
                            'description': user_data.description,
                            'degree': user_data.degree,
                            'dept': user_data.dept,
                            'year': user_data.year,
                        }
                    }), 200
            else:
                response = {
                    'status': 'Invalid',
                    'message': 'invalid user_id or user_type'
                }
                return jsonify(response), 500
        else:
            return jsonify({
                'status': 'invalid',
                'message': "user isn't logged in"
            })
    except:
        response = {'status': 'fail', 'message': 'Try again'}
        return jsonify(response), 404


# CORRECT WRT FRONTEND ALSO
@app.route('/application', methods=['POST'])
def apply():
    # try:
    post_data = request.json

    auth_header = request.headers.get('Authorization')

    if auth_header:
        auth_token = auth_header.split(" ")[1]

    else:
        auth_token = ''

    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        present_user = User.query.get(curr_userid)

        if present_user.type != 'student':
            return jsonify({
                'status':
                'invalid',
                'message':
                'only a student can apply for a job profile'
            }), 500

        temp = Application.query.filter_by(
            student_id=present_user.id,
            profile_id=post_data['profile_id']).first()
        if temp is not None:
            return jsonify({
                'status':
                'fail',
                'message':
                'a student can apply to a profile only once'
            }), 404

        if (Profile.query.filter_by(
                id=post_data['profile_id']).first().deadline < time.time()):
            return jsonify({
                'status': 'invalid',
                'message': 'application deadline expired'
            }), 404

        a = Application(student_id=present_user.id,
                        profile_id=post_data['profile_id'],
                        content=post_data['resume_link'],
                        date_time=time.time(),
                        status=0)
        db.session.add(a)
        db.session.commit()

        # Adding the position to which the application has been sent as unread for the recruiter
        t = ToBeRead.query.filter_by(
            user_id=Profile.query.filter_by(
                id=post_data['profile_id']).first().company.id,
            type='position',
            entity_id=post_data['profile_id']).first()

        if (t is None):
            t = ToBeRead(user_id=Profile.query.filter_by(
                id=post_data['profile_id']).first().company.id,
                         type='position',
                         entity_id=post_data['profile_id'],
                         timestamp=time.time())
            db.session.add(t)
        else:
            t.timestamp = time.time()
        db.session.commit()

        response = {
            'status': 'success',
            'message': 'application and toberead entries added',
            'application_obj': {
                'id': a.id,
                'position_id': a.profile_id,
                'company': a.profile.company.username,
                'status': a.status,
                'dept': a.student.dept,
                'degree': a.student.degree,
                'cgpa': a.student.cgpa,
                'time': a.date_time,
                'update_time': a.date_time,
                'read': True,
            }
        }
        return jsonify(response), 200
    else:
        return jsonify({
            'status': 'invalid',
            'message': "user isn't logged in"
        })

    # except:
    #     response = {'status': 'fail', 'message': 'Try again'}
    #     return jsonify(response), 404


@app.route('/uploadresume', methods=['POST'])
def upload():
    try:
        post_data = request.json

        auth_header = request.headers.get('Authorization')

        if auth_header:
            auth_token = auth_header.split(" ")[1]

        else:
            auth_token = ''

        if auth_token:
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)

            if current_user.type != 'student':
                return jsonify({
                    'status': 'invalid',
                    'message': 'only a student can upload resume'
                }), 500

            s = Student.query.filter_by(id=curr_userid)
            s.resume_link = post_data['resume_link']
            db.session.commit()

            response = {'status': 'success', 'message': 'resume link uploaded'}
            return jsonify(response), 200
        else:
            return jsonify({
                'status': 'invalid',
                'message': "user isn't logged in"
            })
    except:
        response = {'status': 'fail', 'message': 'Try again'}
        return jsonify(response), 404


@app.route('/createmessage', methods=['POST'])
def create_message():
    try:
        post_data = request.json

        auth_header = request.headers.get('Authorization')

        if auth_header:
            auth_token = auth_header.split(" ")[1]

        else:
            auth_token = ''

        if auth_token:
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)

            reciever = User.query.filter_by(
                username=post_data['recipient_username']).first()

            if present_user.id == reciever.id:
                return jsonify({
                    'status': 'invalid',
                    'message': 'user cannot send message to himself'
                })

            if (present_user.type == 'instiadmin'):
                if (reciever.type == 'alumni'):
                    return jsonify({
                        'status':
                        'invalid',
                        'message':
                        'instiadmin cannot send messages to alumni'
                    })
            elif (present_user.type == 'recruiter'):
                if (reciever.type != 'instiadmin'):
                    return jsonify({
                        'status':
                        'invalid',
                        'message':
                        'recruiter can only send messages to instiadmin'
                    })
            elif (present_user.type == 'student'):
                if (reciever.type != 'alumni'):
                    return jsonify({
                        'status':
                        'invalid',
                        'message':
                        'student can only send messages to alumni'
                    })
            else:
                if (reciever.type == 'student'):
                    return jsonify({
                        'status':
                        'invalid',
                        'message':
                        'alumni can only send messages to students'
                    })

            m = Message(author_id=curr_userid,
                        recipient_id=reciever.id,
                        content=post_data['msg_content'],
                        date_time=time.time())
            db.session.add(m)
            db.session.commit()

            t = ToBeRead(user_id=reciever.id,
                         type='message',
                         entity_id=m.id,
                         timestamp=time.time())
            db.session.add(t)

            db.session.commit()
            response = {
                'status': 'success',
                'message': 'message and toberead entries added'
            }
            return jsonify(response), 200
        else:
            return jsonify({
                'status': 'invalid',
                'message': "user isn't logged in"
            })
    except:
        response = {'status': 'fail', 'message': 'Try again'}
        return jsonify(response), 404


@app.route('/createnotice', methods=['POST'])
def create_notice():
    try:
        post_data = request.json

        auth_header = request.headers.get('Authorization')

        if auth_header:
            auth_token = auth_header.split(" ")[1]

        else:
            auth_token = ''

        if auth_token:
            curr_userid = User.decode_auth_token(auth_token)
            present_user = User.query.get(curr_userid)

            if (present_user.type == "instiadmin"):
                n = Notice(author_id=curr_userid,
                           subject=post_data['subject'],
                           content=post_data['content'],
                           date_time=time.time())
                db.session.add(n)
                db.session.commit()

                for student in Student.query.all():
                    t = ToBeRead(user_id=User.query.filter_by(
                        username=student.username).first().id,
                                 type='notice',
                                 entity_id=n.id,
                                 timestamp=time.time())
                    db.session.add(t)

                db.session.commit()
                response = {
                    'notice': {
                        'id': n.id,
                        'author': n.author.username,
                        'subject': n.subject,
                        'content': n.content,
                        'time': n.date_time
                    },
                    'status': 'success',
                    'message': 'message and toberead entries added'
                }
                return jsonify(response), 200
            else:
                return jsonify({
                    'status': 'invalid',
                    'message': "user isn't logged in"
                })
    except:
        response = {'status': 'fail', 'message': 'Try again'}
        return jsonify(response), 404


@app.route('/writefeedback', methods=['POST'])
def write_feedback():
    # try:
    post_data = request.json

    auth_header = request.headers.get('Authorization')

    if auth_header:
        auth_token = auth_header.split(" ")[1]

    else:
        auth_token = ''

    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        current_user = User.query.get(curr_userid)

        if current_user.type != 'alumni':
            return jsonify({
                'status':
                'invalid',
                'message':
                'only an alumni can give feedback on a job profile'
            }), 500

        #subject in feedback
        f = Feedback(author_id=curr_userid,
                     content=post_data['feedback_content'],
                     profile_id=post_data['profile_id'],
                     date_time=time.time())
        db.session.add(f)
        db.session.commit()

        students_list = Student.query.all()
        for student in students_list:
            t = ToBeRead(user_id=student['id'],
                         type='feedback',
                         entity_id=f.id)
            db.session.add(t)

        db.session.commit()
        response = {
            'status': 'success',
            'message': 'feedback and toberead entries added'
        }
        return jsonify(response), 200
    else:
        return jsonify({
            'status': 'invalid',
            'message': "user isn't logged in"
        })
    # except:
    #     response = {'status': 'fail', 'message': 'Try again'}
    #     return jsonify(response), 404


@app.route('/createposition', methods=['POST'])
def create_position():

    # try:
    post_data = request.json

    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''

    if auth_token:
        # curr_userid = current_user.id
        curr_userid = User.decode_auth_token(auth_token)
        current_user = User.query.get(curr_userid)

        if current_user.type != 'recruiter':
            return jsonify({
                'status':
                'invalid',
                'message':
                'only a recruiter can create a job profile'
            }), 500

        p = Profile(profileName=post_data['profileName'],
                    companyName=current_user.username,
                    recruiter_id=current_user.id,
                    ctc=post_data['CTC'],
                    createDate=time.time(),
                    deadline=post_data['deadline'],
                    description=post_data['description'],
                    degree=post_data['degrees'],
                    dept=post_data['depts'])
        db.session.add(p)
        db.session.commit()

        t = ToBeRead(user_id=1, type='position', entity_id=p.id)
        db.session.add(t)
        db.session.commit()

        response = {
            'status': 'success',
            'message': 'profile and toberead entries added',
            'position': {
                'id': p.id,
                'position_title': p.profileName,
                'description': p.description,
                'company': p.companyName,
                'company_id': p.recruiter_id,
                'CTC': p.ctc,
                'depts': p.dept,
                'degrees': p.degree,
                'create_time': p.createDate,
                'release_time': None,
                'deadline': p.deadline,
                'update_time': p.deadline,
                'read': True,
            }
        }
        return jsonify(response), 200
    else:
        response = {'status': 'invalid', 'message': 'User not logged in'}
        return jsonify(response), 404
    # except:
    #     response = {'status': 'fail', 'message': 'Try again'}
    #     return jsonify(response), 404


@app.route('/applicationdetails', methods=['POST'])
def application_details():
    # try:
    get_data = request.json

    auth_header = request.headers.get('Authorization')

    if auth_header:
        auth_token = auth_header.split(" ")[1]

    else:
        auth_token = ''

    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        present_user = User.query.get(curr_userid)

        if present_user.type != 'student' and present_user.type != 'recruiter':
            return jsonify({
                'status':
                'invalid',
                'message':
                'only a recruiter or a student can view application details'
            }), 401

        a = Application.query.filter_by(id=get_data['application_id']).first()

        return jsonify({
            'application': {
                'id': a.id,
                'position_id': a.profile_id,
                'resume_link': a.content,
                'company': a.profile.companyName,
                'status': a.status,
                'dept': a.student.dept,
                'degree': a.student.degree,
                'cgpa': a.student.cgpa,
                'time': a.date_time,
                'update_time': a.date_time,
                'read': True
            }
        }), 200
    else:
        return jsonify({
            'status': 'invalid',
            'message': "user isn't logged in"
        })
    # except:
    #     response = {'status': 'fail', 'message': 'Try again'}
    #     return jsonify(response), 404


@app.route('/selectapplication', methods=['POST'])
def select_application():
    # try:
    get_data = request.json

    auth_header = request.headers.get('Authorization')

    if auth_header:
        auth_token = auth_header.split(" ")[1]

    else:
        auth_token = ''

    if auth_token:
        curr_userid = User.decode_auth_token(auth_token)
        present_user = User.query.get(curr_userid)

        if present_user.type != 'recruiter':
            return jsonify({
                'status':
                'invalid',
                'message':
                'only a recruiter can update application status'
            }), 500

        a = Application.query.filter_by(id=get_data['application_id']).first()
        a.status = get_data['new_status']
        db.session.commit()

        t = ToBeRead(user_id=a.student_id,
                     type='application',
                     entity_id=get_data['application_id'])
        db.session.add(t)
        db.session.commit()

        response = {
            'status': 'success',
            'message': 'updated application status and toberead entry added'
        }
        return jsonify(response), 200
    # except:
    #     response = {'status': 'fail', 'message': 'Try again'}
    #     return jsonify(response), 404

