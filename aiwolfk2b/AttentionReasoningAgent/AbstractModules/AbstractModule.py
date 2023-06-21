from abc import ABC
from configparser import ConfigParser
from aiwolf import GameInfo,GameSetting

class AbstractModule(ABC):
    """モジュールの抽象クラス"""
    config: ConfigParser
    """設定ファイル"""
    
    def __init__(self,config:ConfigParser) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        """
        super().__init__()
        self.config = config
    
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
        pass