from .tensor60 import Tensor60
import numpy as np
import math

class Predictor_5(object):
    
    def __init__(self):
        self.case5 = Tensor60()
        
        # num of param
        self.n_para_3d = 3
        self.n_para_2d = 8
        
        # param_linear
        self.para_3d = np.zeros((4, 4, self.n_para_3d))
        l09 = - math.log10(0.9)
        l05 = - math.log10(0.5)
        # werewolf might not vote possessed
        self.para_3d[1, 2, 0] = l05
        # possessed might not vote werewolf
        self.para_3d[2, 1, 0] = l09
        # possessed might not divine werewolf as werewolf
        self.para_3d[2, 1, 2] = l09
        # werewolf might not divine possessed as werewolf
        self.para_3d[1, 2, 2] = l05
        # werewolf would not divine werewolf as werewolf
        self.para_3d[1, 1, 2] = 1.0
        # Seer should not tell a lie
        self.para_3d[3, 0, 2] = 2.0
        self.para_3d[3, 2, 2] = 2.0
        self.para_3d[3, 1, 1] = 2.0
        
        self.para_2d = np.zeros((4, self.n_para_2d))
        # Seer should comingout correctly
        self.para_2d[3, 2] = -2.0
        self.para_2d[3, 5] = 2.0
        self.para_2d[3, 6] = 2.0
        # Possessed should comingout
        self.para_2d[2, 2] = -2.0
        self.para_2d[2, 6] = -1.0
        # villagers must not comingout
        self.para_2d[0, 2] = -2.0
        self.para_2d[0, 6] = -1.0
        # werewolf is alive
        self.para_2d[1, 0] = 100.0
        self.para_2d[1, 1] = 100.0
        
        self.x_3d = np.zeros((5, 5, self.n_para_3d), dtype='float32')
        self.x_2d = np.zeros((5, self.n_para_2d), dtype='float32')
        
                
    def initialize(self, base_info, game_setting):
        # game_setting
        self.game_setting = game_setting
        
        # base_info
        self.base_info = base_info
        
        # initialize watashi_xxx
        self.watshi_xxx = np.ones((60, 4))
        xv = self.case5.get_case60_df()["agent_"+str(self.base_info['agentIdx'])].values
        self.watshi_xxx[xv != 0, 0] = 0.0
        self.watshi_xxx[xv != 1, 1] = 0.0
        self.watshi_xxx[xv != 2, 2] = 0.0
        self.watshi_xxx[xv != 3, 3] = 0.0
        
        # initialize x_3d, x_2d
        self.x_3d = np.zeros((5, 5, self.n_para_3d), dtype='float32')
        self.x_2d = np.zeros((5, self.n_para_2d), dtype='float32')
        
        
        """
        X_3d
        [i, j, 0] : agent i voted agent j (not in talk, action)
        [i, j, 1] : agent i divined agent j HUMAN
        [i, j, 2] : agent i divined agent j WEREWOLF
        
        X_2d
        [i, 0] : agent i is executed
        [i, 1] : agent i is attacked
        [i, 2] : agent i comingout himself/herself SEER
        [i, 3] : agent i comingout himself/herself MEDIUM
        [i, 4] : agent i comingout himself/herself BODYGUARD
        [i, 5] : agent i comingout himself/herself VILLAGER
        [i, 6] : agent i comingout himself/herself POSSESSED
        [i, 7] : agent i comingout himself/herself WEREWOLF
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
                            self.x_2d[gamedf.agent[i] - 1, 2:8] = 0
                            self.x_2d[gamedf.agent[i] - 1, 2] = 1
                        elif content[2] == 'MEDIUM':
                            self.x_2d[gamedf.agent[i] - 1, 2:8] = 0
                            self.x_2d[gamedf.agent[i] - 1, 3] = 1
                        elif content[2] == 'BODYGUARD':
                            self.x_2d[gamedf.agent[i] - 1, 2:8] = 0
                            self.x_2d[gamedf.agent[i] - 1, 4] = 1
                        elif content[2] == 'VILLAGER':
                            self.x_2d[gamedf.agent[i] - 1, 2:8] = 0
                            self.x_2d[gamedf.agent[i] - 1, 5] = 1
                        elif content[2] == 'POSSESSED':
                            self.x_2d[gamedf.agent[i] - 1, 2:8] = 0
                            self.x_2d[gamedf.agent[i] - 1, 6] = 1
                        elif content[2] == 'WEREWOLF':
                            self.x_2d[gamedf.agent[i] - 1, 2:8] = 0
                            self.x_2d[gamedf.agent[i] - 1, 7] = 1
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
                        
        
    def update_df(self):
        # update 60 dataframe
        self.df_pred = self.case5.apply_tensor_df(self.x_3d, self.x_2d, 
                                                   names_3d=["VOTE", "DIV_HM", "DIV_WW"], 
                                                   names_2d=['executed', 'attacked', 'CO_SEER', 'CO_MEDIUM', 'CO_BODYGUARD', 'CO_VILLAGER', 'CO_POSSESSED', 'CO_WEREWOLF'])
        
    
    def update_pred(self):
        # predict
        # Linear
        l_para = np.append(self.para_3d.reshape((4*4*self.n_para_3d, 1)), self.para_2d.reshape((4*self.n_para_2d, 1)))
        self.df_pred["pred"] = np.matmul(self.df_pred, l_para.reshape(-1, 1))        
        self.df_pred["pred"] = np.exp(-np.log(10)*self.df_pred["pred"])
        
        # average
        self.p_60 = self.df_pred["pred"] / self.df_pred["pred"].sum()
        
        
    def ret_pred(self):
        p = self.p_60
        return np.tensordot(self.case5.get_case60_2d(), p / p.sum(), axes = [0, 0]).transpose()
        
    def ret_pred_wx(self, r):
        p = self.p_60 * self.watshi_xxx[:, r]
        return np.tensordot(self.case5.get_case60_2d(), p / p.sum(), axes = [0, 0]).transpose()


        
