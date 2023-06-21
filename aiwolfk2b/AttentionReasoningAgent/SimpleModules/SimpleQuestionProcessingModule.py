from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleInferenceModule,AbstractStrategyModule,OneStepPlan,ActionType,AbstractQuestionProcessingModule


class SimpleQuestionProcessingModule(AbstractQuestionProcessingModule):
    """質問が来た場合、テキトーなことをいうモジュール"""
    def __init__(self, config: ConfigParser, role_inference_module: AbstractRoleInferenceModule, strategy_module: AbstractStrategyModule) -> None:
        super().__init__(config, role_inference_module, strategy_module)
        
    def process_question(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        plan = OneStepPlan("なんとなく",ActionType.TALK,"なんとなく")
        return plan
    