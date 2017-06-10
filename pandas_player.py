#!/usr/bin/env python
from __future__ import print_function, division 

import aiwolfpy
import aiwolfpy.templatetalkfactory as ttf
import aiwolfpy.templatewhisperfactory as twf

import numpy as np
import pandas as pd
import sklearn
import time
import math

class PandasPlayer(object):
    
    def __init__(self, agent_name):
        # me
        self.me = {'agentName':agent_name, 'agentIdx':0, 'myRole':'VILLAGER'}
        # parser
        self.parser = aiwolfpy.PandasParser()
        # self.parser = aiwolfpy.DictParser()
        
        # pattern
        self.case15 = aiwolfpy.Tensor5460()
        
        # num of param
        self.n_para_3d = 6
        self.n_para_2d = 8
        
        # param_linear
        self.para_3d = np.zeros((3, 3, self.n_para_3d))
        l09 = - math.log10(0.9)
        l05 = - math.log10(0.5)
        # werewolf might not vote possessed
        self.para_3d[1, 2, 0] = l05
        # possessed might not vote werewolf
        self.para_3d[2, 1, 0] = l09
        # werewolf would not vote werewolf
        self.para_3d[1, 1, 0] = 1.0
        # possessed might not divine werewolf as werewolf
        self.para_3d[2, 1, 2] = l09
        # werewolf might not divine possessed as werewolf
        self.para_3d[1, 2, 2] = l05
        # werewolf would not divine werewolf as werewolf
        self.para_3d[1, 1, 2] = 1.0
        # village Seer should not tell a lie
        self.para_3d[0, 0, 2] = 2.0
        self.para_3d[0, 2, 2] = 2.0
        self.para_3d[0, 1, 1] = 2.0
        # village Medium should not tell a lie
        self.para_3d[0, 0, 4] = 2.0
        self.para_3d[0, 2, 4] = 2.0
        self.para_3d[0, 1, 3] = 2.0
        # village Bodyguard should not tell a lie
        # self.para_3d[0, 1, 5] = 2.0
        
        
        self.para_2d = np.zeros((3, self.n_para_2d))
        # self.role05 = aaa
        # strategy
        
        
        
        
    def getName(self):
        return self.me['agentName']
    
    def initialize(self, game_info, game_setting):
        # timeit
        self.t_update_max = 0.0
        self.count = 0
        # base
        self.vil_size = game_setting['playerNum']
        self.divined_list = []
        self.alive_list = [i for i in range(1, self.vil_size+1)]
        # me
        self.me['agentIdx'] = game_info['agent']
        self.me['myRole'] =  game_info["roleMap"][str(self.me['agentIdx'])]
        self.comingout = ''
        self.not_reported = False
        # initialize gameDataFrame
        self.parser.initialize(game_info, game_setting)
        self.pd_read = 0
        # initialize x_3d, x_2d
        self.x_3d = np.zeros((15, 15, self.n_para_3d), dtype='float32')
        self.x_2d = np.zeros((15, self.n_para_2d), dtype='float32')
        """
        X_3d
        [i, j, 0] : agent i voted agent j (not in talk, action)
        [i, j, 1] : agent i divined agent j HUMAN
        [i, j, 2] : agent i divined agent j WEREWOLF
        [i, j, 3] : agent i inquested agent j HUMAN
        [i, j, 4] : agent i inquested agent j WEREWOLF
        # [i, j, 5] : agent i managed to guard agent j
        
        X_2d
        [i, 0] : agent i is executed
        [i, 1] : agent i is attacked
        [i, 2] : agent i comingout himself/herself SEER
        [i, 3] : agent i comingout himself/herself MEDIUM
        [i, 4] : agent i comingout himself/herself BODYGUARD
        # [i, 5] : agent i comingout himself/herself VILLAGER
        # [i, 6] : agent i comingout himself/herself POSSESSED
        # [i, 7] : agent i comingout himself/herself WEREWOLF
        """
        
        
    def update(self, game_info, talk_history, whisper_history, request):
        if self.vil_size == 15:
            # timeit
            t = time.time()
            # update gameDataFrame
            self.parser.update(game_info, talk_history, whisper_history, request)
            gamedf = self.parser.gameDataFrame
            # read log
            for i in range(self.pd_read, gamedf.shape[0]):
                # vote
                if gamedf.type[i] == 'vote' and gamedf.turn[i] == 0:
                    self.x_3d[gamedf.idx[i] - 1, gamedf.agent[i] - 1, 0] += 1
                # execute
                elif gamedf.type[i] == 'execute':
                    self.x_2d[gamedf.agent[i] - 1, 0] = 1
                    if gamedf.agent[i] in self.alive_list:
                        self.alive_list.remove(gamedf.agent[i])
                # attacked
                elif gamedf.type[i] == 'dead':
                    self.x_2d[gamedf.agent[i] - 1, 1] = 1
                    if gamedf.agent[i] in self.alive_list:
                        self.alive_list.remove(gamedf.agent[i])
                # talk
                elif gamedf.type[i] == 'talk':
                    content = gamedf.text[i].split()
                    # comingout
                    if content[0] == 'COMINGOUT':
                        # self
                        if int(content[1][6:8]) == gamedf.agent[i]:
                            if content[2] == 'SEER':
                                self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                                self.x_2d[gamedf.agent[i] - 1, 2] = 0
                            elif content[2] == 'MEDIUM':
                                self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                                self.x_2d[gamedf.agent[i] - 1, 3] = 0
                            elif content[2] == 'BODYGUARD':
                                self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                                self.x_2d[gamedf.agent[i] - 1, 4] = 0
                    # divined
                    elif content[0] == 'DIVINED':
                        # regard comingout
                        self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                        self.x_2d[gamedf.agent[i] - 1, 2] = 0
                        # result
                        if content[2] == 'HUMAN':
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 1] = 1
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 2] = 0
                        elif content[2] == 'WEREWOLF':
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 2] = 1
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 1] = 0
                    # identified
                    elif content[0] == 'IDENTIFIED':
                        # regard comingout
                        self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                        self.x_2d[gamedf.agent[i] - 1, 3] = 0
                        # result
                        if content[2] == 'HUMAN':
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 3] = 1
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 4] = 0
                        elif content[2] == 'WEREWOLF':
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 4] = 1
                            self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 3] = 0
                
                # my information
                elif gamedf.type[i] == 'divine':
                    self.not_reported = True
                    self.myresult = gamedf.text[i]
                elif gamedf.type[i] == 'identify':
                    self.not_reported = True
                    self.myresult = gamedf.text[i]
                    
                
            
            # update row
            self.pd_read = self.parser.gameDataFrame.shape[0]
            
            # update 5460 dataframe
            self.df_pred = self.case15.apply_tensor_df(self.x_3d, self.x_2d, 
                                                       names_3d=["VOTE", "DIV_HM", "DIV_WW", "IDT_HM", "IDT_WW", "GUARDED"], 
                                                       names_2d=['executed', 'attacked', 'CO_SEER', 'CO_MEDIUM', 'CO_BODYGUARD', 'CO_VILLAGER', 'CO_POSSESSED', 'CO_WEREWOLF'])
            
            
            # predict
            # Linear
            l_para = np.append(self.para_3d.reshape((3*3*self.n_para_3d, 1)), self.para_2d.reshape((3*self.n_para_2d, 1)))
            self.df_pred["pred"] = np.matmul(self.df_pred, l_para.reshape(-1, 1))
            
            # If-then rules 1
            # village Seer would comingout
            self.df_pred.loc[(self.df_pred["CO_SEER_W"] + self.df_pred["CO_SEER_P"] > 0) & (self.df_pred["CO_SEER_H"] == 0), "pred"] += 2.0
            # village Medium would comingout
            self.df_pred.loc[(self.df_pred["CO_MEDIUM_W"] + self.df_pred["CO_MEDIUM_P"] > 0) & (self.df_pred["CO_MEDIUM_H"] == 0), "pred"] += 2.0
            # village Bodyguard would comingout
            # self.df_pred.loc[self.df_pred["CO_BODYGUARD_W"] + self.df_pred["CO_BODYGUARD_P"] > 0 & self.df_pred["CO_BODYGUARD_H"] == 0 , "pred"] += 1.0
            # possessed would comingout
            self.df_pred.loc[self.df_pred["CO_SEER_P"] + self.df_pred["CO_MEDIUM_P"] + self.df_pred["CO_BODYGUARD_P"] == 0, "pred"] += 1.0
            # werewolves might not comingout
            self.df_pred.loc[self.df_pred["CO_SEER_W"] + self.df_pred["CO_MEDIUM_W"] + self.df_pred["CO_BODYGUARD_W"] >  1, "pred"] += 2.0
            self.df_pred.loc[self.df_pred["CO_SEER_W"] + self.df_pred["CO_MEDIUM_W"] + self.df_pred["CO_BODYGUARD_W"] >  2, "pred"] += 5.0
            # villagers must not comingout
            self.df_pred.loc[self.df_pred["CO_SEER_H"] > 1, "pred"] += 3.0
            self.df_pred.loc[self.df_pred["CO_MEDIUM_H"] > 1, "pred"] += 3.0
            self.df_pred.loc[self.df_pred["CO_BODYGUARD_H"] > 1, "pred"] += 3.0
            
            self.df_pred["pred"] = np.exp(self.df_pred["pred"])
            
            # werewolves are never to be attacked
            self.df_pred.loc[self.df_pred["attacked_W"] > 0, "pred"] *= 0.0
            # game is going on, there's at least one werewolf
            self.df_pred.loc[self.df_pred["executed_W"] >= 3.0, "pred"] *= 0.0
            # game is going on, humans > wolves
            n_alive = len(self.alive_list)
            self.df_pred.loc[3.0 - self.df_pred["executed_W"] >= n_alive / 2.0, "pred"] *= 0.0
            # average
            self.df_pred["pred"] /= self.df_pred["pred"].sum()
            # watashi ningen
            self.df_pred["pred_wn"] = self.df_pred["pred"]
            self.df_pred.loc[self.case15.get_case5460_df()["agent_"+str(self.me['agentIdx'])] != 0, "pred_wn"] *= 0.0
            self.df_pred["pred_wn"] /= self.df_pred["pred_wn"].sum()
            
            # matrix(15, 3)
            # for village
            self.pred_mat = np.tensordot(self.case15.get_case5460_2d(), self.df_pred["pred"], axes = [0, 0]).transpose()
            # watashi ningen
            self.pred_mat_wn = np.tensordot(self.case15.get_case5460_2d(), self.df_pred["pred_wn"], axes = [0, 0]).transpose()
            
            # timeit
            self.t_update_max = max(self.t_update_max, time.time()-t)
            
        
    def dayStart(self):
        return None
    
    def talk(self):        
        if self.vil_size == 15:
            # 1.comingout anyway
            if self.me['myRole'] == 'SEER' and self.comingout == '':
                self.comingout = 'SEER'
                return ttf.comingout(self.me['agentIdx'], self.comingout)
            elif self.me['myRole'] == 'MEDIUM' and self.comingout == '':
                self.comingout = 'MEDIUM'
                return ttf.comingout(self.me['agentIdx'], self.comingout)
            # elif self.me['myRole'] == 'POSSESSED' and self.comingout == '':
            #     self.comingout = 'SEER'
            #     return ttf.comingout(self.agentIdx, self.comingout)
            
            # 2.report
            if self.me['myRole'] == 'SEER' and self.not_reported:
                self.not_reported = False
                return self.myresult
            elif self.me['myRole'] == 'MEDIUM' and self.not_reported:
                self.not_reported = False
                return self.myresult
            # elif self.me['myRole'] == 'POSSESSED' and self.not_reported:
            #     self.not_reported = False
            #     return ttf.divined(self.divine_result[0], self.divine_result[1])
                
            # 3.declare vote if not yet
            # elif self.day > 0 and self.vote_declare != self._vote_target():
            #     self.vote_declare = self._vote_target()
            #     return ttf.vote(self.vote_declare)
                
            return ttf.over()
        else:
            return ttf.over()
    
    def whisper(self):
        return twf.skip()
        
    def vote(self):
        if self.vil_size == 15:
            # highest prob ww in alive agents provided watashi ningen
            p = -1
            idx = 1
            for i in range(1, 16):
                if i in self.alive_list and self.pred_mat_wn[i-1, 1] > p:
                    p = self.pred_mat_wn[i-1, 1]
                    idx = i
            ### TODO ###
            # possessed and werewolf
            return idx
        else:
            return 1
    
    def attack(self):
        return 1
    
    def divine(self):
        if self.vil_size == 15:
            # highest prob ww in alive and not divined agents provided watashi ningen
            p = -1
            idx = 1
            for i in range(1, 16):
                if i in self.alive_list and i not in self.divined_list and self.pred_mat_wn[i-1, 1] > p:
                    p = self.pred_mat_wn[i-1, 1]
                    idx = i
            self.divined_list.append(idx)
            return idx
        else:
            return 1
    
    def guard(self):
        if self.vil_size == 15:
            # highest prob hm in alive agents
            p = -1
            idx = 1
            for i in range(1, 16):
                if i in self.alive_list and self.pred_mat[i-1, 0] > p:
                    p = self.pred_mat_wn[i-1, 1]
                    idx = i
            return idx
        else:
            return 1
    
    def finish(self):
        if self.vil_size == 15:
            self.count += 1
            if self.count == 2:
                print(self.t_update_max)
        return None
        
 

agent = PandasPlayer('cash')

# run
if __name__ == '__main__':
    aiwolfpy.connect(agent)
    