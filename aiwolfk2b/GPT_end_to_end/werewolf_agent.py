from logging import getLogger, StreamHandler, Formatter, FileHandler
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
sys.path.append(str(pathlib.Path(__file__).parent.parent) + "\\aiwolfpy")
from pathlib import Path
import aiwolfpy
import logging
import openai
import Levenshtein
import argparse

# import os
# import threading
# import time
# import textwrap
# import random
# import re
# import copy
# import requests, simpleaudio, tempfile, json
# import pyaudio
# import wave
# import numpy as np
# from concurrent.futures import ThreadPoolExecutor

from time import sleep
# name
myname = 'gpt3_werewolf_python'
PLAYER_NAMES = [myname]

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

## MODEL SETTINGS
ENABLE_COT = True
MODEL = "gpt-3.5-turbo"
TEMPERATURE = 1
MAX_TOKEN = None
MESSAGE_LOG_DIR = "log_messages"

## GAME SETTINGS
TALKS_PER_DAY = 2
SHUFFLE = True

# file_handler = FileHandler('aiwolf_game.log')
# file_handler.setLevel(logging.WARNING)
# file_handler.setFormatter(handler_format)
# logger.addHandler(file_handler)

# Accumulate game informatin which was sent from server, and convert it to text, then send it to GPT-3.


#######################################

class GameInfoAccumulater:
    def __init__(self, base_info):
        self.role_to_japanese = {"WEREWOLF":"人狼", "POSSESSED":"狂人", "SEER":"占い師", "VILLAGER":"村人", "BODYGUARD":"騎士", "MEDIUM":"霊媒師"}
        # self.context = "私は" + "Agent[{:02d}] ".format(base_info['agentIdx']) +"です。私の役割は" + self.role_to_japanese[str(base_info['myRole'])] + "です。\n"
        # self.context = """
        #  {"あなたは" + "Agent[{:02d}]".format(base_info['agentIdx']) +"です。あなたの役割は" + self.role_to_japanese[str(base_info['myRole'])] + "です。"}
        # """
        self.today = -1
        self.context = [
        
                # systemに役職を書いた方がいいのだろうか
                # "role": "system",
                # "content": textwrap.dedent(
                    f"""\
                    テキストベースの人狼ゲームに参加しているプレイヤーとして振舞ってください。
                    {"あなたは"+"Agent[{:02d}]".format(base_info['agentIdx']) +"です。あなたの役割は" + self.role_to_japanese[str(base_info['myRole'])] + "です。"}
                    ゲーム進行を務めるのはGM(Game Master)です。
                    各プレイヤーが順番に発言していき{TALKS_PER_DAY}周回ると投票に移ります。
                    
                    以下は各役職の説明です。
                    村人(VILLAGER): ただの村人です。
                    占い師(SEER): 一日目の夜から、誰か一人を選んでその人の役職を知ることが出来ます。
                    騎士(BODYGUARD): 二日目の夜から、誰か一人を選んでその人を人狼の襲撃から守ることが出来ます。
                    狂人(POSSESSED): 村人として扱われますが、人狼の味方をします。人狼が勝つことで狂人も勝利出来ます。
                    人狼(WEREWOLF): 二日目の夜から、誰か一人を選んで殺すことが出来ます。

                    役職が狂人、人狼の場合はばれないために自分が狂人、人狼であることを他のメンバーに言わないで下さい。しかし、狂人の場合は人狼に気づいて
                    もらえるように工夫する必要があります。自分が人狼である場合は占い師などの役職になりすます戦略もあります。

                    自分が人狼、狂人ではないかと疑われたら疑いを晴らすために弁解をしてください。嘘をついても構いませんが、過去の自分の発言と矛盾しないように
                    して下さい。
                    """
        ]
                # ),
            
            # {
            #     "role": "user",
            #     "content": textwrap.dedent(
            #         f"""
            #         ### GM ###
            #         ではゲームを始めましょう。準備は良いですか？
            #         """
            #     ),
            # },
            # {
            #     "role": "assistant",
            #     "content": textwrap.dedent(
            #         f"""
            #         <thought>
            #         1. Game Masterから準備が出来ているか聞かれています。
            #         2. 準備が出来ていることを伝えます。
            #         </thought>
            #         <statement>
            #         準備完了です。
            #         </statement>
            #         """
            #     ),
            # },
        
    # def past_remark(self,)
        
    def set_context(self, diff):
        self.context[0] += self.diff_data_to_text(diff)
        print(self.context[0]+"#########################")
        return
    def get_all_context(self):
        return self.context[0]
    def diff_data_to_text(self, diff):
        if diff.empty:
            return ""
        text = ""
        
        for index, row in diff.iterrows():
            if self.today != row.day:
                text += "Day " + str(row.day) + "\n"
                self.today = row.day
            if row.type == "talk":
                text += "Agent[{:02d}]: ".format(row["agent"]) + str(row.text) + "\n"
            elif row.type == "vote":
                text += "Agent[{:02d}]".format(row["agent"]) + "の投票先: Agent[" + row.text[11:13] + "]\n" 
            elif row.type == "finish":
                text += "ゲーム終了。" + "Agent[{:02d}]".format(row["agent"]) + "は" + self.role_to_japanese[row.text.split()[2]] + "でした。\n"
            else:
                text += str(row.type) + ", " +"Agent[{:02d}]: ".format(row["agent"]) + str(row.text) + "\n"
        return text

# GPT3
class AIChat:
    def __init__(self):
        with open(Path(__file__).resolve().parent.parent / 'GPT_end_to_end/openAIAPIkey.txt', "r") as f:
            openai.api_key = f.read()
        #log_paths = ['./werewolf_jp_examples/examples_for_gptinput_1.txt']
        log_paths = []
        self.examples = "人狼ゲームを行います。\n"
        for i, log_path in enumerate(log_paths):
            self.examples += str(i) + "個目の人狼ゲームの例を見せます。"
            with open(log_path, 'r', encoding="utf-8") as f:
                self.examples += f.read()
        self.examples += "では、これから人狼ゲームを始めます。\n"
    
    def speak(self, context):
        #send context to GPT-3, and return response
        print("sending to GPT-3")
        response = openai.Completion.create(engine="text-davinci-003",
            prompt=self.examples+context,
            max_tokens=50,
            temperature=0.5)
        
        # GPTとの通信内容を保存しておく
        # with open(Path(__file__).resolve().parent / 'log_sending_to_gpt.txt', 'a', encoding="utf-8") as f:
        #     f.write("---------------\n")
        #     f.write("sent context:\n")
        #     f.write(self.examples + context)
        #     f.write("\n")
        #     f.write("response:\n")
        #     f.write(response['choices'][0]['text'])
        #     f.write("\n----------------\n")
        print("sent to GPT-3")
        return response['choices'][0]['text']
        # sleep(1)

# 
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
        chat_vote = self.aichat.speak(now_context + "今生き残っている、かつ追放されていないエージェントの中で人狼だと最も疑わしい一人は、")
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
