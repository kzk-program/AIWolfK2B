from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractStrategyModule,AbstractRoleInferenceModule,RoleInferenceResult,OneStepPlan, ActionType
import errno
import os

class StrategyModule(AbstractStrategyModule):
    """戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config,role_estimation_model,role_inference_module)
        self.history = []
        self.future_plan = []
        self.next_plan = None

    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        return "実装お願いします"
    
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
        
if __name__=="__main__":
    import pickle
    from aiwolf.agent import Status
    from aiwolfk2b.AttentionReasoningAgent.SimpleModules import RandomRoleEstimationModel, SimpleRoleInferenceModule
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
    print(strategy_module.vote(game_info, game_setting))