import aiwolfpy_old.contentbuilder as cb
import HeVillager_15 as VillagerBehavior
import util
import random

class MediumBehavior(VillagerBehavior.VillagerBehavior):
    def __init__(self, agent_name, agent_list):
        super().__init__(agent_name, agent_list)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.result_medium = {'black': set(), 'white': set()}
        self.result_medium_new = []
        self.result_medium_temp = self.result_medium.copy()
        self.announced_as_medium = False

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)
        if request == "DAILY_INITIALIZE":
            for i in range(diff_data.shape[0]):
                if diff_data["type"][i] == "identify":
                    content = diff_data["text"][i].split()
                    if content[2] == 'HUMAN':
                        self.result_medium['white'].add(int(content[1][6:8]))
                        self.result_medium_new = [[int(content[1][6:8]), 0]]
                    else:
                        self.result_medium['black'].add(int(content[1][6:8]))
                        self.result_medium_new = [[int(content[1][6:8]), 1]]
        for CO_seer in list(self.divineders):
            if CO_seer not in self.agent_list[4]:
                if int(self.base_info['agentIdx']) in self.result_all_divineders[CO_seer]["black"]:
                    self.likely_fake_divineders.add(CO_seer)
                if self.result_medium["black"] & self.result_all_divineders[CO_seer]["white"]:
                    self.likely_fake_divineders.add(CO_seer)
                if self.result_all_divineders[CO_seer]["white"] & self.result_medium["black"]:
                    self.likely_fake_divineders.add(CO_seer)
        if len(self.COm)>1:
            self.likely_fake_mediums_set |= set(self.COm) - {int(self.base_info['agentIdx'])}

    def dayStart(self):
        super().dayStart()
        return None

    def talk(self):
        if self.result_medium_new:
            who, result = self.result_medium_new.pop(0)
            result = "WEREWOLF" if result else "HUMAN"
            return cb.estimate(who, result)
        elif self.alive <= 10:
            if not self.announced_as_medium and self.base_info["day"] == 3:
                self.announced_as_medium = True
                return cb.comingout(self.base_info['agentIdx'], "MEDIUM")
            if len(self.result_medium_temp["black"]):
                who, result = self.result_medium["black"].pop()
                return cb.identified(who, result)
            if len(self.result_medium_temp["white"]):
                who, result = self.result_medium["white"].pop()
                return cb.identified(who, result)
        return super().talk()

    def vote(self):
        cands = self.vote_cand()
        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 0)
        judge_num = random.random()
        if judge_num >= 0.01:
            return most_voted
        else:
            return super().vote()

    def vote_cand(self):
        if len(self.alive) <= 7 and self.under_7_vote:
            if self.exed_players and self.exed_players[-1] in self.result_medium['white']:
                if self.under_7_vote.pop(0, None):
                    self.under_7_vote = {i: 0 for i in self.alive}
                for i in set(j+1 for j in range(15) if self.yesterday_vote_list[j] == self.exed_players[-1]) & self.alive:
                    if i in self.under_7_vote:
                        self.under_7_vote[i] += 1
                self.yesterday_vote_list = self.vote_list[:]
                for i in set(self.under_7_vote.keys()) - self.alive:
                    self.under_7_vote.pop(i,None)
                if len(self.under_7_vote):
                    under_7_max_vote = {i[0] for i in self.under_7_vote.items()\
                                        if i[1] == max(self.under_7_vote.values())}
                    return under_7_max_vote
        if len(self.COm) >= 2:
            if set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}:
                return set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}
        true_black = self.alive.copy()
        true_white = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]["black"]
            true_white &= self.result_all_divineders[key]["white"]
        if self.divineders and true_black:
            return true_black
        if len(self.divineders) >= 3:
            if self.divineders & self.alive:
                if len(self.divineders - self.result_all_mediums[int(self.base_info["agentIdx"])]["black"]) >= 3:
                    return self.divineders & self.alive
        if self.likely_black_set & self.alive:
            return self.likely_black_set & self.alive
        if self.likely_black_set & self.alive:
            return self.likely_black_set & self.alive
        may_black = set()
        for key in self.divineders - self.fake_divineders - self.likely_fake_divineders:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.divineders
        if may_black & self.alive - {int(self.base_info["agentIdx"])}:
            return may_black & self.alive - {int(self.base_info["agentIdx"])}
        not_fake_divineders_greys = self.alive.copy()
        for key in self.divineders - self.fake_divineders - self.likely_fake_divineders:
            not_fake_divineders_greys -= self.result_all_divineders[key]["black"]
            not_fake_divineders_greys -= self.result_all_divineders[key]["white"]
        my_greys = not_fake_divineders_greys - self.divineders - self.COs - set(self.COm)\
                    - true_white - {int(self.base_info["agentIdx"])}
        if my_greys:
            return my_greys
        if self.fake_divineders & self.alive:
            return self.fake_divineders & self.alive
        return self.alive - {int(self.base_info["agentIdx"])}

    def finish(self):
        return None
