from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,RoleEstimationResult

import random
import math

class RandomRoleEstimationModel(AbstractRoleEstimationModel):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        
    def estimate(self,agent:Agent, game_info_list: List[GameInfo], game_setting: GameSetting) -> RoleEstimationResult:
        """ランダムに役職を推定する"""
        #１人以上存在する役職のリスト
        role_list = [role for role in game_setting.role_num_map.keys() if game_setting.role_num_map[role] > 0]
        estimation = {}
        scores = {}
        for role in role_list:
            scores[role] = 10*random.random() -5.0
            
        #ソフトマックス関数で正規化
        sum_exp = sum([math.exp(v) for v in scores.values()])
        for role in role_list:
            estimation[role] = math.exp(scores[role])/sum_exp
            
        return RoleEstimationResult(agent,estimation,None)