from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractModule

import re,math,os,errno
import pathlib
from pathlib import Path


current_dir = pathlib.Path(__file__).resolve().parent


class RoleEstimationModelPreprocessor(AbstractModule):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        #役職推定に使うラベルのリスト(順番に意味あり)
        self.role_label_list = [Role.VILLAGER,Role.SEER,Role.BODYGUARD,Role.MEDIUM,Role.WEREWOLF,Role.POSSESSED,Role.FOX,Role.FREEMASON]

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
        
    from aiwolfk2b.utils.helper import load_default_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.ParseRuruLogToGameAttribution import load_sample_GameAttirbution
    config_ini = load_default_config()
    game_info_list,game_setting = load_sample_GameAttirbution(view_agent_idx)
    estimated_agent = Agent(estimated_agent_idx)

    preprocessor = RoleEstimationModelPreprocessor(config_ini)
    text = preprocessor.create_estimation_text(estimated_agent,game_info_list,game_setting)
    
    print(text)
        
        
def make_dataset(inputdir:Path,outputdir:Path,output_filename:str="dataset"):
    from aiwolfk2b.utils.helper import load_default_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.ParseRuruLogToGameAttribution import ParseRuruLogToGameAttribution
    import csv,pickle
    import tqdm
    dataset = []
    config = load_default_config()
    preprocessor = RoleEstimationModelPreprocessor(config)
    
    
    # 指定したディレクトリにあるデータを読み込む
    log_grob = "log_*.txt"
    count_completed = 0
    count_discarded = 0
    for inputpath in tqdm.tqdm(inputdir.rglob(log_grob)):
        parser = ParseRuruLogToGameAttribution(view_agent_idx=1)
        #パースがうまく行かないものはスキップ
        try:
            gameinfo_list, gamesetting = parser.create_game_log_from_ruru(inputpath,view_agent_idx=1)
            agent_role_dict = parser.agent_role_dict
            player_num = gamesetting.player_num
            #9人以上のゲームは除外
            if player_num > 9 or player_num < 5:
                continue
            
            for view_agent_idx in range(1,player_num+1):
                #各エージェントの立場からみた、別のエージェントの役職を推定する
                gameinfo_list, gamesetting = parser.create_game_log_from_ruru(None,view_agent_idx=view_agent_idx)
                
                for target_agent_idx in range(1,player_num+1):
                    #自分自身は推定しない
                    if target_agent_idx == view_agent_idx:
                        continue
                    target_agent = Agent(target_agent_idx)
                    estimation_text = preprocessor.create_estimation_text(target_agent,gameinfo_list,gamesetting)
                    answer_role = agent_role_dict[target_agent].name
                    dataset.append((answer_role,estimation_text))
            count_completed += 1
        except Exception as e:
            # print(f"error occured in {inputpath}")
            # print(e)
            count_discarded += 1
            continue
        
    print(f"complete {count_completed} files")
    print(f"discard {count_discarded} files")
    
    #ファイルに書き込む
    write = csv.writer(open(outputdir.joinpath(f"{output_filename}.csv") , "w"))
    write.writerows(dataset)
    
    with open(outputdir.joinpath(f"{output_filename}.pkl"), "wb") as f:
        pickle.dump(dataset, f)

if __name__ == "__main__":
    #単体テスト
    # GameAttribution(GameInfo,GameSetting)からtextを生成できるか確認
    # unit_test_make_estimation_text(view_agent_idx=1,estimated_agent_idx=2)
    
    # データセットを生成する単体テスト
    current_dir = pathlib.Path(__file__).resolve().parent
    input_dir = current_dir.joinpath("data","ruru_log","raw")
    output_dir = current_dir.joinpath("data","train")
    make_dataset(input_dir,output_dir,output_filename="dataset")
    
    # #データ生成の単体テスト
    # current_dir = pathlib.Path(__file__).resolve().parent
    # #蒸留したデータを読み込んで、前処理を行い、１つのファイルにまとめる
    # inputdir =  current_dir.joinpath("preprocessable_data")
    # outputdir = current_dir.joinpath("preprocessed_data")
    # make_dataset(inputdir,outputdir)
    
    
    
        