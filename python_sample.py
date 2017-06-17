#!/usr/bin/env python
from __future__ import print_function, division 

# this is main script

import aiwolfpy
import aiwolfpy.contentbuilder as cb

# sample 
import aiwolfpy.cash

myname = 'cash'

class PythonPlayer(object):
    
    def __init__(self, agent_name):
        # me
        self.me = {'agentName':agent_name, 'agentIdx':0, 'myRole':'VILLAGER'}
        
        # parser
        # JSON -> DataFrame
        self.parser = aiwolfpy.GameInfoParser()
        
        # predictor from sample
        # DataFrame -> P
        self.predicter_15 = aiwolfpy.cash.Predictor_15()
        
        
        
        
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
        
        # me
        self.me['agentIdx'] = game_info['agent']
        self.me['myRole'] =  game_info["roleMap"][str(self.me['agentIdx'])]
        
        # initialize
        self.parser.initialize(game_info, game_setting)
        self.predicter_15.initialize(game_info, game_setting)
                
        ### EDIT FROM HERE ###     
        self.divined_list = []
        self.comingout = ''
        self.myresult = ''
        self.not_reported = False
        self.vote_declare = 0
        

        
    def update(self, game_info, talk_history, whisper_history, request):
        
        # update base_info
        for k in ["day", "roleMap", "remainTalkMap", "remainWhisperMap", "statusMap"]:
            if k in game_info.keys():
                self.base_info[k] =  game_info[k]
        
        # result
        if request == 'DAILY_INITIALIZE':
            # IDENTIFY
            if game_info['mediumResult'] is not None:
                self.not_reported = True
                m = game_info['mediumResult']
                self.myresult = 'IDENTIFIED Agent[' + "{0:02d}".format(m['target']) + '] ' + m['result']
                
            # DIVINE
            if game_info['divineResult'] is not None:
                self.not_reported = True
                d = game_info['divineResult']
                self.myresult = 'DIVINED Agent[' + "{0:02d}".format(d['target']) + '] ' + d['result']
                
            # GUARD
            if game_info['guardedAgent'] != -1:
                self.myresult = 'GUARDED Agent[' + "{0:02d}".format(game_info['guardedAgent']) + ']'
                
            # POSSESSED
            if self.me['myRole'] == 'POSSESSED':
                self.not_reported = True
                
        # UPDATE
        if self.base_info["day"] == 0 and request == 'DAILY_INITIALIZE' and self.game_setting['talkOnFirstDay'] == False:
            # update gameDataFrame
            self.parser.update(game_info, talk_history, whisper_history, request)
            # update pred
            self.predicter_15.update_features(self.parser.get_gamedf_diff())
            self.predicter_15.update_df()
            
        elif self.base_info["day"] == 0 and request == 'DAILY_FINISH' and self.game_setting['talkOnFirstDay'] == False:
            # no talk at day:0
            self.predicter_15.update_pred()
            
        else:
            # update gameDataFrame
            self.parser.update(game_info, talk_history, whisper_history, request)
            # update pred
            self.predicter_15.update(self.parser.get_gamedf_diff())
            
        
        
    def dayStart(self):
        self.vote_declare = 0
        self.talk_turn = 0
        return None
    
    def talk(self):        
        if self.game_setting['playerNum'] == 15:
            
            self.talk_turn += 1
            
            # 1.comingout anyway
            if self.me['myRole'] == 'SEER' and self.comingout == '':
                self.comingout = 'SEER'
                return cb.comingout(self.me['agentIdx'], self.comingout)
            elif self.me['myRole'] == 'MEDIUM' and self.comingout == '':
                self.comingout = 'MEDIUM'
                return cb.comingout(self.me['agentIdx'], self.comingout)
            elif self.me['myRole'] == 'POSSESSED' and self.comingout == '':
                self.comingout = 'SEER'
                return cb.comingout(self.me['agentIdx'], self.comingout)
            
            # 2.report
            if self.me['myRole'] == 'SEER' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.me['myRole'] == 'MEDIUM' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.me['myRole'] == 'POSSESSED' and self.not_reported:
                self.not_reported = False
                # FAKE DIVINE
                # highest prob ww in alive agents
                p = -1
                idx = 1
                p0_mat = self.predicter_15.ret_pred()
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
                self.myresult = 'DIVINED Agent[' + "{0:02d}".format(idx) + '] ' + 'HUMAN'
                return self.myresult
                
            # 3.declare vote if not yet
            if self.vote_declare != self.vote():
                self.vote_declare = self.vote()
                return cb.vote(self.vote_declare)
                
            # 4. skip
            if self.talk_turn <= 10:
                return cb.skip()
                
            return cb.over()
        else:
            return cb.over()
    
    def whisper(self):
        return cb.skip()
        
    def vote(self):
        if self.game_setting['playerNum'] == 15:
            p0_mat = self.predicter_15.ret_pred_wn()
            if self.me['myRole'] == "WEREWOLF":
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if str(i) in self.base_info['roleMap'].keys():
                        p0 *= 0.5
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            elif self.me['myRole'] == "POSSESSED":
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 0]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            else:
                # highest prob ww in alive agents provided watashi ningen
                p = -1
                idx = 1
                for i in range(1, 16):
                    p0 = p0_mat[i-1, 1]
                    if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                        p = p0
                        idx = i
            return idx
        else:
            return 1
    
    def attack(self):
        if self.game_setting['playerNum'] == 15:
            # highest prob hm in alive agents
            p = -1
            idx = 1
            p0_mat = self.predicter_15.ret_pred()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return idx
        else:
            return 1
    
    def divine(self):
        if self.game_setting['playerNum'] == 15:
            # highest prob ww in alive and not divined agents provided watashi ningen
            p = -1
            idx = 1
            p0_mat = self.predicter_15.ret_pred_wn()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 1]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and i not in self.divined_list and p0 > p:
                    p = p0
                    idx = i
            self.divined_list.append(idx)
            return idx
        else:
            return 1
    
    def guard(self):
        if self.game_setting['playerNum'] == 15:
            # highest prob hm in alive agents
            p = -1
            idx = 1
            p0_mat = self.predicter_15.ret_pred()
            for i in range(1, 16):
                p0 = p0_mat[i-1, 0]
                if self.base_info['statusMap'][str(i)] == 'ALIVE' and p0 > p:
                    p = p0
                    idx = i
            return idx
        else:
            return 1
    
    def finish(self):
        pass
        
 

agent = PythonPlayer(myname)

# run
if __name__ == '__main__':
    aiwolfpy.connect(agent)
    