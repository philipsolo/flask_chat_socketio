# Flask Socket IO Chat 💬

---
A lightweight chat application I created as part of a team project coursework for University using Python, JS, Redis 
and Bootstrap. I have only included the parts necessary for the chat to function written by me. Other parts 
have mixed code with teammates and are beyond the scope of this repository.
---

## Table of Contents
- [Flask Socket IO Chat 💬](#flask-socket-io-chat-)
    * [Notes 🎶](#notes)
    * [Demo & Functionality  🎥](#Demo-&-Functionality)
        + [Chat window](#chat-window)
        + [Multiple Users](#multiple-users)
    * [Structure 🏗️](#structure-)
        + [Frontend (Main Components)](#frontend--main-components-)
        + [Backend (Main Components)](#backend--main-components-)
    * [Build & Deployment 🚀](#build-deployment-)
        + [Local Run 💻](#local-run-)
        + [GCP ☁ ️](#gcp)

    
## Notes 🎶

---

- The whole chat frontend is contained within the [chat.html](chat.html) page. Thanks to the power of Jinja and Javascript code is 
  created on the fly using Macros, in this way a very small amount of code is required for each element and "pseudo" abstraction is achieved.


  
- This is not a recommended approach, usually when engaging in such projects, a React alternative would be quite 
  easier and much more efficient to implement. However, sneakily I was able to quickly build this chat application that has minimal dependencies and is extremely lightweight.

  
- I have included the [models.py](http://models.py) file in order to display the way authentication is handled with a Firebase backend. As some 
  fronted auth code is mixed with teammates I have not included it.
    

- It is easy to use any form of auth, user management as all functions can be used as API's.


 

## Demo & Functionality  🎥
### Chat window
![Gif displaing Chat features and UI](example_gifs/chat_responsiveness.gif)


### Multiple Users
![Gif displaying multiple users](example_gifs/multiple_users.gif)
---

## Structure 🏗️

---

### Frontend (Main Components) 

**chat.html** | JS needed is included within in order to minimize file dependencies. All connections and code replications 
required are also included within. Once a new chat is created in a functional programming manner a macro for a tab is first 
called, then a macro for the contents, and within that a macro for the dictionary of messages is called.

#### An example of the tab macro:
```html
{% macro tab_cont(msg_dict,room_id) %}
    <div aria-labelledby="home-tab" class="tab-pane" id="tabChat-{{ room_id }}" role="tabpanel">
        <div class="bg-white">
            <div class="message-area" id="{{ room_id }}message-area">
                <div id="{{ room_id }}chat">
                    {% for item in msg_dict %}
                        {% if user_name == item['name']%}
                            {{int_user(item['msg'],item['time'])}}
                        {% elif 'server' == item['name']%}
                            {{server_msg(item['msg'],item['time'])}}
                        {% else %}
                            {{ext_user(item['msg'],item['time'],item['picture'])}}
                        {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
        <div class="input-group">
            <div class="input-group-prepend">
                <button value="{{ room_id }}" name="exit_butt" onclick="leave_room(this.value)" type="button" class="btn btn-danger btn-lg rounded-0 d-none d-md-block"><i class="fa fa-close"></i>&nbsp;Exit</button>
            </div>
            <input type="text" id="text{{ room_id }}" placeholder="Enter message" class="form-control rounded-0 border-0 py-4 bg-light text-break">
            <div class="input-group-append">
                <button type="button"  id="{{ room_id }}" onclick="send_message(this.id)" class="btn btn-primary btn-lg rounded-0"><i class="fa fa-paper-plane"></i></button>
            </div>
        </div>
    </div>
{% endmacro %}
```
Called by passing the messages (list withing dictionary containing chats,users and messages withing list to maintain 
a queue), and the room id (for message management via JS).

### Backend (Main Components)


<div class="table-responsive">
    <table class="table">
        <thead>
            <tr>
                <th>File</th>
                <th>Description</th>
                <th>Example</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>

[socket_manage.py](socket_manage.py)</td>

<td>This is the Redis interface, Redis already has a PUB/SUB method build in, but the python library is quite lacking, 
so I decided to rebuild the API  myself with a personal touch for each method in order to maximize customizability
(at the cost of some time inefficiency). I also wanted to use as much Redis functionality as possible in order to further 
learn it.
</td>
<td>

```python
def create_room(self, user_id: str, user_name: str, users: list, room_name: str) -> None:
    """
    :param user_id: the users id
    :param user_name: users name
    :param users: a list with the users to be added to the created room
    :param room_name: name for the new room
    """
    user_rooms = list(self.get_rooms(user_id))
    user_rooms.sort()
    # Create list for personal rooms
    personal_rooms = [room for room in user_rooms if user_id in room]
    if personal_rooms:
        # Increment to avoid naming collisions
        new_room = incr_room(personal_rooms[-1])
    else:
        new_room = user_id + '_0'

    self.add_room(user_id, new_room, room_name, user_name)
    for user in users:
        self.add_room(user, new_room, room_name)
```
This is how a room is created (a counter is inserted to the username when creating the room to avoid naming collisions 
allowing unlimited room creations).
</td>
            </tr>
            <tr>
                <td>

[app.py](app.py)</td>
                <td>Beyond the route management of the web app, the backend chat functionality is also stored within. 
A socket_manage.py instance is created here for Join, Leave etc methods to be used.</td>
<td>

```python
@socketio.on('join_random', namespace='/chat')
def join_random(message):
    """
    Called when user requests to join
    :param message: {msg: "Join random request", time:current time, name:local_user}
    """
    user_dict = session['user_dict']
    socket_man.join_random(user_dict.get('uid'), user_dict.get('name'))
```
</td>
</td>
            </tr>
            <tr>
                <td>

[docker-compose.yml](docker-compose.yml) </td>
                <td>Included for quick testing, contains Redis setup required to run the app. (This is the only 
requirement for a local setup)/td>
<td>

```yaml
    redis:
        image: redis:latest
        ports:
            - 6379:6379
        volumes:
            - ./config/redis.conf:/redis.conf
        command: [ "redis-server", "/redis.conf" ]
```
</tr>
            <tr>
                <td>

[app.yaml](app.yaml)</td>
                <td>Yaml configuration used for GCP deployment</td>
<td>

```yaml
entrypoint: gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 main:app
```
Important Note for Socket IO purposes 1 Gunicorn Worker setup must be implemented
</tr>
        </tbody>
    </table>
</div>

---
## Build & Deployment 🚀

### Local Run 💻
After cloning the Repo install requirements. 

**Important** install the provided versions to avoid bugs, I found multiple 
incompatibilities and issues with different versions.

```bash
pip install -r requirements.txt
```
Deploy Redis with the included yml
```bash
docker-compose up
``` 
Run the app
```bash
python -m flask run
```
**Note**
The Auth for this web app is implemented using Firebase, but the frontend is not in this repository. However, the user 
management class is, a simple JSON with the required parameters can be passed to mimic auth. WTF-forms can be used for a 
quick form before entering the Chat.

### GCP ☁ ️
- Setup [Redis](https://cloud.google.com/memorystore/docs/redis/creating-managing-instances) on GCP 


- The [app.yaml](app.yaml) Included contains the setup for  interfacing Redis with App Engine, and the optimal settings 
  to avoid a connection hassle


- After adding authentication or dummy env variables and installing [gcloud sdk](https://cloud.google.com/sdk/docs/install)
  simply run
  ```bash
  gcloud init
  ```
  Login with gcloud account 
  ```bash
  gcloud app deploy
  ```
  after **enabling** App engine from GCP dashboard
