from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,RoleEstimationResult

import re,math,os,errno
import pathlib
from pathlib import Path

import torch

from transformers import BertJapaneseTokenizer, BertForSequenceClassification

current_dir = pathlib.Path(__file__).resolve().parent

class BERTRoleEstimationModel(AbstractRoleEstimationModel):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.modelpath = current_dir.joinpath(config.get("RoleEstimationModel","bert_model_path"))
        self.bert_tokenizer_name = config.get("RoleEstimationModel","bert_tokenizer_name")
        self.batch_size = config.getint("RoleEstimationModel","batch_size")
        self.max_length = config.getint("RoleEstimationModel","max_length")
        #役職推定に使うラベルのリスト(順番に意味あり)
        self.role_label_list = [Role.VILLAGER,Role.SEER,Role.BODYGUARD,Role.MEDIUM,Role.WEREWOLF,Role.POSSESSED,Role.FOX,Role.FREEMASON]
        
        #計算に使うdeviceを取得
        #self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu" #多分推論はCPUの方が速い
        self.bert_sc = BertForSequenceClassification.from_pretrained(
            self.modelpath,
        )
        self.bert_sc = self.bert_sc.to(self.device)
        # 文章をトークンに変換するトークナイザーの読み込み
        self.tokenizer:BertJapaneseTokenizer = BertJapaneseTokenizer.from_pretrained(self.bert_tokenizer_name)
        
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        self.game_info = game_info
        self.game_setting = game_setting
        
    def compress_text(self,text: str)->str:
        """
        会話文の中で、人狼に関係ある部分を抽出する

        Parameters
        ----------
        text : str
            会話文

        Returns
        -------
        str
            圧縮された会話文
        """
        #TODO:実装する
        return text
        
    def make_estimation_text(self,agent: Agent, game_info_list: List[GameInfo], game_setting: GameSetting,compress_text:bool=True)->str:
        """
        役職推定に使うテキストを作成する
        
        Parameters
        ----------
        agent : Agent
            推定対象のエージェント
        game_info : List[GameInfo]
            役職推定に用いるゲーム情報
        game_setting : GameSetting
            役職推定に用いるゲーム設定
        
        Returns
        -------
        str
            役職推定に使うテキスト
        """
        
        #推論に必要な情報をテキスト化
        #書式は以下の通り
        #role_map:(villager,seer,bodyguard,medium,werewolf,possessed,fox,cat,immortal,freemason) 
        #day1
        #attacked,agent_idx
        #guareded,agent_idx
        #(divine,agent_idx,species) #あれば
        #talk
        #unique_id,agent_idx,text
        #vote
        #from_agent_idx,to_agent_idx
        #executed,agent_idx
        #day2
        # same as day1
        #...
        #my_role (あれば)
        
        def rotate_agent_idx(agent_idx:int)->int:
            """
            推定するエージェントの番号が01になるようにインデックスを入れ替える

            Parameters
            ----------
            agent_idx : int
                入れ替えるエージェントの番号

            Returns
            -------
            int
                入れ替えた後のエージェントの番号
            """
            return (agent_idx - agent.agent_idx + game_setting.player_num)%game_setting.player_num+1
        
        estimation_text = ""
        #役職のマップを作成
        role_text=str(game_setting.role_num_map[self.role_label_list[0]])
        for role in self.role_label_list[1:]:
            role_text += ","+str(game_setting.role_num_map[role])
            
        estimation_text += "role_map:("+role_text+")\n"
        
        #日付ごとに情報をまとめる
        for game_info in game_info_list:
            daily_text = ""
            daily_text += f"day{game_info.day}\n"
            #朝わかる結果を追加
            if game_info.divine_result is not None: #占い結果があれば
                target_agent_idx = rotate_agent_idx(game_info.divine_result.target.agent_idx)
                species = game_info.divine_result.result
                daily_text += f"divine,{target_agent_idx},{species}\n"
            if game_info.attacked_agent is not None: #襲撃結果があれば
                agent_idx = rotate_agent_idx(game_info.attacked_agent.agent_idx)
                daily_text += f"attacked,{agent_idx}\n"
            if game_info.guarded_agent is not None: #護衛結果があれば
                agent_idx = rotate_agent_idx(game_info.guarded_agent.agent_idx)
                daily_text += f"guarded,{agent_idx}\n"
                
            #会話文を追加
            daily_text += "talk\n"
            for talk in reversed(game_info.talk_list):
                talk_text = talk.text
                if compress_text:
                    talk_text = self.compress_text(talk_text)
                agent_idx = rotate_agent_idx(talk.agent.agent_idx)
                #テキスト中のエージェントについて、推定対象のエージェントがAgent[01]となるように順番を入れ替える
                talk_text = re.sub(r"Agent\[(\d+)\]",lambda m: f"Agent[{rotate_agent_idx(int(m.group(1)))}:02d]",talk_text)
                daily_text += f"{agent_idx},{talk_text}\n"
            
            
            #投票結果を追加
            daily_text += "vote\n"
            for vote in game_info.vote_list:
                src_agent_idx = rotate_agent_idx(vote.agent.agent_idx)
                tgt_agent_idx = rotate_agent_idx(vote.target.agent_idx)
                daily_text += f"{src_agent_idx},{tgt_agent_idx}\n"
                       
            #処刑結果を追加
            if game_info.executed_agent is not None:
                agent_idx = rotate_agent_idx(game_info.executed_agent.agent_idx)
                daily_text += f"executed,{agent_idx}\n"

            #一日分の情報を追加
            estimation_text += daily_text + "\n"
        
        #Agent[数字]->[数字]に変換して情報を圧縮
        estimation_text = re.sub(r"Agent\[(\d+)\]",lambda m: f"[{m.group(1)}]",estimation_text)
        
        return estimation_text
          
    
    def estimate(self,agent:Agent, game_info_list: List[GameInfo], game_setting: GameSetting,compress_text:bool=True) -> RoleEstimationResult:
        """
        BERTを使って役職を推定する

        Parameters
        ----------
        agent : Agent
            推定対象のエージェント
        game_info : List[GameInfo]
            役職推定に用いるゲーム情報
        game_setting : GameSetting
            役職推定に用いるゲーム設定
        compress_text : bool, optional
            GameInfoのTalkを前処理によって圧縮するかどうか(True:する), by default True

        Returns
        -------
        RoleEstimationResult
            Agentの役職推定結果
        """
        
        
        
        pass
    
    def estimate_from_text(self,text_list:List[str],game_setting: GameSetting=None)-> List[RoleEstimationResult]:
        """
        与えられたテキストからAgent[01]の役職を推定し、その結果を返す関数

        Parameters
        ----------
        text_list : List[str]
            役職推定に用いるテキストのリスト
        game_setting : GameSetting, optional
            計算時に考慮するゲームの設定, by default None

        Returns
        -------
        List[RoleEstimationResult]
            役職推定結果のリスト
        """
        if game_setting is None:
            game_setting = self.game_setting
        
        #テキストをトークン化
        inputs = self.tokenizer(text_list,max_length=self.max_length, 
        padding='longest',truncation=True,return_tensors="pt")
        # 推論
        inputs = { k: v.to(self.device) for k, v in inputs.items() }
        results=[]
        #attentionを計算するように設定
        inputs["output_attentions"] = True
        
        with torch.no_grad():
            outputs = self.bert_sc.forward(**inputs)
            #推論結果をソフトマックス関数で正規化
            scores = outputs.logits
            attentions = outputs.attentions
            #存在しない役職のスコアを-torch.infにする
            for idx,role in enumerate(self.role_label_list):
                if game_setting.role_num_map[role] == 0:
                    scores[:,idx] = -torch.inf
            
            probs = torch.nn.functional.softmax(scores,dim=1)
            #各バッチに対して推論結果を取得
            probs = probs.cpu().double().numpy()
            for i in range(len(text_list)):
                estimation = {}
                for j in range(len(self.role_label_list)):
                    estimation[self.role_label_list[j]] = probs[i][j]
                one_batch_attention = [attentions[k][i].cpu().numpy() for k in range(len(attentions))]
                results.append(RoleEstimationResult(None,estimation,one_batch_attention))
            
        return results
    
    
def get_default_config()-> ConfigParser:
    config_ini = ConfigParser()
    config_ini_path = current_dir.parent.joinpath("config.ini")

    # iniファイルが存在するかチェック
    if os.path.exists(config_ini_path):
        # iniファイルが存在する場合、ファイルを読み込む
        with open(config_ini_path, encoding='utf-8') as fp:
            config_ini.read_file(fp)
    else:
        # iniファイルが存在しない場合、エラー発生
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)
    
    return config_ini

def get_default_GameInfo()->GameInfo:
    from preprocess_data import get_default_GameInfo
    _game_info = get_default_GameInfo()
    game_info = GameInfo(_game_info)
    
    return game_info

def get_default_GameSetting()->GameSetting:
    import pickle
    setting_path = current_dir.joinpath("game_setting.pkl")
    with open(setting_path,"rb") as f:
        game_setting = pickle.load(f)
        
    return game_setting

    
def unit_test_estimate_from_text():
    """
    BERTRoleEstimationModelのestimate_from_text関数の単体テスト
    """    

    config_ini = get_default_config()
    game_info = get_default_GameInfo()
    game_setting = get_default_GameSetting()
    

    estimator = BERTRoleEstimationModel(config_ini)
    estimator.initialize(game_info,game_setting)
    
    test_text =["""2,1,0,0,1,1,0,0
SEER
day1
talk:
占いCO[01]は人狼
そうだ、俺は人狼だ！
"""]                

    
    result_list = estimator.estimate_from_text(test_text)
    for res in result_list:
        print(res.probs)
    
def unit_test_make_estimation_text():
    pass
        
if __name__ == "__main__":
    unit_test_estimate_from_text()
        