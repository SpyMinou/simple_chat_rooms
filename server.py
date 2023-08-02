from flask import Flask, render_template, request, redirect, session, url_for

# socket is used to live update the server without refreshing the page
from flask_socketio import join_room, leave_room, send, SocketIO
import random   # using random library to generate the chatroom code

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"

# setting the socket io integration
socketio = SocketIO(app)

def generate_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += str(random.randint(0,9))
        if code not in rooms:
            break
    return code

rooms = {}

@app.route("/",methods=["GET", "POST"])
def home():
    if request.method == "GET" :
        return render_template("login.html")
    elif request.method == "POST" :
        name = request.form['name']
        code = request.form['roomcode']
        
        join = request.form.get('join',False)       
        create = request.form.get('create',False)
        if (join != False):
            if (name != "") and (code != ""):
                if (code not in rooms):
                    return render_template("login.html",erreur="THE ROOM YOU ARE LOOKING FOR DOES NOT EXIST")
                else:
                    print(name)
                    print(code.isnumeric())
                    session["name"] = name
                    session["room"] = code
                    return redirect(url_for("room",id=code))
            else:
                return render_template("login.html",erreur="YOU DIDNT FILL THE FIELDS")
            
        if (create != False):
            if name != "":
                id = generate_code(5)
                rooms[id] = {"members": 0,"messages":[]}
                session["name"] = name
                session["room"] = id
                return redirect(url_for("room",id=id))
            else: 
                return render_template("login.html",erreur="YOU NEED A NAME TO CREATE A ROOM")

        else:
            return "both arent working"

@app.route("/room",methods=["GET", "POST"])
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms: 
        return redirect(url_for("home"))
    else:
        print(room)
        return render_template("room.html",id=room,messages=rooms[room]["messages"])
    
        
@socketio.on("connect")    
def connnect(auth):
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name":name,"message":"has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(rooms[room]["members"])
    
    print(f"{name} has entered the room {room}")
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name":name,"message":f"{name} has left the room"},to=room)
    print(f"{name} has left the room {room}")

# recieve the message sent from the client and distrbute it to the room
@socketio.on("sending")
def message(data):
    
    room = session.get("room")
    if room not in rooms:
        return
    message_content ={"name": session.get("name"),
                      "message" : data["data"]}
    
    send(message_content, to=room)
    rooms[room]["messages"].append(message_content)
    print(f"{session.get('name')} said : {data['data']} ")

if __name__ == '__main__':
    socketio.run(app=app,debug=True)
