import os,random,re
from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union, Optional
from enum import Enum
import numpy as np

from aiwolf import GameInfo, GameSetting
from aiwolf.utterance import Talk
from aiwolf.agent import Agent,Role, Species

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,RoleEstimationResult,AbstractStrategyModule,AbstractRoleInferenceModule,RoleInferenceResult,OneStepPlan, ActionType
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import GPTAPI,ChatGPTAPI
from aiwolfk2b.utils.helper import load_default_config,load_default_GameInfo,load_default_GameSetting,calc_closest_str,make_gpt_qa_prompt

class GameLog:
    """ゲームのログを保存するクラス"""
    
    _talk_list:List[Talk]
    """talkの履歴をゲームを通して保存"""
    _log:str
    """talkの履歴を文字列で保存"""
    _log_talk_numbers:int
    """logで保存しているtalkの数"""
    _talk_list_updated:bool
    """talk_listが更新されたか=logを更新する必要があるかどうか"""
    @property
    def log(self)->str:
        if self._talk_list_updated:
            #更新を記録
            for talk in self._talk_list[self._log_talk_numbers:]:
                self._log += f"{talk.day}日目 {talk.agent}の発言 :{talk.text}\n"
            #更新済みに変更
            self._talk_list_updated = False
            self._log_talk_numbers = len(self._log)
        #文字数が多いとGPTに入力できないため、最後のtruncate_words文字を返す
        if len(self._log) > self.truncate_words:
            return self._log[-self.truncate_words:]
        else:
            return self._log #ログが短いときはそのまま返す
    
    def __init__(self, game_info:GameInfo, game_setting:GameSetting,truncate_words = 2000) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        truncate_words : int, optional
            入力最大文字数(GPTに入力できなくなるため), by default 2000
        """
        self._log = ""
        self._talk_list = []
        self._log_talk_numbers = 0
        self._talk_list_updated = True
        self.truncate_words = truncate_words
    
    def update(self, game_info:GameInfo, game_setting:GameSetting)->None:
        self._talk_list.extend(game_info.talk_list)
        self._talk_list_updated = True


class TalkTopic(Enum):
    """会話のトピック"""
    ROLEACTION_RESULT = "ROLEACTION_RESULT"
    ROLEACTION_REACTION = "ROLEACTION_REACTION"
    WHO_TO_VOTE = "WHO_TO_VOTE"

class ComingOutStatus:
    """
    各エージェントのカミングアウトの状態
    1日目の最初の会話より前ならUNC, COしたらその役職、COしなかったらVILLAGER
    """
    all_comingout_status:Dict[Agent,Role] = {}
    def __init__(self, game_info:GameInfo, game_setting:GameSetting) -> None:
        for agent in game_info.agent_list:
            self.all_comingout_status[agent] = Role.UNC
            self.gpt3_api =GPTAPI()

    def update(self, game_info:GameInfo, game_setting:GameSetting)->None:
        if not self.is_all_comingout():
            for talk in game_info.talk_list:
                explanation = "以下の発言に対し、カミングアウト(役職の公開)かどうかとその役職を判定してください。カミングアウトが無ければ無しとこたえてください。役職は、人狼・狂人・占い師・村人の4種類で答えてください。"
                examples = {
                    "占いCOします。Agentは白でした。": "占い師",
                    "占い師だ。Agentは人狼だった": "占い師",
                    "占い師をやってみるかな、ってことでCOするぜ。": "占い師",
                    "ガオー、人狼だぞー": "人狼",
                    "人狼として頑張るぞ": "人狼",
                    "俺は村人です。仲良くやりましょう！": "村人",
                    "僕は村人、よろしく": "村人",
                    "あら、村人なのね。一緒に頑張りましょうわ、ね？": "村人",
                    "わたし、村っ子だよ！がんばるぞー！": "村人",
                    "わたしは狂人です。人狼をサポートします。": "狂人",
                    "みなさんよろしくお願いします": "無し",
                    "よろー": "無し",
                    "お元気ですか？": "無し",
                    "こんにちは": "無し",
                }
                #テキストの前処理として、自分以外のAgent[数字]をAgentに置き換えたうえで質問とする
                question = re.sub(r"Agent\[(\d+)\]",lambda m: f"Agent" if int(m.group(1)) != game_info.me.agent_idx else f"{game_info.me}" ,talk.text)
                prompt = self.gpt3_api.make_gpt_qa_prompt(explanation, examples,question)
                
                response = self.gpt3_api.complete(prompt)
                CO_role = calc_closest_str(["無し","人狼","狂人","占い師","村人"], response)
                if CO_role == "無し":
                    if self.all_comingout_status[talk.agent] == Role.UNC:
                        self.all_comingout_status[talk.agent] = Role.VILLAGER
                elif CO_role == "人狼":
                    self.all_comingout_status[talk.agent] = Role.WEREWOLF
                elif CO_role == "狂人":
                    self.all_comingout_status[talk.agent] = Role.POSSESSED
                elif CO_role == "占い師":
                    self.all_comingout_status[talk.agent] = Role.SEER
                elif CO_role == "村人":
                    self.all_comingout_status[talk.agent] = Role.VILLAGER
                else:
                    raise ValueError

    def is_all_comingout(self)->bool:
        for agent, role in self.all_comingout_status.items():
            if role == Role.UNC:
                return False
        return True

class StrategyModule(AbstractStrategyModule):
    """戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config,role_estimation_model,role_inference_module)

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        self.history = []
        self.future_plan = []
        self.next_plan = None
        self.today = 0
        self.today_talked_topic:Dict[TalkTopic, bool] = {TalkTopic.ROLEACTION_RESULT:False, TalkTopic.ROLEACTION_REACTION:False, TalkTopic.WHO_TO_VOTE:False}
        self.comingout_status = ComingOutStatus(game_info, game_setting)
        self.game_log = GameLog(game_info, game_setting)
        self.chatgpt_api = ChatGPTAPI()
        self.has_greeted = False
        self.game_info = game_info
        self.game_setting = game_setting

    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        #初日の処理
        if game_info.day == 0:
            talk_plan:OneStepPlan = None
            if not self.has_greeted: 
                talk_plan = OneStepPlan("挨拶をする必要があるから",ActionType.TALK,"よろしくお願いします！")
                self.has_greeted = True
            else:
                talk_plan = OneStepPlan("挨拶はしたから",ActionType.TALK,"Over")
            return talk_plan
        
        #日にちが変わったらtopicをリセット
        if game_info.day != self.today:
            self.today = game_info.day
            self.reset_talked_topic()

        self.comingout_status.update(game_info, game_setting)
        self.game_log.update(game_info, game_setting)

        # next_planがあればそれを言う
        if self.next_plan != None:
            if self.next_plan.action_type == ActionType.TALK:
                plan = self.next_plan
                self.next_plan = None
                return plan
        
        for topic, is_talked in self.today_talked_topic.items():
            if is_talked == False:
                if topic == TalkTopic.ROLEACTION_RESULT:
                    role_action_result = self.talk_roleaction_result(game_info, game_setting)
                    if role_action_result != None:
                        print("role_action_result", role_action_result)
                        talk_plan = OneStepPlan("勝つために自分の役職に関わる情報をみんなに伝えたいから",ActionType.TALK,role_action_result)
                        return talk_plan
                elif topic == TalkTopic.ROLEACTION_REACTION:
                    roleaction_reaction =  self.talk_roleaction_reaction(game_info, game_setting)
                    if roleaction_reaction != None:
                        self.today_talked_topic[topic] = True
                        print("roleaction_reaction", roleaction_reaction)
                        talk_plan = OneStepPlan("勝つために情報を得たいから",ActionType.TALK,roleaction_reaction)
                        return talk_plan
                elif topic == TalkTopic.WHO_TO_VOTE:
                    who_to_vote = self.talk_who_to_vote(game_info, game_setting)
                    if who_to_vote != None:
                        self.today_talked_topic[topic] = True
                        print("who_to_vote", who_to_vote)
                        talk_plan = OneStepPlan("勝つために周りの投票先を知りたいから",ActionType.TALK,who_to_vote)
                        return talk_plan
                
        # 会話デッキを使い果たしたら
        no_topic = self.talk_no_topic(game_info, game_setting)
        print("no topic", no_topic)
        talk_plan = OneStepPlan("特に話すことがないから",ActionType.TALK,no_topic)
        return talk_plan

    
    def vote(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """投票"""
        # 投票先が既に要求処理モジュールで決定していた場合
        for one_plan in self.future_plan:
            if one_plan.action_type == ActionType.VOTE:
                plan = one_plan
                self.future_plan.remove(one_plan)
                return plan

        # 自前で決める場合
        evaluation = self.vote_evaluation(game_info, game_setting)
        #最大の評価値を持つプランを選択
        max_eval_vote = evaluation[np.argmax([eval_val for _, eval_val in evaluation])][0]
        #もし人狼側ならwerewolfの理由をこじつける
        if game_info.my_role == Role.WEREWOLF or game_info.my_role == Role.POSSESSED:
            inf_result = self.role_inference_module.infer(max_eval_vote.action,[game_info], game_setting,Role.WEREWOLF)
            max_eval_vote.reason = inf_result.reason

        return max_eval_vote
    
    def vote_evaluation(self, game_info: GameInfo, game_setting: GameSetting) -> List[Tuple[OneStepPlan, float]]:
        """
        投票先の評価
        評価値(float)が高いほど投票おすすめ度が高い
        """

        evaluation = []
        #注意：同一のagent_idxに対してagentのインスタンスが一意でないためわざわざidxで判定している
        alive_agent_idx_list = [agent.agent_idx for agent in game_info.alive_agent_list]
        #人狼側の場合、誰に投票するか決める
        if game_info.my_role == Role.WEREWOLF or game_info.my_role == Role.POSSESSED:
            #推定結果を取得
            estimate_results = self.get_survive_agent_estimation_results(game_info, game_setting)
            # print("DEBUG ", estimate_results)
            # print("self.game_info.me", self.game_info.me)
            #占い師が生きている確率が高い場合、占い師の確率が高いエージェントをおすすめ度とし、死んでたら狂人の確率が低いエージェントをおすすめ度とする
            if self.check_survive_seer(estimate_results):
                #最も占い師の確率が高いエージェントに投票する
                for est_result in estimate_results:
                    #自分は対象外
                    if est_result.agent.agent_idx == game_info.me.agent_idx:
                        continue
                    if est_result.agent.agent_idx in alive_agent_idx_list: #生存中のエージェントのみを対象に
                        evaluation.append((OneStepPlan("最も人狼っぽかったから",ActionType.VOTE,est_result.agent), est_result.probs[Role.SEER]))
            else:
                #最も狂人の確率が低いエージェントに投票する
                for est_result in estimate_results:
                    #自分は対象外
                    if est_result.agent.agent_idx == game_info.me.agent_idx:
                        continue
                    if est_result.agent.agent_idx in alive_agent_idx_list: #生存中のエージェントのみを対象に
                        evaluation.append((OneStepPlan("最も人狼っぽかったから",ActionType.VOTE,est_result.agent), 1- est_result.probs[Role.POSSESSED]))        
        #村人側の場合、誰に投票するか決める
        else:
            inf_results = self.get_survive_agent_inference_results(game_info, game_setting)
            #最も人狼の確率が高いエージェントに投票する
            for inf_result in inf_results:
                #自分は対象外
                if inf_result.agent.agent_idx == game_info.me.agent_idx:
                    continue
                if inf_result.agent.agent_idx in alive_agent_idx_list: #生存中のエージェントのみを対象に
                # 人狼と狂人の重み付けをハードコーディングしてる、ごめん、許して
                    eval_val = inf_result.probs[Role.WEREWOLF] + 0.5 * inf_result.probs[Role.POSSESSED]
                    evaluation.append((OneStepPlan(inf_result.reason,ActionType.VOTE,inf_result.agent), eval_val))
        
        return evaluation
    
    def attack(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """襲撃"""
        #各エージェントの役職を推定する
        est_results:List[RoleEstimationResult] = self.get_survive_agent_estimation_results(game_info, game_setting)

        #占い師が生きている確率が高い場合
        if self.check_survive_seer(est_results):
            #最も占い師の確率が高いエージェントに襲撃する
            max_seer_agent = max(est_results, key=lambda x: x.probs[Role.SEER]).agent
            attack_plan = OneStepPlan("最も占い師の確率が高いから",ActionType.ATTACK,max_seer_agent)
        else:
            #最も狂人の確率が低いエージェントに襲撃する
            min_poss_agent = min(est_results, key=lambda x: x.probs[Role.POSSESSED]).agent
            attack_plan = OneStepPlan("最も狂人の確率が低いから",ActionType.ATTACK,min_poss_agent)
        return attack_plan
    
    def divine(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """占い"""
        #各エージェントの役職を推定する
        est_results:List[RoleEstimationResult] = self.get_survive_agent_estimation_results(game_info, game_setting)
        
        #人狼である確率が最も高い結果を選ぶ(ただし、自分は除く)
        max_wolf_agent = max(est_results, key=lambda x: x.probs[Role.WEREWOLF] if x.agent.agent_idx != game_info.me.agent_idx else -1.0).agent

        #最も人狼である確率が高いエージェントの役職の根拠を取得
        inf_result = self.role_inference_module.infer(max_wolf_agent,[game_info],game_setting,Role.WEREWOLF)
        
        divine_plan = OneStepPlan(inf_result.reason,ActionType.DIVINE,max_wolf_agent)
        return divine_plan
    
    
    def guard(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """護衛"""
        """５人人狼では不要"""
        raise NotImplementedError
    
    def whisper(self, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        """人狼同士の相談"""
        """５人人狼では不要"""
        raise NotImplementedError
        
    def plan(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """行動計画"""
        pass

    def update_history(self, game_info: GameInfo, game_setting: GameSetting, executed_plan: OneStepPlan) -> None:
        """過去の行動履歴の更新"""
        return super().update_history(game_info, game_setting, executed_plan)
    
    def update_future_plan(self, game_info: GameInfo, game_setting: GameSetting, executed_plan: OneStepPlan) -> None:
        """未来の行動履歴の更新"""
        return super().update_future_plan(game_info, game_setting, executed_plan)
    
    def weight(self, role: Role) -> List[float]:
        """重みつき：[村人,占い師,狂人,人狼]"""
        if role == Role.VILLAGER:
            return [1,0,0,0]
        elif role == Role.SEER:
            return [0,1,0,0]
        elif role == Role.POSSESSED:
            return [0,0,1,0]
        else:
            return [0,0,0.5,1]
        
    def check_survive_seer(self, result_list: List[RoleEstimationResult]) -> bool:
        """占い師が生きているかinf_listどうか判定する"""
        #占い師である確率の合計値
        sum_seer = 0
        for inf in result_list:
            sum_seer += inf.probs[Role.SEER]
        #占い師がいる可能性が高いかどうかの閾値
        th_seer = 0.7
        if sum_seer > th_seer:
            return True
        else:
            return False
        
    def get_survive_agent_inference_results(self, game_info: GameInfo, game_setting: GameSetting,inferred_role:Role=None)-> List[RoleInferenceResult]:
        """
        生存しているエージェントの推論結果を取得する
        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        inferred_role : Role, optional
            推論された役職(推論対象のエージェントがこの役職であると推論したい場合に指定。Noneの場合はInferenceModuleが役職も推論), by default None

        Returns
        -------
        List[RoleInferenceResult]
            推論結果のリスト
        """
        inf_results:List[RoleInferenceResult] = []
        for agent in game_info.alive_agent_list:
            inf_results.append(self.role_inference_module.infer(agent, [game_info], game_setting, inferred_role))
        return inf_results    
        
    def get_survive_agent_estimation_results(self, game_info: GameInfo, game_setting: GameSetting)-> List[RoleEstimationResult]:
        """
        生存しているエージェントの推定結果を取得する
        
        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
            
        Returns
        -------
        List[RoleEstimationResult]
            推定結果のリスト
        """
        estimate_results:List[RoleEstimationResult] = []
        for agent in game_info.alive_agent_list:
            estimate_results.append(self.role_estimation_model.estimate(agent,[game_info], game_setting))
        return estimate_results
    
    def species_to_japanese(self, species: Species) -> str:
        """種族を日本語に変換する"""
        if species == Species.HUMAN:
            return "人間"
        elif species == Species.WEREWOLF:
            return "人狼"
        else:
            raise ValueError("不正な種族です")
        
    def reset_talked_topic(self)->None:
        """話したトピックをリセットする"""
        for topic in self.today_talked_topic.keys():
            self.today_talked_topic[topic] = False
        return
    
    def talk_roleaction_result(self, game_info:GameInfo, game_setting:GameSetting) -> Optional[str]:
        """占い結果を言う。霊媒師がいる場合は霊媒結果を言うことも想定した関数。"""
        self.today_talked_topic[TalkTopic.ROLEACTION_RESULT] = True
        if game_info.my_role == Role.SEER or game_info.my_role == Role.POSSESSED:
            #　占い結果を言う
            if game_info.my_role == Role.SEER:
                # 真占い師のとき
                divine_target = game_info.divine_result.target
                divine_result = game_info.divine_result.result
            else:
                #狂人のとき
                if game_info.day == 1:
                    # 1日目は自分以外の生存者からランダムにエージェントを選んで、人間と占う
                    alive_list_wo_me = [a for a in game_info.alive_agent_list if a != game_info.me]
                    divine_target = random.choice(alive_list_wo_me)
                    divine_result = Species.HUMAN
                else:
                    # 自分以外の最も人狼の確率が低い人を指名して、黒出しする
                    inf_results:List[RoleInferenceResult] = []
                    for a in game_info.alive_agent_list:
                        if a != game_info.me:
                            inf_results.append(self.role_inference_module.infer(a, [game_info], game_setting))           
                    min_wolf_inference = min(inf_results, key=lambda x: x.probs[Role.WEREWOLF] if x.agent != game_info.me else 1.0)
                    divine_result = Species.WEREWOLF
                    #人狼側で占った理由を偽造しておく
                    self.history.append(OneStepPlan(min_wolf_inference.reason, ActionType.DIVINE, divine_result))
            
            if game_info.day == 1:
                return f"占い師COします。{divine_target}は{self.species_to_japanese(divine_result)}でした。"
            else:
                return f"占い結果です。{divine_target}は{self.species_to_japanese(divine_result)}でした。"
        else:
            return "村人です。頑張りましょう！"
        
    def talk_roleaction_reaction(self, game_info:GameInfo, game_setting:GameSetting)->Optional[str]:
        """COや占い結果に反応したり、占い理由を聞いたりする。"""
        if not self.comingout_status.is_all_comingout:
            return "占い師の人がいたらCOしてください"
        self.today_talked_topic[TalkTopic.ROLEACTION_REACTION] = True
        if self.today == 1:
            # 1日目はCOの状況に反応する(状況を整理する)
            # GPT4にやらせる
            messages = [{"role": "system", "content":f"あなたは今人狼ゲームをしています。あなたは{game_info.me}です。対戦ログと指示が送られてきますので、対戦ログの結果と発言するべきことが送られてきますので、適切に返答してください。"}, 
                        {"role": "user", "content":f"今の人狼ゲームのログは以下です。\n===========\n{self.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。誰が占い師カミングアウトしているかなどの状況を整理して会話を発展させてください。誰かに向けて発言するときは、「>>Agent[01] 」などと文頭につけてください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
            response = self.chatgpt_api.complete(messages)
            return response
        else:
            # 2日目は占い理由を聞く
            # GPT4にやらせる
            messages = [{"role": "system", "content":"あなたは今人狼ゲームをしています。あなたは{game_info.me}です。対戦ログと指示が送られてきますので、対戦ログの結果と発言するべきことが送られてきますので、適切に返答してください。"}, 
                        {"role": "user", "content":f"今の人狼ゲームのログは以下です。\n===========\n{self.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。占い師COした人に、なぜその人を占ったか聞くなどしてください。誰かに向けて発言するときは、「>>Agent[01] 」などと文頭につけてください。ただし他の人が既に聞いてた場合は、もう言う必要は無いので、SKIPと発言してください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
            response = self.chatgpt_api.complete(messages)
            return response

    def talk_who_to_vote(self, game_info:GameInfo, game_setting:GameSetting)->Optional[str]:
        """誰に投票するかの話題を振る(他の人に聞かれて答えるのは要求処理モジュールの役割なのでやらない)"""
        self.today_talked_topic[TalkTopic.WHO_TO_VOTE] = True
        vote_plan = self.vote(game_info, game_setting)
        # future_planに投票を入れる
        self.add_vote_future_plan(OneStepPlan(vote_plan.reason, ActionType.VOTE, vote_plan.action))
        # 自己対戦で要求処理モジュールが起動するように、要求型の言い方にした
        mention = ""
        for agent in game_info.alive_agent_list:
            if agent != game_info.me:
                mention += f">>{agent} "
            
        # GPT4にやらせる
        explain_text = f"""以下の理由から{vote_plan.action}に投票すべきだと考えられる。そこで、前述の理由を踏まえて他のエージェントが{vote_plan.action}に投票するように説得する文を簡潔に述べよ。また、理由に自信がなくても可能な限り説得しなさい
-----
理由:{vote_plan.reason}
-----   
"""
        #print(f"explain_text:{explain_text}")
        
        explain_message = [{"role":"user","content":explain_text}]
        convince_text = self.chatgpt_api.complete(explain_message).strip("\n'「」").strip('"')
        return convince_text
        #return f"{vote_plan.target}が人狼だと思うので投票したいと思います、皆さん{vote_plan.target}に投票しましょう！"
    
    def talk_no_topic(self, game_info:GameInfo, game_setting:GameSetting)->Optional[str]:
        """話題がないときに話す"""
        # GPT4にやらせる
        # messages = [{"role": "system", "content":f"あなたは今人狼ゲームをしています。あなたは{game_info.me}です。対戦ログと指示が送られてきますので、対戦ログの結果と発言するべきことが送られてきますので、適切に返答してください。"}, 
        #                 {"role": "user", "content":f"今の人狼ゲームのログは以下です。\n===========\n{self.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。まだ何か人狼ゲーム上重要なことで言うべきことがあれば言ってください(弁明、他者への質問など)。言うことが無ければ「Over」と返してください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
        # response = self.gpt4_api.complete(messages)
        # return response
        
        #トークン数の関係で、常にOverを返すようにする
        return "Over"
    
    def add_vote_future_plan(self, one_step_plan:OneStepPlan)->None:
        for plan in self.future_plan:
            if plan.action_type == ActionType.VOTE:
                self.future_plan.remove(plan)
        self.future_plan.append(one_step_plan)


if __name__=="__main__":
    from aiwolf.agent import Status
    from aiwolfk2b.AttentionReasoningAgent.SimpleModules import RandomRoleEstimationModel, SimpleRoleInferenceModule
    
    config_ini = load_default_config()
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    
    role_estimation_model = RandomRoleEstimationModel(config_ini)
    role_inference_module = SimpleRoleInferenceModule(config_ini, role_estimation_model)
    
    strategy_module = StrategyModule(config_ini, role_estimation_model, role_inference_module)
    strategy_module.initialize(game_info, game_setting)
    game_info.status_map= {Agent(1):Status.ALIVE, Agent(2):Status.ALIVE, Agent(3):Status.ALIVE, Agent(4):Status.ALIVE, Agent(5):Status.ALIVE}
    game_info.talk_list = [Talk(day=1,agent=game_info.agent_list[0], idx=1, text="占い師COします。占い結果はAgent[02]が白でした。", turn=1),Talk(day=1,agent=game_info.agent_list[1], idx=2, text="1占いCO把握", turn=1),Talk(day=1,agent=game_info.agent_list[2], idx=3, text="占い師COします。Agent[01]を占って黒でした。", turn=1) , Talk(day=1,agent=game_info.agent_list[3], idx=4, text="村人です", turn=1), Talk(day=1,agent=game_info.agent_list[4], idx=5, text="村人です。", turn=1)]
    game_info.day = 1
    print(strategy_module.talk(game_info, game_setting))
    print(strategy_module.talk(game_info, game_setting))
    print(strategy_module.comingout_status.all_comingout_status)
