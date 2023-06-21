from abc import ABC
from configparser import ConfigParser
from aiwolf import GameInfo,GameSetting

class AbstractModule(ABC):
    config: ConfigParser
    """設定ファイル"""
    
    def __init__(self,config:ConfigParser) -> None:
        super().__init__()
        self.config = config
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        pass