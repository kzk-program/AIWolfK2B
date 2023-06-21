from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractStrategyModule,AbstractRoleInferenceModule,RoleInferenceResult,OneStepPlan

import random

class SimpleStrategyModule(AbstractStrategyModule):
    """最も人狼の確率が高いエージェントを釣る・占う戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config,role_estimation_model,role_inference_module)
        self.history = []
        self.future_plan = []
        self.next_plan = None

    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        return "何も言うことはない(from strategy module)"
    
    def vote(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """最も人狼の確率が高いエージェントに投票する"""
        #各エージェントの役職を推定する
        inf_results:List[RoleInferenceResult] = []
        for a in game_info.agent_list:
            inf_results.append(self.role_inference_module.infer(a, game_info, game_setting))
        #エージェントの中から最も人狼の確率が高いエージェントを選ぶ
        max_wolf_prob = 0
        max_wolf_agent = None
        for inf_result in inf_results:
            if inf_result.probs[Role.WEREWOLF] > max_wolf_prob:
                max_wolf_prob = inf_result.probs[Role.WEREWOLF]
                max_wolf_agent = inf_result.agent
                
        #最も人狼の確率が高いエージェントに投票する
        return max_wolf_agent
    
    def attack(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """ランダムに襲撃する"""
        return random.choice(game_info.agent_list)
    
    def divine(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """ランダムに占う"""
        return random.choice(game_info.agent_list)
    
    def guard(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """ランダムに護衛する"""
        return random.choice(game_info.agent_list)
    
    def whisper(self, game_info: GameInfo, game_setting: GameSetting) -> str:
        return "何も言うことはない"
        
    def plan(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        pass

    def update_history(self, game_info: GameInfo, game_setting: GameSetting, executed_plan: OneStepPlan) -> None:
        return super().update_history(game_info, game_setting, executed_plan)
    
    def update_future_plan(self, game_info: GameInfo, game_setting: GameSetting, executed_plan: OneStepPlan) -> None:
        return super().update_future_plan(game_info, game_setting, executed_plan)