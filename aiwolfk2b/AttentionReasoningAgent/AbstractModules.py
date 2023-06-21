from abc import ABC, abstractmethod
from typing import List,Tuple,Dict,Any,Union
from typing import TypedDict
from enum import Enum
import configparser
from configparser import ConfigParser


from aiwolf import GameInfo,GameSetting,Content
from aiwolf.agent import Agent,Role


class RoleEstimateResult:
    """役職推定結果を保持するクラス"""
    agent: Agent
    """推定対象のエージェント"""
    probs: Dict[Role,float]
    """推定結果(キー：役職、値：その役職の確率とした辞書)"""
    attention_map: Any
    """アテンションマップ"""
    
    def __init__(self,agent:Agent, result:Dict[Role,float],attention_map:Any):
        self.agent = agent
        self.probs = result
        self.attention_map = attention_map
        
    def __str__(self) -> str:
        return self.agent + "is " + str(self.probs) + "\nattention_map: " + str(self.attention_map)

    
class RoleInferenceResult:
    """役職推論結果を保持するクラス"""
    agent: Agent
    """推論対象のエージェント"""
    reason: str
    """推論結果に至った理由"""
    probs: Dict[Role,float]
    """推論結果(キー：役職、値：その役職の確率とした辞書)"""
    
    def __init__(self,agent: Agent,reason:str, result: Dict[Role,float]):
        self.agent = agent
        self.reason = reason
        self.probs = result
        
    def __str__(self) -> str:
        return self.agent + "is reason: " + self.reason + "\nresult: " + str(self.probs)

class ActionType(Enum):
    """取る行動の種類"""
    TALK = "TALK"
    VOTE = "VOTE"
    ATTACK = "ATTACK"
    DIVINE = "DIVINE"
    GUARD = "GUARD"
    WHISPER = "WHISPER"
    SKIP = "SKIP"
    OVER = "OVER"
    
class OneStepPlan:
    """戦略を表すクラス"""
    reason: str
    """理由"""
    action_type: ActionType
    """行動の種類"""
    action: Union[Agent,Content,str]

    def __init__(self,reason:str,action_type:ActionType,action:Union[Agent,Content,str]):
        self.reason = reason
        self.action_type = action_type
        self.action = action
    
    def __str__(self) -> str:
        return "reason: " + self.reason + "\naction_type: " + str(self.action_type) + "\naction: " + str(self.action)

class AbstractModule(ABC):
    config: ConfigParser
    """設定ファイル"""
    
    def __init__(self,config:ConfigParser) -> None:
        super().__init__()
        self.config = config
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        pass

class AbstractRoleEstimationModel(AbstractModule):
    def __init__(self,config:ConfigParser) -> None:
        super().__init__(config)
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

    @abstractmethod
    def estimate(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleEstimateResult:
        """
        入力：自然言語の対話・ゲーム情報、役職を推定するエージェント
        出力：エージェントの役職の推定確率とアテンションマップ
        """
        pass

class AbstractRoleInferenceModule(AbstractModule):
    role_estimation_model: AbstractRoleEstimationModel
    """役職推定モデル"""
    
    def __init__(self,config:ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        super().__init__(config)
        self.role_estimation_model = role_estimation_model

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)
  
    @abstractmethod
    def infer(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleInferenceResult:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報、役職を推定するエージェント
        出力：理由・推論結果のペア
        """
        pass
    

class AbstractStrategyModule(AbstractModule):
    history: List[OneStepPlan]
    """過去の行動の履歴"""
    future_plan: List[OneStepPlan]
    """未来の行動の予定"""
    next_plan: OneStepPlan
    """次の行動の予定"""
    
    role_estimation_model: AbstractRoleEstimationModel
    """役職推定モデル"""
    role_inference_module: AbstractRoleInferenceModule
    """役職推論モジュール"""
    
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config)
        self.role_estimation_model = role_estimation_model
        self.role_inference_module = role_inference_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)
        
    @abstractmethod
    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        """talk要求時に発話する内容を返す"""
        raise NotImplementedError()

    @abstractmethod
    def vote(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """vote要求時に投票するエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def attack(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """attack要求時に襲撃するエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def divine(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """divine要求時に占うエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def guard(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """guard要求時に護衛するエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def whisper(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        """whisper要求時に囁く内容を返す"""
        raise NotImplementedError()
    

    @abstractmethod
    def plan(self,game_info: GameInfo, game_setting: GameSetting) -> None:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        """
        pass
    
    @abstractmethod
    def update_history(self,game_info: GameInfo, game_setting: GameSetting,executed_plan:OneStepPlan) -> None:
        """実際の行動を受け取り、履歴を更新する"""
        self.history.append(executed_plan)
    
    @abstractmethod
    def update_future_plan(self,game_info: GameInfo, game_setting: GameSetting) -> None:
        """未来の行動を更新する"""
        pass
    

class AbstractRequestProcessingModule(AbstractModule):
    role_estimation_model: AbstractRoleEstimationModel
    """役職推論モジュール"""
    strategy_module: AbstractStrategyModule
    """戦略立案モジュール"""
    
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config)
        self.role_estimation_model = role_estimation_model
        self.strategy_module = strategy_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)
    
    @abstractmethod
    def process_request(self, game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：他者影響を考慮した行動の根拠と行動のペア
        """
        pass

class AbstractQuestionProcessingModule(AbstractModule):
    role_inference_module: AbstractRoleInferenceModule
    """役職推論モジュール"""
    strategy_module: AbstractStrategyModule
    """戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_inference_module:AbstractRoleInferenceModule, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config)
        self.role_inference_module = role_inference_module
        self.strategy_module = strategy_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

        
    @abstractmethod
    def process_question(self,game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：他者影響を考慮した行動の根拠と行動のペア
        """
        pass

class AbstractSpeakerModule(AbstractModule):  
    def __init__(self,config:ConfigParser) -> None:
        super().__init__(config)
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

    @abstractmethod
    def enhance_speech(self, speech:str) -> str:
        """
        入力：発話内容の自然言語
        出力：キャラ性を加えた自然言語
        """
        pass
    

class AbstractInfluenceConsiderationModule(AbstractModule):
    
    request_processing_module: AbstractRequestProcessingModule
    """他者からの要求を処理するモジュール"""
    question_processing_module: AbstractQuestionProcessingModule
    """他者からの質問を処理するモジュール"""
    
    def __init__(self,config:ConfigParser,request_processing_module:AbstractRequestProcessingModule, question_processing_module:AbstractQuestionProcessingModule) -> None:
        super().__init__(config)
        self.request_processing_module = request_processing_module
        self.question_processing_module = question_processing_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

    
    @abstractmethod
    def check_influence(self,game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool,OneStepPlan]:
        """ 
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：投げかけかどうかを表すbool値と、投げかけであった場合、他者影響を考慮した行動の根拠と行動のペア（投げかけ出ない場合はNone）
        """
        pass