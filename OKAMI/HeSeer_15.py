import aiwolfpy_old.contentbuilder as cb
import HeVillager_15 as VillagerBehavior
import random
import util

class SeerBehavior(VillagerBehavior.VillagerBehavior):
    def __init__(self, agent_name, agent_list):
        super().__init__(agent_name, agent_list)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.result_seer = {'black': set(), 'white': set()}
        self.result_seer_new = []
        self.last_seer_result = "HUMAN"
        self.last_seer_target = 0

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)
        if request == "DAILY_INITIALIZE":
            for i in range(diff_data.shape[0]):
                if diff_data["type"][i] == "divine":
                    content = diff_data["text"][i].split()
                    if int(content[1][6:8]) in range(1, 16):
                        if content[2] == 'HUMAN':
                            self.result_seer['white'].add(int(content[1][6:8]))
                            self.result_seer_new = [[int(content[1][6:8]), 0]]
                        else:
                            self.result_seer['black'].add(int(content[1][6:8]))
                            self.result_seer_new = [[int(content[1][6:8]), 1]]

    def dayStart(self):
        super().dayStart()
        if self.result_seer_new:
            self.last_seer_target, self.last_seer_result = self.result_seer_new.pop(0)
        return None

    def talk(self):
        self.talk_turn += 1
        if self.talk_turn == 1:
            if self.last_seer_result == "HUMAN":
                return cb.estimate(self.last_seer_target, self.last_seer_result)
            elif self.last_seer_result == "WEREWOLF":
                return cb.comingout(self.base_info['agentIdx'], "SEER")
        if self.talk_turn == 2:
            if self.last_seer_result == "HUMAN":
                return cb.request(cb.guard(self.last_seer_target))
            elif self.last_seer_result == "WEREWOLF":
                return cb.divined(self.last_seer_target, self.last_seer_result)
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
        true_black = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]['black']
        if true_black:
            return true_black
        if self.result_seer['black'] & self.alive:
            return self.result_seer['black'] & self.alive
        if self.fake_divineders & self.alive:
            return self.fake_divineders & self.alive
        if self.likely_black_set & self.alive:
            return self.likely_black_set & self.alive
        if self.likely_black_set & self.alive:
            return self.likely_black_set & self.alive
        if len(self.divineders) >= 3:
            if self.divineders & self.alive - {int(self.base_info["agentIdx"])}:
                return self.divineders & self.alive - {int(self.base_info["agentIdx"])}
        may_black = set()
        for key in self.divineders - self.fake_divineders - {int(self.base_info["agentIdx"])}:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.result_seer['white'] | self.result_seer['black'] | {int(self.base_info["agentIdx"])}
        my_greys = self.alive - self.result_seer['white'] - self.result_seer['black'] - {int(self.base_info["agentIdx"])}
        if may_black & self.alive:
            if set(self.COm) <= self.alive and len(self.COm) in [1, 2]:
                return may_black & self.alive
            else:
                return my_greys - may_black - self.divineders - set(self.COm[:1])
        if my_greys - self.divineders - set(self.COm[:1]):
            return my_greys - self.divineders - set(self.COm[:1])
        if self.divineders - {int(self.base_info["agentIdx"])}:
            return self.divineders - {int(self.base_info["agentIdx"])}
        return self.alive - {int(self.base_info["agentIdx"])}

    def divine(self):
        cand = self.divine_cand()
        if not cand:
            cand = self.alive - self.result_seer['white'] - self.result_seer['black'] \
                   - {int(self.base_info["agentIdx"])}
        next_divine = random.choice(list(cand))
        return next_divine

    def divine_cand(self):
        if not self.base_info['day']:
            return self.alive - {int(self.base_info['agentIdx'])}
        cand = self.greys - self.divineders - self.COs
        if len(self.COm) == 1:
            cand -= set(self.COm)
        if len(self.COm) >= 2 and len(set(self.COm) & cand) >= 1:
            for i in self.COm[1:]:
                if i in cand:
                    return {i}
            return {self.COm[0]}
        if len(self.COg) >= 2 and len(self.COg & cand) >= 1:
            return self.COg & cand
        may_black = set()
        for key in self.divineders - self.fake_divineders - {int(self.base_info["agentIdx"])}:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.result_seer['white'] | self.result_seer['black'] | {int(self.base_info["agentIdx"])}
        if may_black & self.alive:
            return may_black & self.alive
        vote_me = set()
        for i in range(15):
            if self.vote_list[i] == int(self.base_info["agentIdx"]):
                vote_me.add(i + 1)
        if len(vote_me & cand) >= 1:
            return vote_me & cand
        vote_max = set()
        if self.exed_players:
            for i in range(15):
                if self.vote_list[i] == self.exed_players[-1]:
                    vote_max.add(i + 1)
        if self.base_info['day'] <= 3:
            if len(vote_max & cand):
                return vote_max & cand
        else:
            if len(cand - vote_max):
                return cand - vote_max
        if cand:
            return cand
        if (self.divineders | self.COs) & self.alive - {int(self.base_info["agentIdx"])}:
            return (self.divineders | self.COs) & self.alive - {int(self.base_info["agentIdx"])}
        if set(self.COm) & self.alive:
            return set(self.COm) & self.alive
        return self.alive - {int(self.base_info['agentIdx'])}

    def finish(self):
        return None
