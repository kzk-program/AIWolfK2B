from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractStrategyModule,AbstractRoleInferenceModule,RoleInferenceResult,OneStepPlan,ActionType

import random

class SimpleStrategyModule(AbstractStrategyModule):
    """最も人狼の確率が高いエージェントを釣る・占う戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config,role_estimation_model,role_inference_module)
        self.history = []
        self.future_plan = []
        self.next_plan = None

    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        talk_plan = OneStepPlan("サンプルだから",ActionType.TALK,"何も言うことはない(from strategy module)")
        return talk_plan
    
    def vote(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """最も人狼の確率が高いエージェントに投票する"""
        #各エージェントの役職を推定する
        inf_results:List[RoleInferenceResult] = []
        for a in game_info.agent_list:
            inf_results.append(self.role_inference_module.infer(a, [game_info], game_setting))
        #エージェントの中から最も人狼の確率が高いエージェントを選ぶ
        max_wolf_prob = 0
        max_wolf_agent = None
        for inf_result in inf_results:
            if inf_result.probs[Role.WEREWOLF] > max_wolf_prob:
                max_wolf_prob = inf_result.probs[Role.WEREWOLF]
                max_wolf_agent = inf_result.agent
                
        #最も人狼の確率が高いエージェントに投票する
        vote_plan = OneStepPlan("最も人狼っぽかったから",ActionType.VOTE,max_wolf_agent)
        
        return vote_plan
    
    def attack(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """ランダムに襲撃する"""
        attack_plan = OneStepPlan("なんとなく決めたから",ActionType.ATTACK,random.choice(game_info.agent_list))
        return attack_plan
    
    def divine(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """ランダムに占う"""
        divine_plan = OneStepPlan("なんとなく決めたから",ActionType.DIVINE,random.choice(game_info.agent_list))
        return divine_plan
    
    def guard(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """ランダムに護衛する"""
        guard_plan = OneStepPlan("なんとなく決めたから",ActionType.GUARD,random.choice(game_info.agent_list))
        return guard_plan
    
    def whisper(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        whisper_plan = OneStepPlan("サンプルだから",ActionType.WHISPER,"何も言うことはない(from strategy module)")
        
        return whisper_plan
        
    def plan(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        pass

    def update_history(self, game_info: GameInfo, game_setting: GameSetting, executed_plan: OneStepPlan) -> None:
        return super().update_history(game_info, game_setting, executed_plan)
    
    def update_future_plan(self, game_info: GameInfo, game_setting: GameSetting, executed_plan: OneStepPlan) -> None:
        return super().update_future_plan(game_info, game_setting, executed_plan)