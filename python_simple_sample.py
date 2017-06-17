#!/usr/bin/env python
from __future__ import print_function, division 

# this is main script
# simple version

import aiwolfpy
import aiwolfpy.contentbuilder as cb

myname = 'cash'

class SampleAgent(object):
    
    def __init__(self, agent_name):
        # me
        self.me = {'agentName':agent_name, 'agentIdx':0, 'myRole':'VILLAGER'}
        
        # parser
        # JSON -> DataFrame
        self.parser = aiwolfpy.GameInfoParser()
        
    def getName(self):
        return self.me['agentName']
    
    def initialize(self, game_info, game_setting):
        
        # game_setting
        self.game_setting = game_setting
        
        # base_info
        self.base_info = dict()
        for k in ["day", "roleMap", "remainTalkMap", "remainWhisperMap", "statusMap"]:
            if k in game_info.keys():
                self.base_info[k] =  game_info[k]
        
        self.divined_list = []
        
        # me
        self.me['agentIdx'] = game_info['agent']
        self.me['myRole'] =  game_info["roleMap"][str(self.me['agentIdx'])]
        
        # initialize
        self.parser.initialize(game_info, game_setting)
        
        
    def update(self, game_info, talk_history, whisper_history, request):
        
        # update base_info
        for k in ["day", "roleMap", "remainTalkMap", "remainWhisperMap", "statusMap"]:
            if k in game_info.keys():
                self.base_info[k] =  game_info[k]
        
        # update gameDataFrame
        self.parser.update(game_info, talk_history, whisper_history, request)
        
        
    def dayStart(self):
        return None
    
    def talk(self):
        return cb.over()
    
    def whisper(self):
        return cb.over()
        
    def vote(self):
        return self.me['agentIdx']
    
    def attack(self):
        return self.me['agentIdx']
    
    def divine(self):
        return self.me['agentIdx']
    
    def guard(self):
        return self.me['agentIdx']
    
    def finish(self):
        return None
    


agent = SampleAgent(myname)
    


# run
if __name__ == '__main__':
    aiwolfpy.connect(agent)
    