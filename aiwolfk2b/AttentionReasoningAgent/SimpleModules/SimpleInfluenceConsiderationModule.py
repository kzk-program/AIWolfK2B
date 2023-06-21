from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractInfluenceConsiderationModule,AbstractRequestProcessingModule,OneStepPlan,AbstractQuestionProcessingModule

import random

class SimpleInfluenceConsiderationModule(AbstractInfluenceConsiderationModule):
    """他者から自分への投げかけがあるかをテキトーに判定して、テキトーなことをいうモジュール"""
    def __init__(self, config: ConfigParser,request_processing_module:AbstractRequestProcessingModule, question_processing_module:AbstractQuestionProcessingModule) -> None:
        super().__init__(config,request_processing_module,question_processing_module)
        
    def check_influence(self, game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool,OneStepPlan]:
        """ランダムに投げかけありと判定して、テキトーなことをいう"""
        has_influence = random.random() > 0.5
        if has_influence:
            """要求か質問のどちらかをランダムに選ぶ"""
            is_request = random.random() > 0.5 or True
            if is_request:
                plan = self.request_processing_module.process_request(game_info, game_setting)
            else:
                plan = self.question_processing_module.process_question(game_info, game_setting)
            return has_influence,plan
        else:
            return has_influence,None