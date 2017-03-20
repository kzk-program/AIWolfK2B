#!/usr/bin/env python
import aiwolfpy
import aiwolfpy.templatetalkfactory as ttf
import aiwolfpy.templatewhisperfactory as twf

import numpy as np
import scipy.sparse as sp
import sklearn
import pandas as pd


class PandasAgentGAT2017(object):
    
    def __init__(self, agent_name):
        self.agent_name = agent_name
        
    def getName(self):
        return self.agent_name
        
    def update(self, game_info, talk_history, whisper_history, request):
        for talk in talk_history:
            if talk['text'].split()[0] == 'COMINGOUT':
                self.coMap[talk['text'].split()[1]] = talk['text'].split()[2]
            if talk['text'].split()[0] == 'DIVINED':
                SEER = 'Agent[' + "{0:02d}".format(talk['agent']) + ']'
                if SEER not in self.divineMap.keys():
                    self.divineMap[SEER] = dict()
                self.divineMap[SEER][talk['text'].split()[1]] = talk['text'].split()[2]
        if "statusMap" in game_info.keys():
            self.statusMap = game_info["statusMap"]
        
        # RESULT
        if self.role == 'MEDIUM' and 'mediumResult' in game_info.keys():
            if game_info['mediumResult'] is None:
                pass
            else:
                self.result = 'IDENTIFIED '+ 'Agent[' + "{0:02d}".format(int(game_info['mediumResult']['target'])) + '] '+game_info['mediumResult']['result']
        elif self.role == 'SEER' and 'divineResult' in game_info.keys():
            if game_info['divineResult'] is None:
                pass
            else:
                self.result = 'DIVINED '+ 'Agent[' + "{0:02d}".format(int(game_info['divineResult']['target'])) + '] '+game_info['divineResult']['result']
        # update list
        self.white_list = []
        self.black_list = []
        self.gray_list = self.agentNames
        # REMOVE DEAD and SELF
        for ids in self.statusMap.keys():
            if self.statusMap[ids] == "DEAD":
                name = 'Agent[' + "{0:02d}".format(int(ids)) + ']'
                if name in self.gray_list:
                    self.gray_list.remove(name)
        if self.agentName in self.gray_list:
            self.gray_list.remove(self.agentName)
        # JUDGE CO
        if self.playerNum == 5:
            black_co_line = 2
        else:
            black_co_line = 3
        for name in self.coMap.keys():
            if name in self.gray_list:
                # count same co
                role = self.coMap[name]
                count_same_role = 0
                for name_ in self.coMap.keys():
                    if self.coMap[name_] == role:
                        count_same_role += 1
                # only one is white
                if count_same_role == 1:
                    self.white_list.append(name)
                    self.gray_list.remove(name)
                    # trust SEER if only one
                    if name in self.divineMap.keys():
                        for target in self.divineMap[name].keys():
                            if target in self.gray_list:
                                if self.divineMap[name][target] == 'WEREWOLF':
                                    self.black_list.append(target)
                                    self.gray_list.remove(target)
                                else:
                                    self.white_list.append(target)
                                    self.gray_list.remove(target)
                # black line
                elif count_same_role >= black_co_line:
                    self.black_list.append(name)
                    self.gray_list.remove(name)
        # TRUST SELF
        name = self.agentName
        if name in self.divineMap.keys():
            for target in self.divineMap[name].keys():
                if target in self.gray_list:
                    if self.divineMap[name][target] == 'WEREWOLF':
                        self.black_list.append(target)
                        self.gray_list.remove(target)
                    else:
                        self.white_list.append(target)
                        self.gray_list.remove(target)
    
    def initialize(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
        self.agentName = 'Agent[' + "{0:02d}".format(self.agentIdx) + ']'
        self.role = game_info['roleMap'][str(self.agentIdx)]
        self.roleMap = game_info['roleMap']
        self.playerNum = game_setting['playerNum']
        self.agentNames = ['Agent[' + "{0:02d}".format(target) + ']' for target in range(1, self.playerNum+1)]
        self.day = -1
        self.coMap = dict()
        self.divineMap = dict()
        self.result = ""
        self.mytalks = []
        
    def dayStart(self):
        if len(self.gray_list) > 0 and self.ROLE == 'POSSESSED':
            target_int = int(np.random.choice(self.gray_list).split("[")[1].split("]")[0])
            self.result = 'DIVINED '+ 'Agent[' + "{0:02d}".format(target_int) + '] '+'HUMAN'
        return None
    
    def talk(self):
        if self.role in ["SEER", "MEDIUM"] and self.agentName not in self.coMap.keys():
            return ttf.comingout(self.agentIdx, self.role)
        elif self.role == "POSSESSED" and self.agentName not in self.coMap.keys():
            return ttf.comingout(self.agentIdx, "SEER")
        elif self.result != "" and self.result not in self.mytalks:
            self.mytalks.append(self.result)
            return self.result
        else:
            return ttf.over()
    
    def whisper(self):
        return twf.over()
        
    def vote(self):
        if len(self.black_list) > 0:
            return int(np.random.choice(self.black_list).split("[")[1].split("]")[0])
        elif len(self.gray_list) > 0:
            return int(np.random.choice(self.gray_list).split("[")[1].split("]")[0])
        else:
            return self.agentIdx
    
    def attack(self):
        if len(self.white_list) > 0:
            return int(np.random.choice(self.white_list).split("[")[1].split("]")[0])
        elif len(self.gray_list) > 0:
            return int(np.random.choice(self.gray_list).split("[")[1].split("]")[0])
        else:
            return self.agentIdx
    
    def divine(self):
        if len(self.gray_list) > 0:
            return int(np.random.choice(self.gray_list).split("[")[1].split("]")[0])
        else:
            return self.agentIdx
    
    def guard(self):
        if len(self.white_list) > 0:
            return int(np.random.choice(self.white_list).split("[")[1].split("]")[0])
        elif len(self.gray_list) > 0:
            return int(np.random.choice(self.gray_list).split("[")[1].split("]")[0])
        else:
            return self.agentIdx
    
    def finish(self):
        return None

agent = PandasAgentGAT2017('cash')
    


# run
if __name__ == '__main__':
    aiwolfpy.connect(agent)
    