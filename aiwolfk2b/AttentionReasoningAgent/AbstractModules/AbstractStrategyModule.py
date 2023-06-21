from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser
from enum import Enum

from aiwolf import GameInfo,GameSetting
from aiwolf import Agent,Content
from AbstractModule import AbstractModule
from AbstractRoleEstimationModel import AbstractRoleEstimationModel
from AbstractRoleInferenceModule import AbstractRoleInferenceModule

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
        """
        コンストラクタ

        Parameters
        ----------
        reason : str
            理由を表す文字列
        action_type : ActionType
            行動の種類
        action : Union[Agent,Content,str]
            行動の種類に応じた行動
        """
        self.reason = reason
        self.action_type = action_type
        self.action = action
    
    def __str__(self) -> str:
        return "reason: " + self.reason + "\naction_type: " + str(self.action_type) + "\naction: " + str(self.action)


class AbstractStrategyModule(AbstractModule):
    """戦略モジュールの抽象クラス"""
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
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        role_estimation_model : AbstractRoleEstimationModel
            役職推定モデル
        role_inference_module : AbstractRoleInferenceModule
            役職推論モジュール
        """
        super().__init__(config)
        self.role_estimation_model = role_estimation_model
        self.role_inference_module = role_inference_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """
        ゲーム開始時に呼ばれる初期化処理

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        """
        super().initialize(game_info, game_setting)
        
    @abstractmethod
    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        """
        指定された情報から、talk要求時に発話すべき内容を返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        str
            発話する内容

        Raises
        ------
        NotImplementedError
            オーバーライドされていない場合に発生
        """
        raise NotImplementedError()

    @abstractmethod
    def vote(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """
        指定された情報から、vote要求時に投票すべきエージェントを返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Agent
            投票するエージェント

        Raises
        ------
        NotImplementedError
            オーバーライドされていない場合に発生
        """
        raise NotImplementedError()

    @abstractmethod
    def attack(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """
        指定された情報から、attack要求時に襲撃すべきエージェントを返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Agent
            襲撃するエージェント

        Raises
        ------
        NotImplementedError
            オーバーライドされていない場合に発生
        """
        raise NotImplementedError()

    @abstractmethod
    def divine(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """
        指定された情報から、divine要求時に占うべきエージェントを返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Agent
            占うエージェント

        Raises
        ------
        NotImplementedError
            オーバーライドされていない場合に発生
        """
        raise NotImplementedError()

    @abstractmethod
    def guard(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """
        指定された情報から、guard要求時に護衛すべきエージェントを返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Agent
            護衛するエージェント

        Raises
        ------
        NotImplementedError
            オーバーライドされていない場合に発生
        """
        raise NotImplementedError()

    @abstractmethod
    def whisper(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        """
        指定された情報から、whisper要求時に囁く内容を返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        str
            囁く内容

        Raises
        ------
        NotImplementedError
            オーバーライドされていない場合に発生
        """
        raise NotImplementedError()
    

    @abstractmethod
    def plan(self,game_info: GameInfo, game_setting: GameSetting) -> None:
        """
        現状の盤面から未来の行動を計画する

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        """
        
        pass
    
    @abstractmethod
    def update_history(self,game_info: GameInfo, game_setting: GameSetting,executed_plan:OneStepPlan) -> None:
        """
        実際に行った行動を受け取り、履歴を更新し、今後の戦略立案に必要な情報を更新する

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        executed_plan : OneStepPlan
            実際に行った行動
        """
        self.history.append(executed_plan)
    
    @abstractmethod
    def update_future_plan(self,game_info: GameInfo, game_setting: GameSetting) -> None:
        """
        未来の行動を更新する

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        """
        pass