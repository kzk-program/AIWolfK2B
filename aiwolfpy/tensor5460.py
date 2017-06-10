from __future__ import print_function, division 
import numpy as np
import pandas as pd



class Tensor5460(object):
    
    def __init__(self):
        # using float (to call BLAS) is much faster than to use int
        self.tensor5460_3d = np.zeros((5460, 3, 3, 15, 15), dtype='float32')
        self.tensor5460_2d = np.zeros((5460, 3, 15), dtype='float32')
        
        self.case5460 = np.zeros((5460, 15), dtype='int32')
        
        # 0 : villagers
        # 1 : werewolves
        # 2 : possessed
        
        ind = 0
        # case5460
        for w1 in range(13):
            for w2 in range(w1+1, 14):
                for w3 in range(w2+1, 15):
                    for p in range(15):
                        if p not in [w1, w2, w3]:
                            self.case5460[ind, p] = 2
                            self.case5460[ind, [w1, w2, w3]] = 1
                            ind += 1
        
        self.case5460_df = pd.DataFrame(self.case5460)
        self.case5460_df.columns = ["agent_" + str(i) for i in range(1, 16)]
        
        
        # tensor5460_3d
        for ind in range(5460):
            for i in range(15):
                for j in range(15):
                    self.tensor5460_3d[ind, self.case5460[ind, i], self.case5460[ind, j], i, j] = 1.0
        
        # tensor5460_2d
        for ind in range(5460):
            for i in range(15):
                self.tensor5460_2d[ind, self.case5460[ind, i], i] = 1.0
    
    
    def get_case5460(self):
        return self.case5460
            
    def get_case5460_df(self):
        return self.case5460_df
        
    def get_case5460_2d(self):
        return self.tensor5460_2d
        
        
    def apply_tensor_3d(self, x_3d):
        # x_3d : np.ndarry of shape (15, 15, k)
        # returns np.ndarry of shape (5460, 3, 3, k)
        return np.tensordot(self.tensor5460_3d, x_3d, axes=[[3,4], [0,1]])
        
        
    def apply_tensor_2d(self, x_2d):
        # x_2d : np.ndarry of shape (15, k)
        # returns np.ndarry of shape (5460, 3, k)
        return np.matmul(self.tensor5460_2d, x_2d)
        
        
    def apply_tensor_df(self, x_3d, x_2d, names_3d=['f3_0'], names_2d=['f2_0']):
        if len(names_3d) != x_3d.shape[2]:
            names_3d = ['f3_'+str(i) for i in range(x_3d.shape[2])]
        if len(names_2d) != x_2d.shape[1]:
            names_2d = ['f2_'+str(i) for i in range(x_2d.shape[1])]
            
        collected_df = pd.DataFrame(np.concatenate((self.apply_tensor_3d(x_3d).reshape((5460, -1)), 
                            self.apply_tensor_2d(x_2d).reshape((5460, -1))), axis=1))
        
        # set names
        collected_df.columns = [x+y+z for y in ["_H", "_W", "_P"] for z in ["H", "W", "P"] for x in names_3d] + [x+y for y in ["_H", "_W", "_P"] for x in names_2d]
        return collected_df
        
        
