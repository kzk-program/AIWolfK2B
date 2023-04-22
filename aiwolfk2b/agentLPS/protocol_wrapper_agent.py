# pythonのprotocol用のエージェントのインスタンスを渡して、NLのエージェントとして使えるようにするラッパー.
import argparse
import logging
import os
import random
import sys
from logging import FileHandler, Formatter, StreamHandler, getLogger

import aiwolfpy
import pandas as pd
from python_simple_protocol_agent import SampleAgent  # 試しに使うprotocol用のエージェント
from aiwolfk2b.agentLPS.speaker import SimpleSpeaker # プロトコルを自然言語に変換するクラス
from aiwolfk2b.agentLPS.jp_to_protocol import JPToProtocolConverter,BertForSequenceClassificationMultiLabel # 自然言語をプロトコルに変換するクラス
from OKAMI import OKAMI


class ProtocolWrapperAgent:
    def __init__(self, agent):
        self.agent = agent
        self.base_info= dict()
        self.game_setting = dict()
        self.talked_num = 0
        self.request = None
        self.diff_data = None
        self.protocol_to_NL_converter = None
        self.NL_to_protocol_converter = JPToProtocolConverter()

    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting
        p_diff_data = self.make_protocol_diff_data(diff_data)
        self.agent.initialize(base_info, p_diff_data, game_setting)
        # converterの初期化
        self.protocol_to_NL_converter = SimpleSpeaker(me="Agent[{:02d}]".format(base_info["agentIdx"]))
        self.NL_to_protocol_converter = JPToProtocolConverter()

    def update(self, base_info, diff_data, request):
        self.base_info = base_info
        p_diff_data = self.make_protocol_diff_data(diff_data)
        self.agent.update(base_info, p_diff_data, request)
    
    # diff_dataの自然言語の部分をプロトコルに変換して返す
    def make_protocol_diff_data(self,diff_data):
        # diff_dataの内、自然言語部分(text)をプロトコルに変換して返す
        protocol_diff_data = diff_data.copy()
        # Dataframeのtextカラムの自然言語をプロトコルに変換
        for i in range(len(diff_data)):
            protocol_diff_data.at[i,'text'] = self.convert_NL_to_protocol(diff_data.at[i,'text'])
        
        return protocol_diff_data

    # 自然言語をプロトコルに変換
    def convert_NL_to_protocol(self, NL_text):
        # NLをプロトコルに変換
        # # TODO: ここに変換のコードを書く
        # test_protocol_text_options = ["COMINGOUT Agent[01] SEER","VOTE Agent[04]","REQUEST ANY (VOTE Agent[01])"]
        # return random.choice(test_protocol_text_options)
        if NL_text == "":
            return ""
        #print("NL_text:",NL_text)
        #print("type(NL_text):",type(NL_text))
        prompts = self.NL_to_protocol_converter.convert(NL_text)
        #print("prompts:",prompts)
        return prompts[0]
        
    
    # プロトコルを自然言語に変換
    def convert_protocol_to_NL(self, protocol_text):
        # プロトコルをNLに変換
        # TODO: より良い変換アルゴリズムを使う
        return self.protocol_to_NL_converter.speak(text=protocol_text)

    def dayStart(self):
        return self.agent.dayStart()

    def talk(self):
        # protocolのtalkを自然言語に変換したうえで返す
        #return self.convert_protocol_to_NL(self.agent.talk()._get_text())
        return self.convert_protocol_to_NL(self.agent.talk()) #OKAMIのエージェントを使う場合,古いのでstrで返してくる

    def whisper(self):
        return self.agent.whisper()

    def vote(self):
        return self.agent.vote()

    def attack(self):
        return self.agent.attack()

    def divine(self):
        return self.agent.divine()

    def guard(self):
        return self.agent.guard()

    def finish(self):
        return self.agent.finish()
    
    
# run
if __name__ == '__main__':
    
    # logger
    logger = getLogger("aiwolfpy")
    logger.setLevel(logging.NOTSET)
    # handler
    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.NOTSET)
    handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(handler_format)

    logger.addHandler(stream_handler)   

    # name
    myname = 'sample_python1'
    
    #protocol_agent = SampleAgent()
    protocol_agent= OKAMI("OKAMI")
    wrapper_agent = ProtocolWrapperAgent(protocol_agent)

    # read args
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-p', type=int, action='store', dest='port')
    parser.add_argument('-h', type=str, action='store', dest='hostname')
    parser.add_argument('-r', type=str, action='store', dest='role', default='none')
    parser.add_argument('-n', type=str, action='store', dest='name', default=myname)
    input_args = parser.parse_args()


    client_agent = aiwolfpy.AgentProxy(
        wrapper_agent, input_args.name, input_args.hostname, input_args.port, input_args.role, logger, "pandas"
    )

    
    client_agent.connect_server()