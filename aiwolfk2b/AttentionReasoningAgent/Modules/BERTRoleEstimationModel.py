from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,RoleEstimationResult

import random
import math
import torch
from transformers import BertJapaneseTokenizer, BertForSequenceClassification


class BERTRoleEstimationModel(AbstractRoleEstimationModel):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.modelpath = config.get("RoleEstimationModel","bert_model_path")
        self.bert_tokenizer_name = config.get("RoleEstimationModel","bert_tokenizer_name")
        self.batch_size = config.getint("RoleEstimationModel","batch_size")
        self.max_length = config.getint("RoleEstimationModel","max_length")
        #役職推定に使うラベルのリスト(順番に意味あり)
        self.labels_list = [Role.VILLAGER,Role.SEER,Role.BODYGUARD,Role.MEDIUM,Role.WEREWOLF,Role.POSSESSED,Role.FOX,Role.FREEMASON]
        
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
        
    def estimate(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleEstimationResult:
        """bertを使って役職を推定する"""
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
            
        return RoleEstimationResult(agent,estimation,None)
    
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
            for idx,role in enumerate(self.labels_list):
                if game_setting.role_num_map[role] == 0:
                    scores[:,idx] = -torch.inf
            
            probs = torch.nn.functional.softmax(scores,dim=1)
            #各バッチに対して推論結果を取得
            probs = probs.cpu().double().numpy()
            for i in range(len(text_list)):
                estimation = {}
                for j in range(len(self.labels_list)):
                    estimation[self.labels_list[j]] = probs[i][j]
                one_batch_attention = [attentions[k][i].cpu().numpy() for k in range(len(attentions))]
                results.append(RoleEstimationResult(None,estimation,one_batch_attention))
            
        return results
        
        
if __name__ == "__main__":
    #単体テスト
    from preprocess_data import get_default_GameInfo
    import configparser
    #現在のプログラムが置かれているディレクトリを取得
    import pathlib,pickle,errno,os
    current_dir = pathlib.Path(__file__).resolve().parent
    
    _game_info = get_default_GameInfo()
    game_info = GameInfo(_game_info)
    setting_path = current_dir.joinpath("game_setting.pkl")
    with open(setting_path,"rb") as f:
        game_setting = pickle.load(f)
     
    config_ini = configparser.ConfigParser()
    config_ini_path = current_dir.parent.joinpath("config.ini")

    # iniファイルが存在するかチェック
    if os.path.exists(config_ini_path):
        # iniファイルが存在する場合、ファイルを読み込む
        with open(config_ini_path, encoding='utf-8') as fp:
            config_ini.read_file(fp)
    else:
        # iniファイルが存在しない場合、エラー発生
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)
     
    estimator = BERTRoleEstimationModel(config_ini)
    estimator.initialize(game_info,game_setting)
    result_list = estimator.estimate_from_text(["今日は晴れですね","明日は雨です"])
    for res in result_list:
        print(res.probs)
        