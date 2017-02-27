#!/usr/bin/env python
import aiwolfpy
import aiwolfpy.templatetalkfactory as ttf
import aiwolfpy.templatewhisperfactory as twf

import numpy as np
import scipy.sparse as sp
import sklearn
import pandas as pd

class SampleAgent(object):
    
    def __init__(self, agent_name):
        self.agent_name = agent_name
        pass
        
    def getName(self):
        return self.agent_name
        
    def update(self, game_info, talk_history, whisper_history):
        pass
    
    def initialize(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
        
    def dayStart(self):
        return None
    
    def talk(self):
        return ttf.over()
    
    def whisper(self):
        return twf.over()
        
    def vote(self):
        return self.agentIdx
    
    def attack(self):
        return self.agentIdx
    
    def divine(self):
        return self.agentIdx
    
    def guard(self):
        return self.agentIdx
    
    def finish(self):
        return None
    


agent = SampleAgent('AIWolfPy_sample')
    


# run
if __name__ == '__main__':
    aiwolfpy.connect(agent)
    