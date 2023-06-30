from configparser import ConfigParser
from typing import List,Tuple,Dict

from aiwolf.gameinfo import GameInfo,_GameInfo
from aiwolf.gamesetting import GameSetting,_GameSetting

from aiwolf.agent import Agent, Role, Status, Species,Winner
from aiwolf.judge import Judge, _Judge
from aiwolf.utterance import Talk, Whisper, _Utterance
from aiwolf.vote import Vote, _Vote
import re,math,os,errno
import pathlib
from pathlib import Path

current_dir = pathlib.Path(__file__).resolve().parent

def get_default_underb_GameInfo(my_agent_idx:int=1)->_GameInfo:
    """
    デフォルトのゲーム情報を返す（デバッグ用）

    Parameters
    ----------
    my_agent_idx : int, optional
        情報を受け取るエージェント, by default 1

    Returns
    -------
    _GameInfo
        デフォルトのゲーム情報(デバッグ用)
    """
    _gameinfo = _GameInfo()
    
    _gameinfo["agent"]:int = my_agent_idx #初期値
    _gameinfo["attackVoteList"]: List[Vote] = []
    _gameinfo["attackedAgent"] = -1 #初期値
    _gameinfo["cursedFox"] = -1 #初期値
    _gameinfo["day"]:int = 0 #初期値
    _gameinfo["divineResult"] = None
    _gameinfo["executedAgent"] = -1 #初期値
    _gameinfo["existingRoleList"]:List[Role] = []
    _gameinfo["guardedAgent"] = -1 #初期値
    _gameinfo["lastDeadAgentList"]: List[Agent] = []
    _gameinfo["latestAttackVoteList"]: List[Agent] = []
    _gameinfo["latestExecutedAgent"] = -1 #初期値
    _gameinfo["latestVoteList"]: List[Vote] = []
    _gameinfo["mediumResult"] = None
    _gameinfo["remainTalkMap"]: Dict[Agent, int] = {}
    _gameinfo["remainWhisperMap"]: Dict[Agent, int] = {}
    _gameinfo["roleMap"]: Dict[Agent, Role] = {}
    _gameinfo["statusMap"]: Dict[Agent, Status] = {}
    _gameinfo["talkList"]: List[Talk] = []
    _gameinfo["voteList"]: List[Vote] = []
    _gameinfo["whisperList"]: List[Whisper] = []
    return _gameinfo

def get_default_underb_GameSetting()->_GameSetting:
    """
    デフォルトのゲーム設定を返す（デバッグ用）

    Returns
    -------
    _GameSetting
        デフォルトのゲーム設定(デバッグ用)
    """

    _gamesetting = _GameSetting()
    
    _gamesetting["enableNoAttack"]:bool = False
    _gamesetting["enableNoExecution"]:bool = False
    _gamesetting["enableRoleRequest"]:bool = False
    _gamesetting["maxAttackRevote"]:int = 0
    _gamesetting["maxRevote"]:int = 1
    _gamesetting["maxSkip"]:int = 3
    _gamesetting["maxTalk"]:int = 10
    _gamesetting["maxTalkTurn"]:int = 20
    _gamesetting["maxWhisper"]:int = 10
    _gamesetting["maxWhisperTurn"]:int = 20
    _gamesetting["playerNum"]:int = 5
    _gamesetting["randomSeed"]:int = 0
    _gamesetting["roleNumMap"]:Dict[str,int] = {}
    _gamesetting["talkOnFirstDay"]:bool = False
    _gamesetting["timeLimit"]:int = 10000
    _gamesetting["validateUtterance"]:bool = False
    _gamesetting["votableInFirstDay"]:bool = False
    _gamesetting["voteVisible"]:bool = True
    _gamesetting["whisperBeforeRevote"]:bool = False
    
    return _gamesetting
    

def load_config(config_path:Path)-> ConfigParser:
    config = ConfigParser()

    # iniファイルが存在するかチェック
    if os.path.exists(config_path):
        # iniファイルが存在する場合、ファイルを読み込む
        with open(config_path, encoding='utf-8') as fp:
            config.read_file(fp)
    else:
        # iniファイルが存在しない場合、エラー発生
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_path)
    
    return config

def load_default_config()-> ConfigParser:
    config_ini_path = current_dir.parent.joinpath("AttentionReasoningAgent").joinpath("config.ini")
    return load_config(config_ini_path)

def load_GameInfo(game_info_path:Path)->GameInfo:
    import pickle
    with open(game_info_path,"rb") as f:
        game_info = pickle.load(f)
        
    return game_info

def load_default_GameInfo()-> GameInfo:
    game_info_path = current_dir.joinpath("game_info.pkl")
    game_info = load_GameInfo(game_info_path)
    
    return game_info

def load_GameSetting(game_setting_path:Path)->GameSetting:
    import pickle
    with open(game_setting_path,"rb") as f:
        game_setting = pickle.load(f)
        
    return game_setting

def load_default_GameSetting()->GameSetting:
    setting_path = current_dir.joinpath("game_setting.pkl")
    game_setting = load_GameSetting(setting_path)
        
    return game_setting


def get_openai_api_key()->str:
    """
    OpenAI APIのKEYを取得する

    Returns
    -------
    str
        OpenAI APIのKEY
    """
    key = ''
    #環境変数にAPIキーがある場合
    if 'OPENAI_API_KEY' in os.environ:
        key = os.environ['OPENAI_API_KEY']
    #環境変数にAPIキーがない場合
    else:
        #AIWOLFK2BにあるopenAIAPIkey.txtを読み込む
        aiwolfk2b_path = current_dir.parent.parent
        key_path = aiwolfk2b_path.joinpath("openAIAPIkey.txt")
        #openAIのAPIキーを読み込む
        with open(key_path, "r",encoding="utf-8") as f:
            key = f.read().strip()
            
    return key