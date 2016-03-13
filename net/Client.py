from __future__ import print_function
import json
import socket
from socket import error as SocketError
import errno
from template.template import talk_check, whisper_check

def AIWOLFPythonClient(AgentClass, aiwolf_host, aiwolf_port, agent_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect
    sock.connect((aiwolf_host, aiwolf_port))
    line = ''
    while True:
        try:
            # l01:recieve 8KB
            line_recv = sock.recv(8192)
            if line_recv == '':
                break
            buffer_flg = 1
            while buffer_flg == 1:
                # l02:there's more json
                line += line_recv
                if '}\n{' in line:
                    # 2 jsons recieved, goto l02 after l03
                    (line, line_recv) = line.split("\n", 1)
                    buffer_flg = 1
                else:
                    # at most 1 json recieved, goto l01 after l03
                    buffer_flg = 0
                # parse json
                try:
                    # is this valid json?
                    obj_recv = json.loads(line)
                    # ok, goto l03
                    line = ''
                except ValueError:
                    # if not, there's more to read, goto l01 now
                    break
                # l03 make game_info
                game_info = obj_recv['gameInfo']
                if game_info is None:
                    game_info = dict()
                # talk_history and whisper_history
                talk_history = obj_recv['talkHistory']
                if talk_history is None:
                    talk_history = []
                whisper_history = obj_recv['whisperHistory']
                if whisper_history is None:
                    whisper_history = []
                # request must exist
                request = obj_recv['request']
                
                # run requested
                if request == 'NAME':
                    sock.send(agent_name + '\n')
                elif request == 'ROLE':
                    sock.send('none\n')
                elif request == 'INITIALIZE':
                    game_setting = obj_recv['gameSetting']
                    agent = AgentClass(game_info, game_setting)
                elif request == 'DAILY_INITIALIZE':
                    agent.dayStart(game_info)
                elif request == 'DAILY_FINISH':
                    agent.dayFinish(talk_history, whisper_history)
                elif request == 'FINISH':
                    agent.finish(game_info)
                elif request == 'VOTE':
                    sock.send(json.dumps({'agentIdx':agent.vote(talk_history, whisper_history)}, separators=(',', ':')) + '\n')
                elif request == 'ATTACK':
                    sock.send(json.dumps({'agentIdx':agent.attack()}, separators=(',', ':')) + '\n')
                elif request == 'GUARD':
                    sock.send(json.dumps({'agentIdx':agent.guard()}, separators=(',', ':')) + '\n')
                elif request == 'DIVINE':
                    sock.send(json.dumps({'agentIdx':agent.divine()}, separators=(',', ':')) + '\n')
                elif request == 'TALK':
                    sock.send(talk_check(agent.talk(talk_history, whisper_history)) + '\n')
                elif request == 'WHISPER':
                    sock.send(whisper_check(agent.whisper(talk_history, whisper_history)) + '\n')
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise
            else:
                # expected error, connection reset by server
                pass
            # close connection
            sock.close()
            break