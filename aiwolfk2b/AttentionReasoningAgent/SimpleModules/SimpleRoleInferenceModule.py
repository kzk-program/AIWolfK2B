from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleInferenceModule, AbstractRoleEstimationModel,RoleInferenceResult

class SimpleRoleInferenceModule(AbstractRoleInferenceModule):
    """推論モデルを鵜呑みにする役職推論モジュール"""
    def __init__(self,config:ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        super().__init__(config,role_estimation_model)
    
    def infer(self,agent:Agent, game_info_list: List[GameInfo], game_setting: GameSetting) -> RoleInferenceResult:
        """推論モデルを鵜呑みにする役職推論"""
        result = self.role_estimation_model.estimate(agent, game_info_list, game_setting)
        return RoleInferenceResult(agent=agent,reason="推論モデルがそう言っていたから",result=result.probs)
