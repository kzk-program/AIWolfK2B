#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This code is originated from python_simple_sample.py


from logging import getLogger, StreamHandler, Formatter, FileHandler
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
sys.path.append(str(pathlib.Path(__file__).parent.parent) + "\\aiwolfpy")
from pathlib import Path
import aiwolfpy
import logging
import Levenshtein
import argparse
from time import sleep

from aiwolfk2b.GPT_end_to_end.game_info_accumulater import GameInfoAccumulater
from aiwolfk2b.GPT_end_to_end.ai_chat import AIChat

# name
myname = 'gpt3_python'

# content factory
cf = aiwolfpy.ContentFactory()

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

# 発話と投票先決定にGPT3を使ったend to endなエージェント
# 投票先決定では、最も人狼だろうと思われるエージェントに投票するようになっている。
# その他（占い先など）はすべて自分のエージェント番号を返している

class GPT3Agent(object):
    
    def __init__(self):
        # my name
        self.base_info = dict()
        self.game_setting = dict()
        self.my_name = myname
        self.talked_num_today = 0
        self.aichat = AIChat()

    def getName(self):
        return self.my_name
    
    # new game (no return)
    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting
        self.gameinfo = GameInfoAccumulater(base_info)

        
    # new information (no return)
    def update(self, base_info, diff_data, request):
        self.base_info = base_info
        self.gameinfo.set_context(diff_data)

    # Start of the day (no return)
    def dayStart(self):
        #reset the number of talks
        self.talked_num_today = 0
        return None

    # conversation actions: require a properly formatted
    def talk(self):
        if self.talked_num_today >= 3:
            return cf.over()
        else:
            self.talked_num_today += 1

        # get game information
        now_context = self.gameinfo.get_all_context()
        # speak using GPT-3
        return self.aichat.speak(now_context + "Agent[{:02d}]: ".format(self.base_info['agentIdx']))

    # whisper: speak between werewolves
    def whisper(self):
        # just say "Over"
        return cf.over()
        
    # targetted actions: Require the id of the target
    # agent as the return
    def vote(self):
        now_context = self.gameinfo.get_all_context()
        # this is not appropriate if the agent is in the werewolf team.
        chat_vote = self.aichat.speak(now_context + "今生き残っているエージェントの中で人狼だと最も疑わしい一人は、")
        # vote for the agent who is the most similar to the message fron GPT-3
        min_val = 10000
        min_arg = -1
        for i in range(5):
            if min_val > Levenshtein.distance(chat_vote, "Agent[{:02d}]".format(i)):
                min_val = Levenshtein.distance(chat_vote, "Agent[{:02d}]".format(i))
                min_arg = i
        return min_arg

    def attack(self):
        return self.base_info['agentIdx']

    def divine(self):
        return self.base_info['agentIdx']

    def guard(self):
        return self.base_info['agentIdx']

    # Finish (no return)
    def finish(self):
        return None
    

agent = GPT3Agent()

# read args
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-p', type=int, action='store', dest='port')
parser.add_argument('-h', type=str, action='store', dest='hostname')
parser.add_argument('-r', type=str, action='store', dest='role', default='none')
parser.add_argument('-n', type=str, action='store', dest='name', default=myname)
input_args = parser.parse_args()


client_agent = aiwolfpy.AgentProxy(
    agent, input_args.name, input_args.hostname, input_args.port, input_args.role, logger, "pandas"
)

# run
if __name__ == '__main__':
    client_agent.connect_server()
