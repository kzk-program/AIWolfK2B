from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union, Optional
from enum import Enum

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role, Species

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractStrategyModule,AbstractRoleInferenceModule,RoleInferenceResult,OneStepPlan, ActionType
import errno
import os
import random
import openai
import Levenshtein
import pathlib

class GameLog:
    """ゲームのログを保存するクラス"""
    def __init__(self, game_info:GameInfo, game_setting:GameSetting) -> None:
        self.log = ""
    
    def update(self, game_info:GameInfo, game_setting:GameSetting)->None:
        for talk in game_info.talk_list:
            self.log += f"{talk.day}日目 {talk.agent}の発言 :{talk.text}\n"

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
        print("sending to GPT3")
        response = openai.Completion.create(engine="text-davinci-003",
            prompt=input,
            max_tokens=100,
            temperature=0)
        print("received from GPT3")
        return response['choices'][0]['text']

    
class GPT4API:
    """
    GPT4とのやりとりを行うためのクラス
    """
    def __init__(self):
        parent_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
        with open(parent_dir + '/openAIAPIkey.txt', "r") as f:
            openai.api_key = f.read().strip()

    def complete(self, messages)->str:
        """GPT4でCompletionを行う"""
        print("sending to GPT4")
        response = openai.ChatCompletion.create(model="gpt-4-0613",
            messages=messages, 
            max_tokens=200,
            temperature=0.5)
        print("received from GPT4")
        parent_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
        with open(parent_dir+"/log.txt", "a") as f:
            f.write(f"{messages}\n{response['choices'][0]['message']['content']}")
        return response['choices'][0]['message']['content']
    

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
            self.gpt3_api  =GPT3API()

    def update(self, game_info:GameInfo, game_setting:GameSetting)->None:
        if not self.is_all_comingout():
            for talk in game_info.talk_list:
                prompt = f"""以下の発言に対し、カミングアウト(役職の公開)かどうかとその役職を判定してください。カミングアウトが無ければ無しとこたえてください。役職は、人狼・狂人・占い師・村人の4種類で答えてください。
「占いCOします。Agent[01]は白でした。」 :占い師
「ガオー、人狼だぞー」:人狼
「俺は村人です。仲良くやりましょう！」:村人
「みなさんよろしくお願いします」:無し
「{talk.text}」 :"""
                response = self.gpt3_api.complete(prompt)
                CO_role = self._closest_str(["無し","人狼","狂人","占い師","村人"], response)
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
    
    def _closest_str(self, str_list:List[str], target_str:str)->str:
        """str_listの中からtarget_strに最も近い文字列を返す"""
        min_distance = 100000
        min_str = ""
        for str in str_list:
            distance = Levenshtein.distance(str, target_str)
            if distance < min_distance:
                min_distance = distance
                min_str = str
        return min_str


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
        self.gpt4_api = GPT4API()

    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        if game_info.day == 0:
            return "よろしくお願いします！"
        
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
                        return role_action_result
                elif topic == TalkTopic.ROLEACTION_REACTION:
                    roleaction_reaction =  self.talk_roleaction_reaction(game_info, game_setting)
                    if roleaction_reaction != None:
                        self.today_talked_topic[topic] = True
                        print("roleaction_reaction", roleaction_reaction)
                        return roleaction_reaction
                elif topic == TalkTopic.WHO_TO_VOTE:
                    who_to_vote = self.talk_who_to_vote(game_info, game_setting)
                    if who_to_vote != None:
                        self.today_talked_topic[topic] = True
                        print("who_to_vote", who_to_vote)
                        return who_to_vote
                
        # 会話デッキを使い果たしたら
        no_topic = self.talk_no_topic(game_info, game_setting)
        print("no topic", no_topic)
        return no_topic

    
    def vote(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """投票"""
        #各エージェントの役職を推定する
        inf_results:List[RoleInferenceResult] = []
        for a in game_info.alive_agent_list:
            inf_results.append(self.role_inference_module.infer(a, game_info, game_setting))

        #エージェントの中から最も占い師の確率が高いエージェントを選ぶ
        #エージェントの中から最も狂人の確率が低いエージェントを選ぶ
        #エージェントの中から最も人狼の確率が高いエージェントを選ぶ
        max_seer_agent = self.max_agent(inf_results, Role.SEER)
        min_poss_agent = self.min_agent(inf_results, Role.POSSESSED)
        max_wolf_agent = self.max_agent(inf_results, Role.WEREWOLF)

        #人狼側の場合、誰に投票するか決める
        if game_info.my_role == Role.WEREWOLF or game_info.my_role == Role.POSSESSED:
            #占い師が生きている確率が高い場合
            if self.check_survive_seer(inf_results):
                #最も占い師の確率が高いエージェントに投票する
                return max_seer_agent
            else:
                #最も狂人の確率が低いエージェントに投票する
                return min_poss_agent
        #村人側の場合、誰に投票するか決める
        else:
            #最も人狼の確率が高いエージェントに投票する
            return max_wolf_agent
    
    def attack(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """襲撃"""
        #各エージェントの役職を推定する
        inf_results:List[RoleInferenceResult] = []
        for a in game_info.alive_agent_list:
            inf_results.append(self.role_inference_module.infer(a, game_info, game_setting))

        #エージェントの中から最も占い師の確率が高いエージェントを選ぶ
        #エージェントの中から最も狂人の確率が低いエージェントを選ぶ
        max_seer_agent = self.max_agent(inf_results, Role.SEER)
        min_poss_agent = self.min_agent(inf_results, Role.POSSESSED)

        #占い師が生きている確率が高い場合
        if self.check_survive_seer(inf_results):
            #最も占い師の確率が高いエージェントに襲撃する
            return max_seer_agent
        else:
            #最も狂人の確率が低いエージェントに襲撃する
            return min_poss_agent
    
    def divine(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """占い"""
        #各エージェントの役職を推定する
        inf_results:List[RoleInferenceResult] = []
        for a in game_info.alive_agent_list:
            inf_results.append(self.role_inference_module.infer(a, game_info, game_setting))

        #人狼側である確率が最も低いエージェントを選ぶ
        min_wolf_agent = self.min_agent(inf_results, Role.WEREWOLF)

        #最も人狼の確率が低いエージェントに投票する
        return min_wolf_agent
    
    def guard(self, game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """護衛"""
        """５人人狼では不要"""
        raise NotImplementedError
    
    def whisper(self, game_info: GameInfo, game_setting: GameSetting) -> str:
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
    
    #以下、新規に追加した関数
    def max_agent(self, inf_list: List[RoleInferenceResult], role: Role) -> Agent:
        """推定結果から最も役職の確率の高いエージェントを選ぶ"""
        w = self.weight(role)

        max_prob = -1
        max_agent = None
        for inf in inf_list:
            p = [inf.probs[Role.VILLAGER],inf.probs[Role.SEER],inf.probs[Role.POSSESSED],inf.probs[Role.WEREWOLF]]
            f = 0
            for x, y in zip(p, w):
                f += x * y
            if f > max_prob:
                max_prob = f
                max_agent = inf.agent
        return max_agent

    def min_agent(self, inf_list: List[RoleInferenceResult], role: Role) -> Agent:
        """推定結果から最も役職の確率の高いエージェントを選ぶ"""
        w = self.weight(role)

        min_prob = 2
        min_agent = None
        for inf in inf_list:
            p = [inf.probs[Role.VILLAGER],inf.probs[Role.SEER],inf.probs[Role.POSSESSED],inf.probs[Role.WEREWOLF]]
            f = 0
            for x, y in zip(p, w):
                f += x * y
            if f < min_prob:
                min_prob = f
                min_agent = inf.agent
        return min_agent
    
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
        
    def check_survive_seer(self, inf_list: List[RoleInferenceResult]) -> bool:
        """占い師が生きているかどうか判定する"""
        #占い師である確率の合計値
        sum_seer = 0
        for inf in inf_list:
            sum_seer += inf.probs[Role.SEER]
        #占い師がいる可能性が高いかどうかの閾値
        th_seer = 0.7
        if sum_seer > th_seer:
            return True
        else:
            return False
    
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
                    divine_target = random.choice(game_info.alive_agent_list)
                    divine_result = Species.HUMAN
                else:
                    # 最も人狼の確率が低い人を指名して、黒出しする
                    inf_results:List[RoleInferenceResult] = []
                    for a in game_info.alive_agent_list:
                        if a != game_info.me:
                            inf_results.append(self.role_inference_module.infer(a, game_info, game_setting))
                    
                    divine_target = self.min_agent(inf_results, Role.WEREWOLF)
                    divine_result = Species.WEREWOLF
                    self.history.append(OneStepPlan("一番怪しいと思ったから", ActionType.DIVINE, divine_target))
            
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
                        {"role": "user", "content":f"今の人狼ゲームのログは以下です。\n===========\n{self.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。誰が占い師カミングアウトしているかなどの状況を整理して会話を発展させてください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
            response = self.gpt4_api.complete(messages)
            return response
        else:
            # 2日目は占い理由を聞く
            # GPT4にやらせる
            messages = [{"role": "system", "content":"あなたは今人狼ゲームをしています。あなたは{game_info.me}です。対戦ログと指示が送られてきますので、対戦ログの結果と発言するべきことが送られてきますので、適切に返答してください。"}, 
                        {"role": "user", "content":f"今の人狼ゲームのログは以下です。\n===========\n{self.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。占い師COした人に、なぜその人を占ったか聞くなどしてください。ただし他の人が既に聞いてた場合は、もう言う必要は無いので、SKIPと発言してください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
            response = self.gpt4_api.complete(messages)
            return response

    def talk_who_to_vote(self, game_info:GameInfo, game_setting:GameSetting)->Optional[str]:
        """誰に投票するかの話題を振る(他の人に聞かれて答えるのは要求処理モジュールの役割なのでやらない)"""
        self.today_talked_topic[TalkTopic.WHO_TO_VOTE] = True
        vote_target = self.vote(game_info, game_setting)
        return f"{vote_target}が人狼だと思うので投票したいと思うのですが、皆さんはどう思いますか？"
    
    def talk_no_topic(self, game_info:GameInfo, game_setting:GameSetting)->Optional[str]:
        """話題がないときに話す"""
        messages = [{"role": "system", "content":f"あなたは今人狼ゲームをしています。あなたは{game_info.me}です。対戦ログと指示が送られてきますので、対戦ログの結果と発言するべきことが送られてきますので、適切に返答してください。"}, 
                        {"role": "user", "content":f"今の人狼ゲームのログは以下です。\n===========\n{self.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。まだ何か人狼ゲーム上重要なことで言うべきことがあれば言ってください(弁明、他者への質問など)。言うことが無ければ「Over」と返してください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
        response = self.gpt4_api.complete(messages)
        return response
        


if __name__=="__main__":
    import pickle
    from aiwolf.agent import Status
    from aiwolfk2b.AttentionReasoningAgent.SimpleModules import RandomRoleEstimationModel, SimpleRoleInferenceModule
    from aiwolf import Talk
    config_ini = ConfigParser()
    config_ini_path = os.pardir + '/config.ini'

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
    with open(os.pardir +"/game_info.pkl", mode="rb") as f:
        game_info:GameInfo = pickle.load(f)
    with open(os.pardir + "/game_setting.pkl", mode="rb") as f:
        game_setting:GameSetting = pickle.load(f)
    
    strategy_module = StrategyModule(config_ini, role_estimation_model, role_inference_module)
    strategy_module.initialize(game_info, game_setting)
    game_info.status_map= {Agent(1):Status.ALIVE, Agent(2):Status.ALIVE, Agent(3):Status.ALIVE, Agent(4):Status.ALIVE, Agent(5):Status.ALIVE}
    game_info.talk_list = [Talk(day=1,agent=game_info.agent_list[0], idx=1, text="占い師COします。占い結果はAgent[02]が白でした。", turn=1),Talk(day=1,agent=game_info.agent_list[1], idx=2, text="1占いCO把握", turn=1),Talk(day=1,agent=game_info.agent_list[2], idx=3, text="占い師COします。Agent[01]を占って黒でした。", turn=1) , Talk(day=1,agent=game_info.agent_list[3], idx=4, text="村人です", turn=1), Talk(day=1,agent=game_info.agent_list[4], idx=5, text="村人です。", turn=1)]
    game_info.day = 1
    print(strategy_module.talk(game_info, game_setting))
    print(strategy_module.talk(game_info, game_setting))
    print(strategy_module.comingout_status.all_comingout_status)
