#!/usr/bin/env python

# simple version
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler
import aiwolfpy
import aiwolfpy.contentbuilder as cb
import argparse

# name
my_name = 'cash'

# logger
logger = getLogger("aiwolfpy")
logger.setLevel(logging.NOTSET)
# handler
stream_handler = StreamHandler()
stream_handler.setLevel(logging.NOTSET)
handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(handler_format)


logger.addHandler(stream_handler)

# file_handler = FileHandler('aiwolf_game.log')
# file_handler.setLevel(logging.WARNING)
# file_handler.setFormatter(handler_format)
# logger.addHandler(file_handler)


class SampleAgent(object):
    
    def __init__(self):
        # my name
        self.base_info = dict()
        self.game_setting = dict()

    def getName(self):
        return self.my_name
    
    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        # game_setting
        self.game_setting = game_setting
        
    def update(self, base_info, diff_data, request):
        self.base_info = base_info
        
    def dayStart(self):
        return None
    
    def talk(self):
        return cb.over()
    
    def whisper(self):
        return cb.over()
        
    def vote(self):
        return self.base_info['agentIdx']
    
    def attack(self):
        return self.base_info['agentIdx']
    
    def divine(self):
        return self.base_info['agentIdx']
    
    def guard(self):
        return self.base_info['agentIdx']
    
    def finish(self):
        return None
    

agent = SampleAgent()

# read args
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-p', type=int, action='store', dest='port')
parser.add_argument('-h', type=str, action='store', dest='hostname')
parser.add_argument('-r', type=str, action='store', dest='role', default='none')
input_args = parser.parse_args()


client_agent = aiwolfpy.AgentProxy(agent, my_name, input_args.hostname, input_args.port, input_args.role, logger, "pandas")

# run
if __name__ == '__main__':
    client_agent.connect_server()
