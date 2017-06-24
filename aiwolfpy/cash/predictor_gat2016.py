from .tensor5460 import Tensor5460
import numpy as np
import math

class Predictor_15(object):
    
    def __init__(self):
        self.x = 100
        self.case15 = Tensor5460()

        # num of param
        self.n_para_3d = 5
        self.n_para_2d = 5
        
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
        
        self.x_3d = np.zeros((15, 15, self.n_para_3d), dtype='float32')
        self.x_2d = np.zeros((15, self.n_para_2d), dtype='float32')
        
                
    def initialize(self, base_info, game_setting):
        # game_setting
        self.game_setting = game_setting
        
        # base_info
        self.base_info = base_info
        
        # initialize watashi_ningen
        self.watshi_ningen = np.ones(5460)
        xv = self.case15.get_case5460_df()["agent_"+str(self.base_info['agentIdx'])].values
        self.watshi_ningen[xv != 0] = 0.0
        
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
        
    def update(self, gamedf):
        self.update_features(gamedf)
        self.update_df()
        self.update_pred()
        # self.mod_pred()
        
    def update_features(self, gamedf):
        # read log
        for i in range(gamedf.shape[0]):
            # vote
            if gamedf.type[i] == 'vote' and gamedf.turn[i] == 0:
                self.x_3d[gamedf.idx[i] - 1, gamedf.agent[i] - 1, 0] += 1
            # execute
            elif gamedf.type[i] == 'execute':
                self.x_2d[gamedf.agent[i] - 1, 0] = 1
            # attacked
            elif gamedf.type[i] == 'dead':
                self.x_2d[gamedf.agent[i] - 1, 1] = 1
            # talk
            elif gamedf.type[i] == 'talk':
                content = gamedf.text[i].split()
                # comingout
                if content[0] == 'COMINGOUT':
                    # self
                    if int(content[1][6:8]) == gamedf.agent[i]:
                        if content[2] == 'SEER':
                            self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                            self.x_2d[gamedf.agent[i] - 1, 2] = 1
                        elif content[2] == 'MEDIUM':
                            self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                            self.x_2d[gamedf.agent[i] - 1, 3] = 1
                        elif content[2] == 'BODYGUARD':
                            self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                            self.x_2d[gamedf.agent[i] - 1, 4] = 1
                # divined
                elif content[0] == 'DIVINED':
                    # regard comingout
                    self.x_2d[gamedf.agent[i] - 1, 2:5] = 0
                    self.x_2d[gamedf.agent[i] - 1, 2] = 1
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
                    self.x_2d[gamedf.agent[i] - 1, 3] = 1
                    # result
                    if content[2] == 'HUMAN':
                        self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 3] = 1
                        self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 4] = 0
                    elif content[2] == 'WEREWOLF':
                        self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 4] = 1
                        self.x_3d[gamedf.agent[i] - 1, int(content[1][6:8])-1, 3] = 0
        
    def update_df(self):
        # update 5460 dataframe
        self.df_pred = self.case15.apply_tensor_df(self.x_3d, self.x_2d, 
                                                   names_3d=["VOTE", "DIV_HM", "DIV_WW", "IDT_HM", "IDT_WW"], 
                                                   names_2d=['executed', 'attacked', 'CO_SEER', 'CO_MEDIUM', 'CO_BODYGUARD'])
        
    
    def update_pred(self):
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
        
        self.df_pred["pred"] = np.exp(-np.log(10)*self.df_pred["pred"])
        
        # werewolves are never to be attacked
        self.df_pred.loc[self.df_pred["attacked_W"] > 0.0, "pred"] *= 0.0
        # game is going on, there's at least one werewolf
        self.df_pred.loc[self.df_pred["executed_W"] >= 3.0, "pred"] *= 0.0
        # game is going on, humans > wolves
        n_alive = self.game_setting['playerNum'] - self.x_2d[:, :2].sum()
        self.df_pred.loc[3.0 - self.df_pred["executed_W"] >= n_alive / 2.0, "pred"] *= 0.0
        # average
        self.p_5460 = self.df_pred["pred"] / self.df_pred["pred"].sum()
        
    def mod_pred(self):
        # watashi ningen
        self.df_pred["pred_wn"] = self.df_pred["pred"]
        self.df_pred.loc[self.case15.get_case5460_df()["agent_"+str(self.base_info['agentIdx'])] != 0, "pred_wn"] *= 0.0
        self.df_pred["pred_wn"] /= self.df_pred["pred_wn"].sum()
        # for werewolves
        self.df_pred["pred_ww"] = self.df_pred["pred"]
        if self.base_info['myRole'] == "WEREWOLF": 
            for i in self.base_info['roleMap'].keys():
                self.df_pred.loc[self.case15.get_case5460_df()["agent_"+i] != 0, "pred_ww"] *= 0.0
            self.df_pred["pred_ww"] /= self.df_pred["pred_ww"].sum()
        # matrix(15, 3)
        # for village
        self.pred_mat = np.tensordot(self.case15.get_case5460_2d(), self.df_pred["pred"], axes = [0, 0]).transpose()
        # watashi ningen
        self.pred_mat_wn = np.tensordot(self.case15.get_case5460_2d(), self.df_pred["pred_wn"], axes = [0, 0]).transpose()
        # for werewolves
        self.pred_mat_ww = np.tensordot(self.case15.get_case5460_2d(), self.df_pred["pred_ww"], axes = [0, 0]).transpose()
        
        
        
    def ret_pred(self):
        p = self.p_5460
        return np.tensordot(self.case15.get_case5460_2d(), p / p.sum(), axes = [0, 0]).transpose()
        
    def ret_pred_wn(self):
        p = self.p_5460 * self.watshi_ningen
        return np.tensordot(self.case15.get_case5460_2d(), p / p.sum(), axes = [0, 0]).transpose()


        