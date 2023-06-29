from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractModule

import re,math,os,errno
import unicodedata,neologdn
import pathlib
from pathlib import Path


current_dir = pathlib.Path(__file__).resolve().parent


class RoleEstimationModelPreprocessor(AbstractModule):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        #役職推定に使うラベルのリスト(順番に意味あり)
        self.role_label_list = [Role.VILLAGER,Role.SEER,Role.BODYGUARD,Role.MEDIUM,Role.WEREWOLF,Role.POSSESSED,Role.FOX,Role.FREEMASON]
        
    def preprocess_text(self,text: str)->str:
        """
        会話文において不要と思われる記号の削除や表記ゆれの統一

        Parameters
        ----------
        text : str
            前処理する会話文

        Returns
        -------
        str
            前処理後の会話文
        """
        #TODO:実装する
        #Unicode正規化
        text = unicodedata.normalize("NFKC",text)
        #全部小文字にする
        text = text.lower()
        #文字種の統一と不要な文字の除去,文字の繰り返しの削除
        text = neologdn.normalize(text,repeat=3) #REVIEW:repeat数は要検討
        #二個以上の連続した改行削除(間に空白がある場合も削除)
        text = re.sub(r"\n[ ]*\n","\n",text)
        text = re.sub(r"\n{2,}","\n",text)
        # # 改行削除
        #text = text.replace("\n","")
        #空白削除
        text = text.replace(" ","")
        #白・黒の記号(○・●)を置換
        text = text.replace("○","白").replace("◯","白").replace("◦","白")
        text = text.replace("•","黒").replace("●","黒")
        
        return text
        


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
        
    def create_estimation_text(self,estimated_agent: Agent, game_info_list: List[GameInfo], game_setting: GameSetting,compress_text:bool=True)->str:
        """
        役職推定に使うテキストを作成する
        
        Parameters
        ----------
        estimated_agent : Agent
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
            return (agent_idx - estimated_agent.agent_idx + game_setting.player_num)%game_setting.player_num+1
        
        estimation_text = ""
        #役職のマップを作成
        role_text=str(game_setting.role_num_map[self.role_label_list[0]])
        for role in self.role_label_list[1:]:
            role_text += ","+str(game_setting.role_num_map[role])
            
        estimation_text += "role_map:"+role_text+"\n"
        
        #日付ごとに情報をまとめる
        #日付でlistをソート
        game_info_list.sort(key=lambda x:x.day)
        
        
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
            #会話順にソート
            game_info.talk_list.sort(key=lambda x:x.idx)
            for talk in game_info.talk_list:
                talk_text = talk.text
                if compress_text:
                    talk_text = self.compress_text(talk_text)
                agent_idx = rotate_agent_idx(talk.agent.agent_idx)
                #テキスト中のエージェントについて、推定対象のエージェントがAgent[01]となるように順番を入れ替える
                talk_text = re.sub(r"Agent\[(\d+)\]",lambda m: f"Agent[{rotate_agent_idx(int(m.group(1))):02d}]",talk_text)
                daily_text += f"{agent_idx},{talk_text}\n"
            
            #TODO:voteの結果はすべて表示させるものになっているが、再投票になった場合の明示をどうするか、検討する必要あり
            #投票結果を追加
            daily_text += "vote\n"
            for vote in reversed(game_info.latest_vote_list): #投票順に並べる
                src_agent_idx = rotate_agent_idx(vote.agent.agent_idx)
                tgt_agent_idx = rotate_agent_idx(vote.target.agent_idx)
                daily_text += f"{src_agent_idx},{tgt_agent_idx}\n"
                       
            #処刑結果を追加
            if game_info.executed_agent is not None:
                agent_idx = rotate_agent_idx(game_info.executed_agent.agent_idx)
                daily_text += f"executed,{agent_idx}\n"

            #一日分の情報を追加
            estimation_text += daily_text
        
        #Agent[数字]->[数字]に変換して情報を圧縮
        estimation_text = re.sub(r"Agent\[(\d+)\]",lambda m: f"[{m.group(1)}]",estimation_text)
        
        return estimation_text
      


    
def unit_test_make_estimation_text(view_agent_idx:int, estimated_agent_idx:int):
    """
    RoleEstimationModelPreprocessorのcreate_estimation_text関数の単体テスト

    Parameters
    ----------
    view_agent_idx : _type_
        GameInfo,GameSettingを受け取っているAgentの番号
    estimated_agent_idx : _type_
        推定対象のエージェントの番号
    """
        
    from aiwolfk2b.utils.helper import load_default_config,load_default_GameInfo,load_default_GameSetting
    from aiwolf import Talk
    config_ini = load_default_config()
    game_info = load_default_GameInfo()
    game_info.talk_list.append(Talk(idx=1,day=1,turn=1,agent=Agent(1),text="Agent[01]は人狼だよ"))
    game_setting = load_default_GameSetting()
    
    estimated_agent = Agent(estimated_agent_idx)

    preprocessor = RoleEstimationModelPreprocessor(config_ini)
    text = preprocessor.create_estimation_text(estimated_agent,[game_info],game_setting)
    
    print(text)
        

if __name__ == "__main__":
    #単体テスト
    # GameAttribution(GameInfo,GameSetting)からtextを生成できるか確認
    unit_test_make_estimation_text(view_agent_idx=1,estimated_agent_idx=2)
    
    # #データ生成の単体テスト
    # current_dir = pathlib.Path(__file__).resolve().parent
    # #蒸留したデータを読み込んで、前処理を行い、１つのファイルにまとめる
    # inputdir =  current_dir.joinpath("preprocessable_data")
    # outputdir = current_dir.joinpath("preprocessed_data")
    # make_dataset(inputdir,outputdir)
    
    
    
        