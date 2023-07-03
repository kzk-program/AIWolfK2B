from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractQuestionProcessingModule, AbstractRoleInferenceModule, AbstractStrategyModule, OneStepPlan, ActionType, RoleInferenceResult
from configparser import ConfigParser
from aiwolfk2b.AttentionReasoningAgent.SimpleModules import SimpleRoleInferenceModule, SimpleStrategyModule, RandomRoleEstimationModel
from aiwolfk2b.utils.helper import load_default_config,get_openai_api_key,load_default_GameInfo,load_default_GameSetting
from aiwolf import GameInfo, GameSetting
from enum import Enum
from aiwolf.agent import Agent,Role
from typing import List, Optional
import openai
import Levenshtein
import numpy as np

class QuestionType(Enum):
    """質問の種類"""
    ACTION_REASON = "ACTION_REASON"
    """過去の行動の理由"""
    ACTION_PLAN = "ACTION_PLAN"
    """将来の行動のプラン"""
    ROLE_INFERENCE = "ROLE_INFERENCE"
    """役職推定"""

class GPT3API:
    """
    GPT3とのやりとりを行うためのクラス
    """
    def __init__(self):
        openai.api_key = get_openai_api_key()

    def complete(self, input:str,model="text-davinci-003",max_tokens=100,temperature=0)->str:
        """GPT3でCompletionを行う"""
        response = openai.Completion.create(engine=model,
            prompt=input,
            max_tokens=max_tokens,
            temperature=temperature)
        return response['choices'][0]['text']

class QuestionProcessingModule(AbstractQuestionProcessingModule):
    """
    質問処理モジュール
    """
    def __init__(self,config:ConfigParser,role_inference_module:AbstractRoleInferenceModule, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config,role_inference_module, strategy_module)
        self.gpt3_api = GPT3API()
    
    def process_question(self,question: str, questioner: Agent ,game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        self._game_info = game_info
        self._game_setting = game_setting

        # 質問の種類を分類する
        question_type = self._classify_question(question)

        if question_type == None:
            return OneStepPlan("何を意図した質問か分からなかったから", ActionType.TALK, f">>{questioner}何を言ってるか分かりません。")
        
        elif question_type == QuestionType.ACTION_REASON:
            question_actiontype = self._classify_question_actiontype(question)
            return OneStepPlan(f"{questioner}に質問されたから", ActionType.TALK, f">>{questioner} {self._answer_action_reason(question, question_actiontype)}")
        
        elif question_type == QuestionType.ACTION_PLAN:
            question_actiontype = self._classify_question_actiontype(question)
            return self._answer_action_plan(question, question_actiontype, questioner)
        
        elif question_type == QuestionType.ROLE_INFERENCE:
            return self._answer_role_inference(question, questioner)

        else:
            raise NotImplementedError("未実装")


    def _classify_question(self, question: str) -> Optional[QuestionType]:
        """質問を分類する。分類できないときはNoneを返す"""
        prompt = f"""以下の質問に対し、質問の種類が 1 過去の行動の理由 2 将来の行動のプラン 3 役職推定 4.どれでも無い のどれかに分類します。ただし、「疑う」「怪しい」などと言ったときは人狼の役職推定を指します。
「なぜあなたはAgent[01]を占ったのですか」 :1
「あなたは誰に投票しますか」:2
「あなたは誰が人狼だと思いますか」:3
「人狼はあなたを明日殺すと思いますか」:4
「{question}」 :"""

        question_type_num = self.closest_str(["1", "2", "3", "4"], self.gpt3_api.complete(prompt).strip())
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
        prompt = f"""以下の質問に対し、質問の種類が 1 占い行為 2 護衛行為 3 投票行為 4 襲撃行為 5 発言(カミングアウトや、行為の呼びかけ、行為の宣言等を含む) のどれかに分類します。ただし、投票することを「吊る」と言うこともあることに注意してください。
「なぜあなたはAgent[01]を占ったのですか」 :1
「なぜあなたはAgent[01]を守ったのか？」 :2
「Agent[02]に投票したのは何故か。」:3
「Agent[02]を襲撃したのは何故か。」:4
「COするつもりはありますか。」 :5
「なぜAgent[01]に投票するよう呼びかけたのか？」 :5
「{question}」 :"""
        question_actiontype_num = self.closest_str(["1", "2", "3", "4", "5"], self.gpt3_api.complete(prompt).strip())
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
        
        # historyから、該当するactiontypeのOneStepPlanを取ってくる
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
            prompt = f"""質問は、誰{verb}した理由を聞いてますか？Agent[01]~Agent[{self._game_setting.player_num:02d}]のどれかを答えてください。
---
質問:
「>>Agent[02] なんでAgent[04]{verb}したんじゃ？」
正解:
Agent[04]
---
質問:
"""
            prompt += "「" + question + "」\n"
            target_agent = self.closest_str([str(agent) for agent in self._game_info.agent_list],self.gpt3_api.complete(prompt).strip())
            for one_step_plan in the_actiontype_history_list[::-1]:  #最新のから検索
                if str(one_step_plan.action) == target_agent:
                    return one_step_plan
            return None
        
        else:
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
            corresponding_num = int(self.closest_str([str(x) for x in range(len(the_actiontype_history_list)+1)],self.gpt3_api.complete(prompt).strip()))
            if corresponding_num == 0:
                return None
            else:
                return the_actiontype_history_list[corresponding_num-1]
        
    def _answer_action_plan(self, question:str, question_actiontype:ActionType, questioner:Agent) -> OneStepPlan:
        """
        行動予定質問に対し回答する。
        Args:
            question (str): 質問
            question_actiontype (ActionType): 質問の行動タイプ

        Returns:
            str: 回答
        """

        if question_actiontype == ActionType.ATTACK:
            return OneStepPlan("人狼ではないから", ActionType.TALK, "そもそも私は人狼ではありません。")
        elif question_actiontype == ActionType.TALK:
            return OneStepPlan("質問の意図が理解できないから", ActionType.TALK, "どういうことですか")
        
        corresponding_action = self._corresponding_future_action(question, question_actiontype)
        if corresponding_action == None:
            return OneStepPlan("深く考えていないから", ActionType.TALK, "まだどうするか決めていません。")
        
        if question_actiontype == ActionType.DIVINE:
            return OneStepPlan(corresponding_action.reason, ActionType.TALK, f">>{questioner} {str(corresponding_action.action)}を占うつもりです。")
        elif question_actiontype == ActionType.GUARD:
            return OneStepPlan(corresponding_action.reason, ActionType.TALK, f">>{questioner} {str(corresponding_action.action)}を護衛するつもりです。")
        elif question_actiontype ==  ActionType.VOTE:
            return OneStepPlan(corresponding_action.reason, ActionType.TALK, f">>{questioner} {str(corresponding_action.action)}に投票するつもりです。")
        else:
            raise ValueError("ActionTypeが不正: " + question_actiontype.value)


    def _corresponding_future_action(self, question:str, question_actiontype:ActionType) -> Optional[OneStepPlan]:
        """
        行動予定質問に対し、該当する行動を返す
        """
        the_actiontype_plan_list = []
        for one_step_plan in self.strategy_module.future_plan:
            if one_step_plan.action_type == question_actiontype:
                the_actiontype_plan_list.append(one_step_plan)

        if len(the_actiontype_plan_list) == 0:
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
            target_agent = self.closest_str(["Agent[" + "{:02}".format(x) + "]" for x in range(1, 6)],self.gpt3_api.complete(prompt).strip())
            for one_step_plan in the_actiontype_plan_list[::-1]:  #最新のから検索
                if str(one_step_plan.action) == target_agent:
                    return one_step_plan
            return None
        else:
            raise NotImplementedError("未実装")

    def _answer_role_inference(self, question:str, questioner:Agent) -> OneStepPlan:
        """
        疑わしいエージェント質問に対し、疑わしいエージェントを返す
        人狼の場合はあとで実装方法を考える
        """
        prompt = f"""何の役職だと思われる人を聞いていますか？1 人狼 2 狂人 3 占い師  4 村人 0 それ以外で答えてください。ただし、「疑う」「怪しい」などと言ったときは人狼のことを指します。
---
「狂人は誰だと思いますか？」 :2
「>>Agent[02] 一番占い師っぽいと思ってるのは誰？」 :3
「村人は誰かな？」 :4
「誰が一番怪しいと思う？」 :1
「誰が作曲家だと思う？」 :0
「{question}」 :
"""
        questioned_role = self.closest_str([str(x) for x in range(5)],self.gpt3_api.complete(prompt).strip())
        questioned_role:Optional[Role] = [None, Role.WEREWOLF, Role.POSSESSED, Role.SEER, Role.VILLAGER][int(questioned_role)]
        if questioned_role == None:
            return OneStepPlan("質問の意図が分からなかったので", ActionType.TALK, f">>{questioner} どういうことか分かりません。")
        questioned_role_str = self.role_to_japanese(questioned_role)
        role_inference_results:List[RoleInferenceResult] = []
        for agent in self._game_info.agent_list:
            role_inference_results.append(self.role_inference_module.infer(agent, [self._game_info], self._game_setting))
        max_prob = max([x.probs[questioned_role] for x in role_inference_results])
        high_prob_results = [x for x in role_inference_results if x.probs[questioned_role] > max_prob-0.1]
        if len(high_prob_results) == 1:
            return OneStepPlan(high_prob_results[0].reason, ActionType.TALK, f">>{questioner} {high_prob_results[0].agent}が{questioned_role_str}ではないかと思っています。")
        elif len(high_prob_results) == 2:
            return OneStepPlan(f"{high_prob_results[0].agent}に関しては{high_prob_results[0].reason}、{high_prob_results[1].agent}に関しては{high_prob_results[1].reason}", ActionType.TALK, f">>{questioner} {high_prob_results[0].agent}と{high_prob_results[1].agent}が{questioned_role_str}の可能性が高いと思います。")
        else:
            return OneStepPlan(f"まだ決定的な情報が無いので", ActionType.TALK, f">>{questioner} 誰が{questioned_role_str}か分かっていません。")

    def role_to_japanese(self, role:Role)->str:
        """Role型を日本語str型に変える関数。これはRoleで作って欲しい感じもある。"""
        if role == Role.WEREWOLF:
            return "人狼"
        elif role == Role.SEER:
            return "占い師"
        elif role == Role.POSSESSED:
            return "狂人"
        elif role == Role.VILLAGER:
            return "村人"
        
    def closest_str(self, str_list:List[str], target_str:str)->str:
        """str_listの中からtarget_strに最も近い文字列を返す"""
        min_distance = np.inf
        min_str = ""
        for str in str_list:
            distance = Levenshtein.distance(str, target_str)
            if distance < min_distance:
                min_distance = distance
                min_str = str
        return min_str



if __name__ == "__main__":
    config_ini = load_default_config()
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    
    role_estimation_model = RandomRoleEstimationModel(config_ini)
    role_inference_module = SimpleRoleInferenceModule(config_ini, role_estimation_model)
    strategy_module = SimpleStrategyModule(config_ini, role_estimation_model, role_inference_module)
    
    
    question_processing_module = QuestionProcessingModule(config_ini,role_inference_module,strategy_module)
    question_processing_module.initialize(game_info, game_setting)
    question_processing_module.strategy_module.history = [OneStepPlan("怪しい動きをしてたから", ActionType.TALK, "Agent[02]が人狼だと思う"), OneStepPlan("怪しい動きをしてたから", ActionType.VOTE, Agent(2))]
    print(question_processing_module.process_question("なぜAgent[02]を怪しんだんじゃ？", Agent(1), game_info, game_setting).action)
    print(question_processing_module.process_question("君は誰が怪しいと思う？", Agent(2), game_info, game_setting).action)