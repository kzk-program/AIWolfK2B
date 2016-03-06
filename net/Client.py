from __future__ import print_function
import json
import socket
from socket import error as SocketError
import errno

def AIWOLFPythonClient(AgentClass, aiwolf_host, aiwolf_port, agent_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((aiwolf_host, aiwolf_port))
    line = ''
    while True:
        try:
            line_recv = sock.recv(8192)
            if line_recv == '':
                break
            buffer_flg = 1
            while buffer_flg == 1:
                line += line_recv
                if '}\n{' in line:
                    (line, line_recv) = line.split("\n", 1)
                    buffer_flg = 1
                else:
                    buffer_flg = 0
                # parse json
                try:
                    obj_recv = json.loads(line)
                    line = ''
                except ValueError:
                    break
                game_info = obj_recv['gameInfo']
                if game_info is None:
                    game_info = dict()
                talk_history = obj_recv['talkHistory']
                if talk_history is None:
                    talk_history = []
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
                    agent.update(game_info, talk_history)
                    agent.dayStart()
                elif request == 'DAILY_FINISH':
                    pass
                elif request == 'FINISH':
                    # agent.update(game_info, talk_history)
                    agent.finish()
                elif request == 'VOTE':
                    agent.update(game_info, talk_history)
                    sock.send(json.dumps({'agentIdx':agent.vote()}, separators=(',', ':')) + '\n')
                elif request == 'ATTACK':
                    agent.update(game_info, talk_history)
                    sock.send(json.dumps({'agentIdx':agent.attack()}, separators=(',', ':')) + '\n')
                elif request == 'GUARD':
                    agent.update(game_info, talk_history)
                    sock.send(json.dumps({'agentIdx':agent.guard()}, separators=(',', ':')) + '\n')
                elif request == 'DIVINE':
                    agent.update(game_info, talk_history)
                    sock.send(json.dumps({'agentIdx':agent.divine()}, separators=(',', ':')) + '\n')
                elif request == 'TALK':
                    agent.update(game_info, talk_history)
                    sock.send(agent.talk() + '\n')
                elif request == 'WHISPER':
                    agent.update(game_info, talk_history)
                    sock.send(agent.whisper() + '\n')
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise
            else:
                return 'ECONNRESET'
            sock.close()
            break