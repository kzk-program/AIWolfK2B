from configparser import ConfigParser
from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent
from AbstractModules import *
import random
import math

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleInferenceModule, AbstractStrategyModule, OneStepPlan


class RandomRoleEstimationModel(AbstractRoleEstimationModel):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        
    def estimate(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleEstimateResult:
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
            
        return RoleEstimateResult(agent,estimation,None)
    
class SimpleRoleInferenceModule(AbstractRoleInferenceModule):
    """推論モデルを鵜呑みにする役職推論モジュール"""
    def __init__(self,config:ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        super().__init__(config,role_estimation_model)
    
    def infer(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleInferenceResult:
        """推論モデルを鵜呑みにする役職推論"""
        result = self.role_estimation_model.estimate(agent, game_info, game_setting)
        return RoleInferenceResult(agent=agent,reason="推論モデルがそう言っていたから",result=result.probs)

class SimpleStrategyModule(AbstractStrategyModule):
    """最も人狼の確率が高いエージェントを釣る・占う戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config,role_estimation_model,role_inference_module)
        self.history = []
        self.future_plan = []
        self.next_plan = None

    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        return "何も言うことはない"
    
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
    

class SimpleRequestProcessingModule(AbstractRequestProcessingModule):
    """要求が来た場合、テキトーなことをいうモジュール"""
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config,role_estimation_model,strategy_module)
        
    def process_request(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        plan = OneStepPlan("なんとなく",ActionType.TALK,"お前には従わない")
        return plan
    
    
class SimpleQuestionProcessingModule(AbstractQuestionProcessingModule):
    """質問が来た場合、テキトーなことをいうモジュール"""
    def __init__(self, config: ConfigParser, role_inference_module: AbstractRoleInferenceModule, strategy_module: AbstractStrategyModule) -> None:
        super().__init__(config, role_inference_module, strategy_module)
        
    def process_question(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        plan = OneStepPlan("なんとなく",ActionType.TALK,"なんとなく")
        return plan
    
    
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
        
class SimpleSpeakerModule(AbstractSpeakerModule):
    """そのまま喋るモジュール"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
    
    def enhance_speech(self,speech:str) -> str:
        return speech
        