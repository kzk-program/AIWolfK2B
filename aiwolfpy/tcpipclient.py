# -*- coding: utf-8 -*-
"""
TcpIpClient

@author: KeiHarada
Date:2016/05/03
UpDate:2016/12/15
UpDate:2017/02/25
"""

from __future__ import print_function, division 
import argparse
import socket
from socket import error as SocketError
import errno
import json

def connect(agent):
    # parse Args
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-p', type=int, action='store', dest='port')
    parser.add_argument('-h', type=str, action='store', dest='hostname')
    input_args = parser.parse_args()
    aiwolf_host = input_args.hostname
    aiwolf_port = input_args.port
    # socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect
    sock.connect((aiwolf_host, aiwolf_port))
    line = ''
    while True:
        try:
            # l01:recieve 8KB
            line_recv = sock.recv(8192).decode('utf-8')
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
                # print(obj_recv)
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
                # print(obj_recv['request'])
                request = obj_recv['request']
                
                # run requested
                if request == 'NAME':
                    sock.send((agent.getName() + '\n').encode('utf-8'))
                elif request == 'ROLE':
                    sock.send(('none\n').encode('utf-8'))
                elif request == 'INITIALIZE':
                    game_setting = obj_recv['gameSetting']
                    agent.initialize(game_info, game_setting)
                elif request == 'DAILY_INITIALIZE':
                    agent.update(game_info, talk_history, whisper_history, request)
                    agent.dayStart()
                elif request == 'DAILY_FINISH':
                    agent.update(game_info, talk_history, whisper_history, request)
                elif request == 'FINISH':
                    agent.update(game_info, talk_history, whisper_history, request)
                    agent.finish()
                elif request == 'VOTE':
                    agent.update(game_info, talk_history, whisper_history, request)
                    sock.send((json.dumps({'agentIdx':int(agent.vote())}, separators=(',', ':')) + '\n').encode('utf-8'))
                elif request == 'ATTACK':
                    agent.update(game_info, talk_history, whisper_history, request)
                    sock.send((json.dumps({'agentIdx':int(agent.attack())}, separators=(',', ':')) + '\n').encode('utf-8'))
                elif request == 'GUARD':
                    agent.update(game_info, talk_history, whisper_history, request)
                    sock.send((json.dumps({'agentIdx':int(agent.guard())}, separators=(',', ':')) + '\n').encode('utf-8'))
                elif request == 'DIVINE':
                    agent.update(game_info, talk_history, whisper_history, request)
                    sock.send((json.dumps({'agentIdx':int(agent.divine())}, separators=(',', ':')) + '\n').encode('utf-8'))
                elif request == 'TALK':
                    agent.update(game_info, talk_history, whisper_history, request)
                    sock.send((agent.talk() + '\n').encode('utf-8'))
                elif request == 'WHISPER':
                    agent.update(game_info, talk_history, whisper_history, request)
                    sock.send((agent.whisper() + '\n').encode('utf-8'))
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise
            else:
                # expected error, connection reset by server
                pass
            # close connection
            sock.close()
            break