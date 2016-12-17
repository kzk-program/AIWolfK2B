#!/usr/bin/env python
import aiwolfpy
import aiwolfpy.templatetalkfactory as ttf
import aiwolfpy.templatewhisperfactory as twf

import numpy as np
import scipy.sparse as sp
import sklearn
import pandas as pd

class MyAgent(object):
    
    NAME = 'aiwolfpy'
    
    def __init__(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
        
    def dayStart(self, game_info):
        return None
    
    def dayFinish(self, talk_history, whisper_history):
        return None
    
    def finish(self, game_info):
        return None
    
    def vote(self, talk_history, whisper_history):
        return self.agentIdx
    
    def attack(self):
        return self.agentIdx
    
    def guard(self):
        return self.agentIdx
    
    def divine(self):
        return self.agentIdx
    
    def talk(self, talk_history, whisper_history):
        return ttf.over()
    
    def whisper(self, talk_history, whisper_history):
        return twf.over()

# run
if __name__ == '__main__':
    aiwolfpy.connect(MyAgent)
    