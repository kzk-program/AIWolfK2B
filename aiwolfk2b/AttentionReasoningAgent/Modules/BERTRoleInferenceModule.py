import pathlib
from pathlib import Path
from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf import Role,Agent,Species
from aiwolf.utterance import Utterance,Talk
from aiwolf.judge import Judge
from aiwolf.vote import Vote
from aiwolfk2b.AttentionReasoningAgent.Modules.RoleEstimationModelPreprocessor import RoleEstimationModelPreprocessor
from aiwolfk2b.AttentionReasoningAgent.Modules.BERTRoleEstimationModel import BERTRoleEstimationModel
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import RoleEstimationResult,RoleInferenceResult,AbstractRoleEstimationModel,AbstractRoleInferenceModule
from aiwolfk2b.utils.helper import get_openai_api_key

import torch,re,openai,threading
import numpy as np

current_dir = pathlib.Path(__file__).resolve().parent

class BERTRoleInferenceModule(AbstractRoleInferenceModule):
    """BERTを使って役職を推論するモジュール"""
    def __init__(self, config: ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        super().__init__(config,role_estimation_model)
        #計算に使うdeviceを取得
        #self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu" #TODO:多分推論はCPUの方が速いからこのように指定するが、GPUでの推論と比較してみる
        
        #上位何件までの情報をもとに推論するか
        self.top_n = self.config.getint("BERTRoleInferenceModule","top_n")
        
        #gptまわりの設定
        self.gpt_model= self.config.get("BERTRoleInferenceModule","gpt_model")
        self.gpt_max_tokens = self.config.getint("BERTRoleInferenceModule","gpt_max_tokens")
        self.gpt_temperature = self.config.getfloat("BERTRoleInferenceModule","gpt_temperature")
        #openAIのAPIキーを読み込む
        openai.api_key = get_openai_api_key()
        
        #BERTのモデルを読み込むことを前提にする
        if not isinstance(self.role_estimation_model,BERTRoleEstimationModel):
            raise Exception("role_estimation_model must be BERTRoleEstimationModel with BERTRoleInferenceModule")
        else:
            self.estimator:BERTRoleEstimationModel = self.role_estimation_model
        
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        self.game_info = game_info
        self.game_setting = game_setting
        
            
    def parse_estimate_text(self,estimate_text:str,result: RoleEstimationResult,agent: Agent, game_setting: GameSetting)->List[Tuple[float,Agent,Union[Agent,str,Species],str]]:
        """
        推定したテキストと推定結果をパースして、アクションごとのアテンションとアクションのリストに変換して返す

        Parameters
        ----------
        estimate_text : str
            推定に使用したテキスト(エージェント番号変更済み)
        result : RoleEstimationResult
            推定結果
        agent : Agent
            推定対象のエージェント
        game_setting : GameSetting
            ゲーム設定

        Returns
        -------
        List[Tuple[float,Agent,Union[Agent,str,Species],str]]
            [attentionの総和、アクションを行ったエージェント、アクションごとの個別の行動、アクションの種類]のリスト

        Raises
        ------
        Exception
            想定外のアクションがあった場合に発生
        Exception
            空行があった場合に発生
        """
        
        #\nを[SEP]に変換する
        sep_estimate_text = estimate_text.replace("\n","[SEP]")
        
        words = self.estimator.convert_to_tokens_without_joint_sign(sep_estimate_text)
        _,attens = self.estimator.calc_word_attention_pairs(estimate_text,result)

        sentence_attens:List[Tuple[float,Agent,Union[Agent,str,Species],str]] = []
        accum_text=""
        phase = ""
        day = 0
        accum_attens = 0.0
        
        for word,atten in zip(words,attens):
            if word == "[SEP]":#一行終わったら終わり
                if accum_text == "":
                    raise Exception("空行は想定していません") 
                elif accum_text in ["talk","vote"]:
                    phase = accum_text
                elif accum_text.startswith("day"):
                    day = int(accum_text.replace("day",""))
                elif accum_text.startswith("role_map:"):
                    role_map = accum_text.replace("role_map:","")
                    sentence_attens.append((accum_attens,None,role_map,"role_map"))
                else:
                    word_split = accum_text.split(",")
                    if phase == "talk":
                        talk = self.decompose_talk_text(accum_text,agent,game_setting)
                        sentence_attens.append((accum_attens,talk.agent,talk.text,"talk"))
                    elif phase == "vote":
                        vote = self.decompose_vote_text(accum_text,agent,game_setting)
                        sentence_attens.append((accum_attens,vote.agent,vote.target,"vote"))
                    else:
                        action_type = word_split[0]
                        if action_type == "divine":
                            target_idx = self.revert_agent_idx(int(word_split[1]),agent,game_setting)
                            species = Species(word_split[2])
                            sentence_attens.append((accum_attens,Agent(target_idx),species,"divine"))
                        elif action_type == "attacked":
                            attacked_idx = self.revert_agent_idx(int(word_split[1]),agent,game_setting)
                            sentence_attens.append((accum_attens,Agent(attacked_idx),None,"attacked"))
                        elif action_type == "guarded":
                            guarded_idx = self.revert_agent_idx(int(word_split[1]),agent,game_setting)
                            sentence_attens.append((accum_attens,Agent(guarded_idx),None,"guarded"))
                        elif action_type =="executed":
                            executed_idx = self.revert_agent_idx(int(word_split[1]),agent,game_setting)
                            sentence_attens.append((accum_attens,Agent(executed_idx),None,"executed"))
                        else:
                            raise Exception(f"想定外のaction_type:{action_type}")
                accum_text = ""
                accum_attens = 0.0
            else:
                accum_text += word
                accum_attens += atten
                
        return sentence_attens
    
    def format_reason_text(self,sentence_attens:List[Tuple[float,Agent,Union[Agent,str,Species],str]])->str:
        """
        単語とattentionのペアのリストを受け取り、上位top_n個の会話文を取得し、chatgptに入力する形式に整形する

        Parameters
        ----------
        sentence_attens : List[Tuple[float,Agent,Union[Agent,str,Species],str]]
            [attentionの総和、アクションを行ったエージェント、アクションごとの個別の行動、アクションの種類]のリスト

        Returns
        -------
        str
            chatgptに理由として入力する形式に整形した文字列

        Raises
        ------
        Exception
           未定義行動が含まれている場合
        """
        #attentionの大きい順にソートする
        sentence_attens.sort(key=lambda x:x[0],reverse=True)
        #上からtop_n個の会話文を取得する
        reason_text = ""
        for attens, agent,uni,action_type in sentence_attens[:self.top_n]:
            if action_type == "talk":
                reason_text += f"{agent}が「{uni}」と言った\n"
            elif action_type == "vote":
                reason_text += f"{agent}が{uni}に投票した\n"
            elif action_type == "divine":
                reason_text += f"{agent}を占った結果、{uni}だった\n"
            elif action_type == "attacked":
                reason_text += f"{agent}が襲撃された\n"
            elif action_type == "guarded":
                reason_text += f"{agent}を護衛した\n"
            elif action_type == "executed":
                reason_text += f"{agent}が処刑された\n"
            elif action_type == "role_map":
                role_nums = [int(x) for x in uni.split(",")]
                reason_text += "役職の分布が、"
                for num,role in zip(role_nums,self.estimator.preprocessor.role_label_list):
                    if num == 0: #0人なら表示しない
                        continue
                    reason_text += f"{role.name}が{num}人、"
                reason_text += "である\n"
            else:
                raise Exception(f"想定外のaction_type:{action_type}")
        
        return reason_text
    
    def infer(self,agent:Agent, game_info_list:List[GameInfo], game_setting: GameSetting) -> RoleInferenceResult:
        """
        指定された情報から、BERTを使って指定されたエージェントの役職を推論する

        Parameters
        ----------
        agent : Agent
            推論対象のエージェント
        game_info_list : List[GameInfo]
            ゲームの情報のリスト
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        RoleInferenceResult
            指定されたエージェントの役職推論結果(理由・推論結果のペア)
        """
        #推論に用いる入力の作成
        estimate_text = self.estimator.preprocessor.create_estimation_text(agent,game_info_list,game_setting)
        #役職推定の実行
        result = self.estimator.estimate_from_text([estimate_text],game_setting)[0]
        #単語とattentionのペアのリストを作成
        sentence_attens = self.parse_estimate_text(estimate_text,result,agent,game_setting)
        #print(f"sentence_attens:{sentence_attens}")
        
        #chatgptに投げるために、推論理由を整形
        reason_text = self.format_reason_text(sentence_attens)
        
        # chatgptを用いて推論理由を生成
        #最大確率を持つラベルを予測結果とする
        pred_role = max(result.probs.items(), key=lambda x: x[1])[0]
        
        # 与え方1
        explain_text = f"人狼ゲームにて、以下の箇条書きの内容から{agent}が{pred_role.name}であると推定される。以下の情報を元に{agent}の役職が{pred_role.name}と呼べる理由を論理的に簡潔に50字内で述べなさい。だだし、文末は「から」で終わらせなさい\n{reason_text}"
        #print(f"explain_text:{explain_text}")
        
        explain_message = [{"role":"user","content":explain_text}]
        
        # # 与え方2
        # explain_text = f"人狼ゲームにて、以下の箇条書きの内容から{agent}が{pred_role.name}であると推定される。以下の情報を元に{agent}の役職が{pred_role.name}と呼べる理由を論理的に簡潔に50字内で述べなさい。だだし、文末は「から」で終わらせなさい\n"
        # #print(f"explain_text:{explain_text}")
        
        # explain_message = [{"role":"system","content":explain_text},{"role":"user","content":reason_text}]
        
        
        explained_reason = self.send_message_to_api(explain_message)
        #print(f"log_text:{estimate_text}")
        
        inference = RoleInferenceResult(agent,explained_reason,result.probs)
        
        return inference
    
    def revert_agent_idx(self, agent_idx:int, agent: Agent, game_setting: GameSetting) -> int:
        """
        推定するエージェントの番号が01になるようにインデックスを入れ替える

        Parameters
        ----------
        agent_idx : int
            入れ替え後のエージェントの番号
        agent : Agent
            推論対象のエージェント
        game_setting : GameSetting
            ゲームの設定
            
        Returns
        -------
        int
            基準をもとに戻したエージェントの番号
        """
        return (agent_idx + agent.agent_idx + game_setting.player_num) % game_setting.player_num + 1

    def decompose_talk_text(self, talk_text:str, agent: Agent, game_setting: GameSetting) -> Talk:
        """
        会話文を分解する

        Parameters
        ----------
        talk_text : str
            分解する会話文
        agent : Agent
            推論対象のエージェント
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        List[str]
            分解した会話文
        """
        split_text = talk_text.split(",")
        # TODO:他の情報も復元する
        agent_idx = self.revert_agent_idx(int(split_text[0]), agent, game_setting)
        #[2桁の数字]->Agent[revert_agent_idx(2桁の数字)]に変換
        rev_text = re.sub(r"\[([0-9]{2})\]",lambda m: f"Agent[{self.revert_agent_idx(int(m.group(1)), agent, game_setting):02d}]",split_text[1])
        return Talk(agent=Agent(agent_idx),text=rev_text)
    
    def decompose_vote_text(self, vote_text:str, agent: Agent, game_setting: GameSetting) -> Vote:
        """
        投票文を分解する

        Parameters
        ----------
        vote_text : str
            分解する投票文
        agent : Agent
            推論対象のエージェント
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Vote
            分解した投票文
        """
        split_text = vote_text.split(",")
        #TODO:他の情報も復元する
        from_agent_idx = self.revert_agent_idx(int(split_text[0]), agent, game_setting)
        to_agent_idx = self.revert_agent_idx(int(split_text[1]), agent, game_setting)
        return Vote(agent=Agent(from_agent_idx),target=Agent(to_agent_idx))

    def send_message_to_api(self,messages:List[Dict[str,str]], max_retries:int=5, timeout:int=10)-> str:
        """
        OpenAI APIにメッセージを送信し、返信を受け取る

        Parameters
        ----------
        messages : List[Dict[str,str]]
            送信するメッセージ
        max_retries : int, optional
            最大の再送処理回数, by default 5
        timeout : int, optional
            タイムアウトの時間[s], by default 10

        Returns
        -------
        str
            OpenAI APIからの返信(assistantの内容)
        """

        def api_call(api_result, event):
            try:
                # print("calling api")
                completion = openai.ChatCompletion.create(
                    model=self.gpt_model,
                    messages=messages,
                    max_tokens=self.gpt_max_tokens,
                    temperature=self.gpt_temperature
                )
                api_result["response"] = completion.choices[0].message.content
            except Exception as e:
                api_result["error"] = e
            finally:
                event.set()

        for attempt in range(max_retries):
            api_result = {"response": None, "error": None}
            event = threading.Event()
            api_thread = threading.Thread(target=api_call, args=(api_result, event))

            api_thread.start()
            finished = event.wait(timeout)

            if not finished:
                print(
                    f"Timeout exceeded: {timeout}s. Attempt {attempt + 1} of {max_retries}. Retrying..."
                )
            else:
                if api_result["error"] is not None:
                    print(api_result["error"])
                    print(
                        f"API error: {api_result['error']}. Attempt {attempt + 1} of {max_retries}. Retrying..."
                    )
                else:
                    return api_result["response"]

        print("Reached maximum retries. Aborting.")
        return ""

def unit_test_infer(estimate_idx:int):
    from aiwolfk2b.utils.helper import load_default_GameInfo,load_default_GameSetting,load_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.ParseRuruLogToGameAttribution import load_sample_GameAttirbution

    config_path = current_dir.parent / "config.ini"
    config_ini = load_config(config_path)
    # game_info = load_default_GameInfo()
    # game_setting = load_default_GameSetting()

    game_info_list,game_setting = load_sample_GameAttirbution(estimate_idx)
    
    estimator = BERTRoleEstimationModel(config_ini)
    inference_module = BERTRoleInferenceModule(config_ini,estimator)
    
    estimator.initialize(game_info_list,game_setting)
    inference_module.initialize(game_info_list,game_setting)
    
    agent = Agent(estimate_idx)
    result = inference_module.infer(agent,game_info_list,game_setting)
    
    pred_role = max(result.probs.items(), key=lambda x: x[1])[0]
    print(f"{result.agent} is {pred_role.name} bacause {result.reason}")
    

if __name__ == "__main__":
    unit_test_infer(3)
