from __future__ import print_function, division 
import numpy as np
import pandas as pd



class Tensor60(object):
    
    def __init__(self):
        # using float (to call BLAS) is much faster than to use int
        self.tensor60_3d = np.zeros((60, 4, 4, 5, 5), dtype='float32')
        self.tensor60_2d = np.zeros((60, 4, 5), dtype='float32')
        
        self.case60 = np.zeros((60, 5), dtype='int32')
        
        # 0 : villager
        # 1 : werewolves
        # 2 : possessed
        # 3 : seer
        
        ind = 0
        # case5460
        for w in range(5):
            for p in range(5):
                for s in range(5):
                    if w != p and p != s and s != w:
                        self.case60[ind, w] = 1
                        self.case60[ind, p] = 2
                        self.case60[ind, s] = 3
                        ind += 1
        
        self.case60_df = pd.DataFrame(self.case60)
        self.case60_df.columns = ["agent_" + str(i) for i in range(1, 6)]
        
        
        # tensor5460_3d
        for ind in range(60):
            for i in range(5):
                for j in range(5):
                    self.tensor60_3d[ind, self.case60[ind, i], self.case60[ind, j], i, j] = 1.0
        
        # tensor5460_2d
        for ind in range(60):
            for i in range(5):
                self.tensor60_2d[ind, self.case60[ind, i], i] = 1.0
    
    
    def get_case60(self):
        return self.case60
            
    def get_case60_df(self):
        return self.case60_df
        
    def get_case60_2d(self):
        return self.tensor60_2d
        
        
    def apply_tensor_3d(self, x_3d):
        # x_3d : np.ndarry of shape (5, 5, k)
        # returns np.ndarry of shape (60, 4, 4, k)
        return np.tensordot(self.tensor60_3d, x_3d, axes=[[3,4], [0,1]])
        
        
    def apply_tensor_2d(self, x_2d):
        # x_2d : np.ndarry of shape (5, k)
        # returns np.ndarry of shape (60, 4, k)
        return np.matmul(self.tensor60_2d, x_2d)
        
        
    def apply_tensor_df(self, x_3d, x_2d, names_3d=['f3_0'], names_2d=['f2_0']):
        if len(names_3d) != x_3d.shape[2]:
            names_3d = ['f3_'+str(i) for i in range(x_3d.shape[2])]
        if len(names_2d) != x_2d.shape[1]:
            names_2d = ['f2_'+str(i) for i in range(x_2d.shape[1])]
            
        collected_df = pd.DataFrame(np.concatenate((self.apply_tensor_3d(x_3d).reshape((60, -1)), 
                            self.apply_tensor_2d(x_2d).reshape((60, -1))), axis=1))
        
        # set names
        collected_df.columns = [x+y+z for y in ["_V", "_W", "_P", "_S"] for z in ["V", "W", "P", "S"] for x in names_3d] + [x+y for y in ["_H", "_W", "_P", "_S"] for x in names_2d]
        return collected_df
        
        
