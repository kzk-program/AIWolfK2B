from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractRequestProcessingModule,AbstractStrategyModule,OneStepPlan,ActionType

class SimpleRequestProcessingModule(AbstractRequestProcessingModule):
    """要求が来た場合、テキトーなことをいうモジュール"""
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config,role_estimation_model,strategy_module)
        
    def process_request(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        plan = OneStepPlan("なんとなく",ActionType.TALK,"お前には従わない")
        return plan