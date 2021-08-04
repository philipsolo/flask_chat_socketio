import json
import os
import flask
from flask import Flask, render_template, session, send_from_directory, request, jsonify, Blueprint
from flask_socketio import emit, join_room, leave_room, SocketIO
from models import User, get_all_users
from socket_manage import MessageManage

"""Flask Configuration files starts user object, Redis and flask app"""
async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax')

socketio = SocketIO(app, async_mode=async_mode, pingInterval=10000, pingTimeout=10000,
                    cors_allowed_origins=["http://localhost:5000",
                                          "https://routetouni.me",
                                          "https://www.routetouni.me"],
                    logger=True, engineio_logger=True)

main = Blueprint('main', __name__)
user_obj = User()
socket_man = MessageManage()


@app.route('/sessionLogin', methods=['GET', 'POST'])
def session_login():
    """
    Called by frontend when user logs in, passing
    calling function to set cookie via token received
    """
    response = user_obj.login_user()
    return response


@app.route('/sessionLogout', methods=['GET', 'POST'])
def session_logout():
    """Passed from frontend call to logout user"""
    user_obj.logout_user()
    return index()


@app.route('/')
def index():
    """
    Check if the user exists in the session if not check if a
    token exists for the user to add him to session.
    """
    if "name" not in session:
        session_cookie = flask.request.cookies.get('session_token')
        if session_cookie:
            user = user_obj.verify_user
        else:
            user = None
    else:
        user = session['user_dict']
    return render_template("index.html", user=user)


@app.route('/gregister')
def gregister():
    return render_template("google-login.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/chat')
def chat():
    """
    Performs user authentication and sends user to chat template
    :return: the chat template if user is authenticated else index page
    """
    user = user_obj.verify_user
    if not user:
        return render_template("index.html", user=user)
    else:
        if user.get('mentor_verified'):
            role = 'Peer Mentor'
        else:
            role = 'Student'
        return render_template('chat.html', prev_msg=socket_man.conv_dict(user.get('uid')),
                               user_name=user.get('name'), role=role)


@app.route("/chat/get_users", methods=['GET', 'POST'])
def create_entry():
    """
    Requested from chat.html via ajax in order to retrieve all users and id's for chat creation
    :return: json containing all users in the database except user making request
    """
    user_dict = session['user_dict']
    if request.method == 'GET':
        ref = get_all_users()
        ref.pop(user_dict.get('uid'))
        return jsonify(ref)
    if request.method == 'POST':
        return 'Success', 200


@app.route('/chat/create_chat', methods=['GET', 'POST'])
def create_chat():
    """
    This function is used to create a new chat, the users it will contain as well as the name are sent via ajax
    when this function is called
    :return: json with status of chat creation
    """
    user_dict = session['user_dict']
    if user_dict.get('mentor_verified'):
        user_add = []
        room_name = None
        if request.method == 'POST':
            form_json = request.get_json()
            for item in form_json:
                # Set the name of the room to be created
                if item.get('name') == 'chat_name':
                    room_name = item['value']
                else:
                    user_add.append(item['name'])
            socket_man.create_room(user_dict.get('uid'), user_dict.get('name'), user_add, room_name)
            return json.dumps({'status': 'OK'})
        return json.dumps({'status': 'ERROR'})
    else:
        return chat()


# When Client Enters
@socketio.on('joined', namespace='/chat')
def joined(message):
    """
    called by frontend once websocket connection is established, grabs user rooms/messages and adds the user to each one
    :param message: {'name':user that joined, 'time':time joined}
    """
    user_dict = session['user_dict']
    if user_dict.get('name'):
        user_conv = socket_man.conv_dict(user_dict.get('uid'))
    else:
        return chat()
    for category in user_conv:
        for room in user_conv[category]:
            join_room(room)
            emit('status', {'msg': "Has Joined the Chat", 'name': user_dict.get('name'), 'uid': user_dict['uid'],
                            "room_id": str(room), 'color': 'success', 'picture': user_dict.get('picture'),
                            'type': 'join'},
                 room=room, prev_msg=user_conv, user_name=user_dict.get('name'))


@socketio.on('text', namespace='/chat')
def text(message):
    """
    Called by javascript frontend when user sends message, forwards the message to all users in the room, adds it
    to the redis database for storage
    :param message: {msg: the users text-message, time: time sent, name: name of sender, room_id: the room received from}
    """
    user_dict = session['user_dict']

    # Room Message arrived from
    room = message['room_id']

    # Add the user picture to the redis store
    message['picture'] = user_dict.get('picture')

    # First check if user in the chat
    if socket_man.check_user_in(user_dict.get('uid'), room):
        emit('internal_msg',
             {'msg': message['msg'], 'room_id': str(room), 'uid': user_dict.get('uid'), 'name': user_dict.get('name'),
              'picture': user_dict.get('picture')},
             room=room, user_name=user_dict.get('name'))
        socket_man.add_message(room, message, user_dict.get('uid'))
    else:
        print("Error User not in room")


@socketio.on('join_random', namespace='/chat')
def join_random(message):
    """
    Called when user requests to join
    :param message: {msg: "Join random request", time:current time, name:local_user}
    """
    user_dict = session['user_dict']
    socket_man.join_random(user_dict.get('uid'), user_dict.get('name'))


@socketio.on('exit_room', namespace='/chat')
def exit_room(message):
    """
    Called when a user clicks to exit a room, removes him from redis and socket.
    :param message: {msg: "Room exit request", time: Current time, name:local_user, room_id:room_id}
    """
    user_dict = session['user_dict']
    socket_man.del_room(user_dict.get('uid'), message['room_id'])
    emit('status', {'msg': "Has left the Chat", 'name': user_dict.get('name'), 'color': 'danger', 'type': 'exit',
                    'room_id': message['room_id']}, room=message['room_id'], user_name=user_dict.get('name'))
    leave_room(message['room_id'])


@socketio.on('disconnect', namespace='/chat')
def disconnected():
    """
    Called after a minute of user disconnect, cleans of user info and sends message to the rooms he was in
    """
    user_dict = session['user_dict']
    for room in socket_man.get_rooms(user_dict.get('uid')):
        join_room(room)
        socketio.send('status',
                      {'msg': "Has left the Chat", 'name': user_dict.get('name'), 'color': 'danger', 'type': 'exit'},
                      room=room, user_name=user_dict.get('name'))
        leave_room(room)


if __name__ == '__main__':
    socketio.run(app, debug=True)
