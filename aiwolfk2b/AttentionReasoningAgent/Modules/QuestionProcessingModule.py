from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractQuestionProcessingModule, AbstractRoleInferenceModule, AbstractStrategyModule, OneStepPlan, ActionType
from configparser import ConfigParser
from aiwolfk2b.AttentionReasoningAgent.SimpleModules import SimpleRoleInferenceModule, SimpleStrategyModule, RandomRoleEstimationModel
from aiwolf import GameInfo, GameSetting
from aiwolf.gameinfo import _GameInfo
from aiwolf.gamesetting import _GameSetting
from enum import Enum
from aiwolf.agent import Agent,Role
from typing import List, Optional
import configparser
import errno
import os
import openai
import Levenshtein

class QuestionType(Enum):
    """質問の種類"""
    ACTION_REASON = "ACTION_REASON"
    ACTION_PLAN = "ACTION_PLAN"
    ROLE_INFERENCE = "ROLE_INFERENCE"

class GPT3API:
    """
    GPT3とのやりとりを行うためのクラス
    """
    def __init__(self):
        parent_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
        with open(parent_dir + '/openAIAPIkey.txt', "r") as f:
            openai.api_key = f.read().strip()

    def complete(self, input:str)->str:
        """GPT3でCompletionを行う"""
        response = openai.Completion.create(engine="text-davinci-003",
            prompt=input,
            max_tokens=100,
            temperature=0)
        return response['choices'][0]['text']

def closest_str(str_list:List[str], target_str:str)->str:
    """str_listの中からtarget_strに最も近い文字列を返す"""
    min_distance = 100000
    min_str = ""
    for str in str_list:
        distance = Levenshtein.distance(str, target_str)
        if distance < min_distance:
            min_distance = distance
            min_str = str
    return min_str

class QuestionProcessingModule(AbstractQuestionProcessingModule):
    """
    質問処理モジュール
    """
    def __init__(self,config:ConfigParser,role_inference_module:AbstractRoleInferenceModule, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config,role_inference_module, strategy_module)
        self.gpt3_api = GPT3API()
    
    def process_question(self,question: str, questioner: Agent ,game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        question_type = self._classify_question(question)
        if question_type == None:
            return OneStepPlan("何を意図した質問か分からなかったから", ActionType.TALK, str(questioner)+"、何を言ってるか分かりません。")
        
        if question_type == QuestionType.ACTION_REASON:
            question_actiontype = self._classify_question_actiontype(question)
            return OneStepPlan(str(questioner)+"に質問されたから", ActionType.TALK, str(questioner)+"、"+self._answer_action_reason(question, question_actiontype))
        
        else:
            raise NotImplementedError("未実装")

    def _classify_question(self, question: str) -> Optional[QuestionType]:
        """質問を分類する。分類できないときはNoneを返す"""
        prompt = f"""以下の質問に対し、質問の種類が 1 過去の行動の理由 2 将来の行動のプラン 3 役職推定 4.どれでも無い のどれかに分類します。
「なぜあなたはAgent[01]を占ったのですか」 :1
「あなたは誰に投票しますか」:2
「あなたは誰が人狼だと思いますか」:3
「人狼はあなたを明日殺すと思いますか」:4
「{question}」 :"""
        question_type_num = closest_str(["1", "2", "3", "4"], self.gpt3_api.complete(prompt).strip())
        if question_type_num == "1":
            return QuestionType.ACTION_REASON
        elif question_type_num == "2":
            return QuestionType.ACTION_PLAN
        elif question_type_num == "3":
            return QuestionType.ROLE_INFERENCE
        elif question_type_num == "4":
            return None
        else:
            raise ValueError("question_type_numが1~4のどれでもない")

    def _classify_question_actiontype(self, question: str) -> ActionType:
        """質問の種類が行動理由か行動予定のとき、具体的にどのActionTypeのことか判定する"""
        prompt = f"""以下の質問に対し、質問の種類が 1 占い行為 2 護衛行為 3 投票行為 4 襲撃行為 5 発言(カミングアウトや、行為の呼びかけ、行為の宣言等を含む) のどれかに分類します。
「なぜあなたはAgent[01]を占ったのですか」 :1
「なぜあなたはAgent[01]を守ったのか？」 :2
「Agent[02]に投票したのは何故か。」:3
「Agent[02]を襲撃したのは何故か。」:4
「COするつもりはありますか。」 :5
「なぜAgent[01]に投票するよう呼びかけたのか？」 :5
「{question}」 :"""
        question_actiontype_num = closest_str(["1", "2", "3", "4", "5"], self.gpt3_api.complete(prompt).strip())
        if question_actiontype_num == "1":
            return ActionType.DIVINE
        elif question_actiontype_num == "2":
            return ActionType.GUARD
        elif question_actiontype_num == "3":
            return ActionType.VOTE
        elif question_actiontype_num == "4":
            return ActionType.ATTACK
        elif question_actiontype_num == "5":
            return ActionType.TALK
        else:
            raise ValueError("question_actiontype_numが1~5のどれでもない")

    
    def _answer_action_reason(self, question: str, question_actiontype:ActionType) -> str:
        """
        行動理由質問に対し回答する。
        人狼のATTACK以外全部正直に答える（戦略立案モジュールのhistoryから該当するのを探し、そのreasonを返す）
        """
        if question_actiontype == ActionType.ATTACK:
            return "そもそも私は人狼ではありません。"
        
        corresponding_action = self._corresponding_past_action(question, question_actiontype)
        if corresponding_action == None:
            return "何の話か分かりません。"

        if question_actiontype == ActionType.TALK:
            return "その発言をしたのは、" + corresponding_action.reason + "です。"
        elif question_actiontype == ActionType.DIVINE:
            return str(corresponding_action.action)+"を占ったのは、" + corresponding_action.reason + "です。"
        elif question_actiontype == ActionType.GUARD:
            return str(corresponding_action.action)+"を守ったのは、" + corresponding_action.reason + "です。"
        elif question_actiontype ==  ActionType.VOTE:
            return str(corresponding_action.action)+"に投票したのは、" + corresponding_action.reason + "です。"
        else:
            raise ValueError("ActionTypeが不正: " + question_actiontype.value)

    def _corresponding_past_action(self, question: str, question_actiontype:ActionType) -> Optional[OneStepPlan]:
        """
        行動理由質問に関して、該当する行動を返す
        """

        the_actiontype_history_list = []
        for one_step_plan in self.strategy_module.history:
            if one_step_plan.action_type == question_actiontype:
                the_actiontype_history_list.append(one_step_plan)

        if len(the_actiontype_history_list) == 0:
            return None
        
        if question_actiontype != ActionType.TALK:
            if question_actiontype == ActionType.DIVINE:
                verb = "を投票"
            elif question_actiontype == ActionType.GUARD:
                verb = "を護衛"
            elif question_actiontype == ActionType.VOTE:
                verb = "に投票"
            prompt = f"""質問は、誰{verb}した理由を聞いてますか？Agent[01]~Agent[05]のどれかを答えてください。
---
質問:
「>>Agent[02] なんでAgent[04]{verb}したんじゃ？」
正解:
Agent[04]
---
質問:
"""
            prompt += "「" + question + "」\n"
            target_agent = closest_str(["Agent[" + "{:02}".format(x) + "]" for x in range(1, 6)],self.gpt3_api.complete(prompt).strip())
            for one_step_plan in the_actiontype_history_list[::-1]:  #最新のから検索
                if str(one_step_plan.action) == target_agent:
                    return one_step_plan
            return None
        

        prompt = """質問に最も近い発言の番号を答えてください。どれも合致しない場合は0と答えてください。
---
質問：
「なぜあなたはAgent[01]を人狼だと疑ったのですか。」
発言：
1 「占い師COします。Agent[02]は人間です。」
2 「Agent[01]、Agent[02]を占ったのは、発言が少なくて人狼だと思ったからです。」
3 「Agent[01]が人狼だと思う。」
答え:
3
---
質問：
"""
        prompt += "「" + question + "」\n"
        for i, one_step_plan in enumerate(the_actiontype_history_list):
            prompt += f"{i+1} {one_step_plan.action}\n"
        prompt += "答え:\n"
        corresponding_num = int(closest_str([str(x) for x in range(len(the_actiontype_history_list)+1)],self.gpt3_api.complete(prompt).strip()))
        if corresponding_num == 0:
            return None
        else:
            return the_actiontype_history_list[corresponding_num-1]
        
    def _corresponding_future_action(self, question:str, ) -> OneStepPlan:
        """
        行動予定質問に対し、該当する行動を返す
        人狼のATTACK以外全部正直に答える
        """
        pass

    def _suspicious_agent() -> OneStepPlan:
        """
        疑わしいエージェント質問に対し、疑わしいエージェントを返す
        人狼の場合はあとで実装方法を考える
        """
        pass


if __name__ == "__main__":
    import pickle
    config_ini = configparser.ConfigParser()
    config_ini_path = '/home/meip-users/aiwolf_ara/AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/config.ini'

    # iniファイルが存在するかチェック
    if os.path.exists(config_ini_path):
        # iniファイルが存在する場合、ファイルを読み込む
        with open(config_ini_path, encoding='utf-8') as fp:
            config_ini.read_file(fp)
    else:
        # iniファイルが存在しない場合、エラー発生
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)
    
    role_estimation_model = RandomRoleEstimationModel(config_ini)
    role_inference_module = SimpleRoleInferenceModule(config_ini, role_estimation_model)
    strategy_module = SimpleStrategyModule(config_ini, role_estimation_model, role_inference_module)
    with open("/home/meip-users/aiwolf_ara/AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/game_info.pkl", mode="rb") as f:
        game_info = pickle.load(f)
    with open("/home/meip-users/aiwolf_ara/AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/game_setting.pkl", mode="rb") as f:
        game_setting = pickle.load(f)
    
    question_processing_module = QuestionProcessingModule(config_ini,role_inference_module,strategy_module)
    question_processing_module.initialize(game_info, game_setting)
    question_processing_module.strategy_module.history = [OneStepPlan("怪しい動きをしてたから", ActionType.VOTE, Agent(2))]
    print(question_processing_module.process_question("なぜAgent[02]に投票したんじゃ？", Agent(1), game_info, game_setting).action)
    print(question_processing_module.process_question("なぜAgent[03]に投票したんじゃ？", Agent(1), game_info, game_setting).action)