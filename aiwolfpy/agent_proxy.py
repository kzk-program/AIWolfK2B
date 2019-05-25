import socket
from socket import error as socket_error
import errno
import json
from .gameinfoparser import GameInfoParser


# decorator
class AgentProxy(object):

    def __init__(self, agent, my_name, host_name, port, role, parser=None):
        self.agent = agent
        self.my_name = my_name
        self.host_name = host_name
        self.port = port
        self.role = role
        self.sock = None
        self.parser = GameInfoParser()
        self.base_info = dict()

    # ここも色々ある
    def initialize_agent(self, game_info, game_setting):
        if True:
            self.base_info = dict()
            self.base_info['agentIdx'] = game_info['agent']
            self.base_info['myRole'] = game_info["roleMap"][str(game_info['agent'])]
            self.base_info["roleMap"] = game_info["roleMap"]
            self.agent.initialize(self.base_info,  self.parser.get_gamedf_diff(), game_setting)
            return None
        else:
            self.agent.initialize(game_info, game_setting)

    # ここは色々ある
    def update_agent(self, game_info, talk_history, whisper_history, request):
        if True:
            for k in ["day", "remainTalkMap", "remainWhisperMap", "statusMap"]:
                if k in game_info.keys():
                    self.base_info[k] = game_info[k]
            self.parser.update(game_info, talk_history, whisper_history, request)
            self.agent.update(self.base_info, self.parser.get_gamedf_diff(), request)
            return None
        else:
            self.agent.update(game_info, talk_history, whisper_history, request)

    def send_response(self, json_received):
        res_txt = self._get_json(json_received)
        if res_txt is None:
            pass
        else:
            self.sock.send((res_txt + '\n').encode('utf-8'))
        return None

    def _get_json(self, json_received):
        game_info = json_received['gameInfo']
        if game_info is None:
            game_info = dict()
        # talk_history and whisper_history
        talk_history = json_received['talkHistory']
        if talk_history is None:
            talk_history = []
        whisper_history = json_received['whisperHistory']
        if whisper_history is None:
            whisper_history = []
        # request must exist
        # TODO : LOG
        # print(json_received['request'])
        request = json_received['request']
        if request == 'INITIALIZE':
            game_setting = json_received['gameSetting']
        else:
            game_setting = None

        # run_request
        if request == 'NAME':
            return self.my_name
        elif request == 'ROLE':
            return self.role
        elif request == 'INITIALIZE':
            self.initialize_agent(game_info, game_setting)
            return None
        else:
            # UPDATE
            self.update_agent(game_info, talk_history, whisper_history, request)
            if request == 'DAILY_INITIALIZE':
                self.agent.dayStart()
                return None
            elif request == 'DAILY_FINISH':
                return None
            elif request == 'FINISH':
                self.agent.finish()
                return None
            elif request == 'VOTE':
                return json.dumps({'agentIdx': int(self.agent.vote())}, separators=(',', ':'))
            elif request == 'ATTACK':
                return json.dumps({'agentIdx': int(self.agent.attack())}, separators=(',', ':'))
            elif request == 'GUARD':
                return json.dumps({'agentIdx': int(self.agent.guard())}, separators=(',', ':'))
            elif request == 'DIVINE':
                return json.dumps({'agentIdx': int(self.agent.divine())}, separators=(',', ':'))
            elif request == 'TALK':
                return self.agent.talk()
            elif request == 'WHISPER':
                return self.agent.whisper()

    def connect_server(self):
        # socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect
        self.sock.connect((self.host_name, self.port))
        line = ''
        while True:
            try:
                line += self.sock.recv(8192).decode('utf-8')
                line_list = line.split("\n", 1)

                for i in range(len(line_list) - 1):
                    json_received = json.loads(line_list[i])
                    self.send_response(json_received)
                    line = line_list[-1]

                try:
                    # check if valid json
                    json_received = json.loads(line)
                    self.send_response(json_received)
                    line = ''
                except ValueError:
                    pass

            except socket_error as e:
                if e.errno != errno.ECONNRESET:
                    raise
                else:
                    # expected error, connection reset by server
                    pass
                # close connection
                self.sock.close()
                break
        return None
