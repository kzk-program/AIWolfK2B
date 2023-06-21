
from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting
from AbstractModule import AbstractModule


class AbstractSpeakerModule(AbstractModule):
    """個性のない発話内容を個性のある発話内容に変換するモジュールの抽象クラス"""
    
    def __init__(self,config:ConfigParser) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        """
        super().__init__(config)
    
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
    def enhance_speech(self, speech:str) -> str:
        """
        発話内容(自然言語)をキャラ性を加えた内容に変換する

        Parameters
        ----------
        speech : str
            変換したい発話内容(自然言語)

        Returns
        -------
        str
            変換した後の発話内容(自然言語)
        """
        pass
