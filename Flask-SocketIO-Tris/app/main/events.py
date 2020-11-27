import json
from flask import session
from flask_socketio import emit, join_room, leave_room
from .. import socketio
people = {}
games = []
queue = None
currentIndex = 0



@socketio.on('joined', namespace='/chat')
def joined(message):
    global people, currentIndex, queue
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    name = session.get('name')    
    while name in people:
        name = name + '1'
    people[name] = 0
    if queue==None:
        currentIndex+=1
        room = 'room'+str(currentIndex)
        queue = Game(currentIndex, name)
        sym = 'o'
        own = queue.turn
        playerId = 0
        emit('status', {'msg': ' you joined room number ' + str(currentIndex) + '  with symbol ' + sym, 'roomId': currentIndex, 'yourId': playerId, 'yourSym': sym, 'score': people[name], 'controlId': own})
    else:
        room = 'room'+str(currentIndex)
        sym = 'x'
        queue.player1 = name
        own = queue.turn
        playerId = 1
        emit('status', {'msg': ' you joined room number ' + str(currentIndex) + '  with symbol ' + sym, 'roomId': currentIndex, 'yourId': playerId, 'yourSym': sym, 'score': people[name], 'controlId': own})
        emit('status', {'msg': name+ ' has joined room number ' + str(currentIndex) + ' with symbol ' + sym + ' together with ' + queue.player0, 'roomId': currentIndex, 'yourId': playerId, 'yourSym': sym, 'score': people[name], 'controlId': own}, room=room)
        games.append(queue)
        queue = None
    join_room(room)


@socketio.on('text', namespace='/chat')
def text(message):
    global games
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    game = [a for a in games if a.gameid==message['gameid']]
    if len(game)==1:       
        x = int(message['x'])-1
        y = int(message['y'])-1
        room = 'room'+str(message['gameid'])
        own = int(message['id'])
        game[0].placeMark(x, y, message['sym'], own)
        if own == 0:
            winner = game[0].player0
            loser = game[0].player1
        else:
            winner = game[0].player1
            loser = game[0].player0
        if game[0].owner[x][y] and ((game[0].owner[0][y] == game[0].owner[1][y] and game[0].owner[1][y] == game[0].owner[2][y]) or (game[0].owner[x][0] == game[0].owner[x][1] and game[0].owner[x][1] == game[0].owner[x][2])):
            #game[0].turn = 1 - own
            people[winner] += 1
            emit('status', {'msg': winner + ' has won this game and has ' + str(people[winner]) + ' points', 'id': own, 'score': people[winner]}, room=room)
            game[0].clear()
        elif game[0].owner[x][y] and x == y and game[0].owner[0][0] == game[0].owner[1][1] and game[0].owner[1][1] == game[0].owner[2][2]:
            #game[0].turn = 1 - own
            people[winner] += 1
            emit('status', {'msg': winner + ' has won this game and has ' + str(people[winner]) + ' points', 'id': own, 'score': people[winner]}, room=room)
            game[0].clear()
        elif game[0].owner[x][y] and (x+y) == 2 and game[0].owner[2][0] == game[0].owner[1][1] and game[0].owner[1][1] == game[0].owner[0][2]:
            #game[0].turn = 1 - own
            people[winner] += 1
            emit('status', {'msg': winner + ' has won this game and has ' + str(people[winner]) + ' points', 'id': own, 'score': people[winner]}, room=room)
            game[0].clear()
        elif all(all(game[0].owner[i][j] != False for i in range(3)) for j in range(3)):
            emit('status', {'msg':' the game was tied between ' + winner + ' with '+ str(people[winner]) + ' points and ' + loser + ' with '+ str(people[loser]) + ' points', 'id': 2, 'score': people[winner]}, room=room)
            game[0].clear()

@socketio.on('left', namespace='/chat')
def left(message):
    global games
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    gameid = message['gameid']
    try:
        game = [a for a in self.games if a.gameid==gameid][0]
        room = 'room'+message['gameid']
        emit('close', {'msg': 'the game was closed'}, room=room)
    except:
        pass

class Game:
    def __init__(self, currentIndex, player0):
        # whose turn (1 or 0)
        self.turn = 0
        #owner map
        self.owner=[[False for x in range(3)] for y in range(3)]
        self.values = {}
        #gameid of game
        self.gameid=currentIndex
        #initialize the players including the one who started the game
        self.player0=player0
        self.player1=None
        #chat room
        self.room = 'room'+str(self.gameid)
    def placeMark(self, x, y, data, num):
        #make sure it's their turn
        if num==self.turn:
            cell = "a"+str(x+1)+str(y+1)
            self.values[cell] = data
            self.owner[x][y] = self.turn+1
            self.turn = 1 - self.turn
            emit('question', json.dumps(self.values), room=self.room)
    def clear(self):
        self.values={}
        self.owner=[[False for x in range(3)] for y in range(3)]
        #self.turn = 1 - self.turn
        emit('question', json.dumps(self.values), room=self.room)
