import random
import collections
import aiwolfpy_old.contentbuilder as cb
import util
import HeVillager_15 as VillagerBehavior

class WerewolfBehavior(VillagerBehavior.VillagerBehavior):
    def __init__(self, agent_name, agent_list):
        super().__init__(agent_name, agent_list)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.result_Wmed = []
        self.whisper_turn = 0
        self.pp_mode = 1
        self.stealth = 0
        self.first_identify = 0
        self.shonichi_target = 0
        self.kurodashi = set()
        self.shirodashi = set()
        self.most_voted = 0
        self.SPcounter = 0
        self.wolfs = set(map(lambda i: int(i), self.base_info["roleMap"].keys()))
        judger = random.random()
        if judger <= 0.1:
            self.role_decision = 0
        elif judger > 0.1 and judger <= 0.5:
            self.role_decision = 1
        else:
            self.role_decision = 2

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)
        for CO_seer in self.divineders:
            if CO_seer not in self.agent_list[4]:
                if self.wolfs & self.result_all_divineders[CO_seer]["white"]:
                    self.likely_fake_divineders.add(CO_seer)
                if self.result_all_divineders[CO_seer]["black"] - self.wolfs:
                    self.likely_fake_divineders.add(CO_seer)

    def dayStart(self):
        super().dayStart()
        self.whisper_turn = 0
        return None

    def talk(self):
        self.talk_turn += 1
        self.attack_judge = 0
        if self.role_decision == 0:
            if self.base_info["day"] == 1:
                if self.stealth == 0:
                    if self.talk_turn == 1:
                        random_seer_medium_parameter = random.randint(0, 9)
                        if random_seer_medium_parameter % 2 == 0:
                            CO_SEER = cb.comingout(self.base_info['agentIdx'], "SEER")
                        else:
                            CO_SEER = cb.comingout(self.base_info['agentIdx'], "MEDIUM")
                        return CO_SEER
                    elif self.talk_turn == 2:
                        if self.COs - {int(self.base_info["agentIdx"])}:
                            self.shonichi_target = random.choice(list(self.COs - {int(self.base_info["agentIdx"])}))
                            self.kurodashi.add(self.shonichi_target)
                            return cb.divined(self.shonichi_target, "WEREWOLF")
                        else:
                            self.shonichi_target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders))
                            self.kurodashi.add(self.shonichi_target)
                            return cb.divined(self.shonichi_target, "WEREWOLF")
                    elif self.talk_turn >= 3:
                        return cb.vote(self.shonichi_target)
                else:
                    return super().talk()
            else:
                if self.stealth == 0:
                    judger = random.random()
                    if judger <= 0.7 and self.SPcounter <= 2:
                        if self.talk_turn == 1:
                            if self.alive - self.COs - set(self.COm) - self.divineders - self.kurodashi - self.shirodashi:
                                target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders - self.kurodashi - self.shirodashi))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            elif self.alive - self.kurodashi - self.shirodashi:
                                target = random.choice(list(self.alive - self.kurodashi - self.shirodashi))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            elif self.alive & self.shirodashi:
                                target = random.choice(list(self.alive & self.shirodashi))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            else:
                                target = random.choice(list(self.alive & self.kurodashi))
                                self.kurodashi.add(target)
                                return cb.divined(target, "WEREWOLF")
                        else:
                            target = self.vote()
                            return cb.vote(target)
                    else:
                        self.SPcounter += 1
                        if self.talk_turn == 1:
                            if self.alive & self.wolfs - {int(self.base_info["agentIdx"])}:
                                target = random.choice(list(self.alive & self.wolfs - {int(self.base_info["agentIdx"])}))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            else:
                                target = self.vote()
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                        else:
                            target = self.vote()
                            return cb.vote(target)
                else:
                    return super().talk()
            return super().talk()
        if self.role_decision == 1:
            return super().talk()
        if self.role_decision == 2:
            if self.base_info["day"] == 1:
                if self.talk_turn == 1:
                    if self.stealth == 0:
                        CO_MEDIUM = cb.comingout(self.base_info['agentIdx'], "MEDIUM")
                        return CO_MEDIUM
                    else:
                        return super().talk()
                else:
                    return super().talk()
            else:
                if self.stealth == 0:
                    if self.talk_turn == 1:
                        if self.exed_players[-1] in set(self.COm):
                            if self.first_identify == 0:
                                if len(self.COm) >= 2:
                                    IDENTIFIED_BLACK = cb.identified(self.exed_players[-1], "WEREWOLF")
                                    self.first_identify = 1
                                    return IDENTIFIED_BLACK
                                else:
                                    return super().talk()
                            if self.first_identify == 1:
                                if len(self.COm) >= 2:
                                    IDENTIFIED_WHITE = cb.identified(self.exed_players[-1], "HUMAN")
                                    self.first_identify = 1
                                    return IDENTIFIED_WHITE
                                else:
                                    return super().talk()
                        else:
                            black_cand = set()
                            for i in self.divineders:
                                black_cand |= self.result_all_divineders[i]['black']
                            black_cand -= self.wolfs
                            if self.exed_players[-1] in black_cand:
                                IDENTIFIED_BLACK = cb.identified(self.exed_players[-1], "WEREWOLF")
                                return IDENTIFIED_BLACK
                            else:
                                if self.exed_players[-1] in set(self.wolfs):
                                    IDENTIFIED_BLACK = cb.identified(self.exed_players[-1], "WEREWOLF")
                                    return IDENTIFIED_BLACK
                                else:
                                    IDENTIFIED_WHITE = cb.identified(self.exed_players[-1], "HUMAN")
                                    return IDENTIFIED_WHITE
                    if self.talk_turn >= 2:
                        return super().talk()
                else:
                    return super().talk()

    def vote(self):
        if self.base_info["day"] == 1:
            if self.stealth == 0:
                if self.role_decision == 0:
                    return self.shonichi_target
                else:
                    cands = self.decide_vote_cand()
                    most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                    return most_voted
            else:
                cands = self.decide_vote_cand()
                most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                return most_voted
        else:
            if len(self.alive) <= 7:
                if len(self.COp) != 0:
                    possessed_vote = set()
                    for i in self.COp:
                        possessed_vote.add(self.talk_vote_list[int(i)-1])
                    possessed_vote = possessed_vote - self.wolfs
                    possessed_vote = possessed_vote - {0}
                    if len(possessed_vote) != 0:
                        cands = max_frequent(list(possessed_vote))
                        target = random.choice(list(cands))
                        return target
                    else:
                        cands = self.alive - self.wolfs
                        target = random.choice(list(cands))
                        return target
                else:
                    if self.decide_vote_cand() - self.shirodashi:
                        cands = self.decide_vote_cand() - self.shirodashi
                        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                        return most_voted
                    else:
                        cands = self.decide_vote_cand()
                        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                        return most_voted
            else:
                if self.decide_vote_cand() - self.shirodashi:
                    cands = self.decide_vote_cand() - self.shirodashi
                    most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                    return most_voted
                else:
                    cands = self.decide_vote_cand()
                    most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                    return most_voted

    def whisper(self):
        self.whisper_turn += 1
        if self.role_decision == 0:
            if self.base_info["day"] == 0:
                if self.whisper_turn == 1:
                    return cb.comingout(self.base_info['agentIdx'], 'SEER')
                if self.whisper_turn == 2:
                    if len(self.W_COs) >= 2 or len(self.W_COm) >= 1:
                        self.stealth = 1
                        return cb.comingout(self.base_info['agentIdx'], 'VILLAGER')
                    else:
                        return cb.skip()
                if self.whisper_turn >= 3:
                    return cb.skip()
                return cb.skip()
        if self.role_decision == 1:
            if self.base_info["day"] == 0:
                if self.whisper_turn == 1:
                    return cb.comingout(self.base_info['agentIdx'], 'VILLAGER')
                if self.whisper_turn >= 2:
                    return cb.skip()
                return cb.skip()
        if self.role_decision == 2:
            if self.base_info["day"] == 0:
                if self.whisper_turn == 1:
                    return cb.comingout(self.base_info['agentIdx'], 'MEDIUM')
                if self.whisper_turn == 2:
                    if len(self.W_COm) >= 2 or len(self.W_COs) >= 1:
                        self.stealth = 1
                        return cb.comingout(self.base_info['agentIdx'], 'VILLAGER')
                if self.whisper_turn >= 3:
                    return cb.skip()
                return cb.skip()
        if self.base_info["day"] >= 1:
            if self.whisper_turn == 1:
                return cb.attack(self.attack())
            else:
                return cb.skip()
        return cb.skip()

    def attack(self):
        if self.role_decision == 0:
            if self.base_info["day"] == 1:
                cand_1 = self.COm
                if (len(cand_1) != 0):
                    return random.choice(list(cand_1))
                else:
                    cand_2 = self.greys
                    return random.choice(list(cand_2))
            if self.base_info["day"] >= 2:
                cand_3 = self.greys
                if (len(cand_3) != 0):
                    return random.choice(list(cand_3))
                else:
                    return random.choice(list(self.alive - self.wolfs))
            return random.choice(list(self.alive - self.wolfs))
        if self.role_decision == 1:
            if self.base_info["day"] == 1:
                likely_true_divineders = self.alive & self.divineders - self.fake_divineders\
                                         - self.wolfs - self.likely_fake_divineders
                if len(likely_true_divineders) == 1:
                    return list(likely_true_divineders)[0]
                elif len(self.divineders & self.alive - self.wolfs) != 0:
                    cand_1 = self.divineders & self.alive - self.wolfs
                    return random.choice(list(cand_1))
                else:
                    cand_2 = self.alive - self.wolfs
                    return random.choice(list(cand_2))
            if self.base_info["day"] >= 2:
                AJ_set = set()
                AJ_set.add(self.attack_judge)
                if 0 in AJ_set:
                    if set(self.COm) - self.wolfs:
                        cand_3 = set(self.COm) - self.wolfs
                        return random.choice(list(cand_3))
                    elif self.greys - self.wolfs:
                        cand_4 = self.greys - self.wolfs
                        return random.choice(list(cand_4))
                    else:
                        cand_5 = self.alive - self.wolfs
                        return random.choice(list(cand_5))
                else:
                    cand_6 = self.greys - self.wolfs
                    return random.choice(list(cand_6))
            return random.choice(list(self.alive - self.wolfs))
        if self.role_decision == 2:
            likely_true_seers = (self.divineders & self.alive) - self.fake_divineders - self.likely_fake_divineders
            if (likely_true_seers):
                return random.choice(list(likely_true_seers))
            if (len(self.divineders) >= 2) and (self.divineders & self.alive) == self.divineders:
                return random.choice(list(self.divineders))
            nonW_COg = self.COg & self.alive - self.wolfs
            if (len(list(nonW_COg)) >= 1):
                return random.choice(list(nonW_COg))
            white_cand = set()
            may_seer = self.divineders - self.fake_divineders - self.likely_fake_divineders
            for i in may_seer:
                white_cand = white_cand | self.result_all_divineders[i]['white']
            white_cand = white_cand - set(self.COm)
            white_cand = white_cand - self.COs
            if (white_cand & self.alive):
                return random.choice(list(white_cand))
            cand_5 = self.alive - self.COs - set(self.COm) - self.wolfs
            if (len(cand_5) != 0):
                return random.choice(list(cand_5))
            cand_6 = self.alive - self.COs - self.wolfs
            if (len(cand_6) != 0):
                return random.choice(list(cand_6))
            cand_7 = self.alive - self.wolfs
            if (len(cand_7) != 0):
                return random.choice(list(cand_7))
            return random.choice(list(self.alive - self.wolfs))

    def finish(self):
        return None

    def pp_judger(self):
        if len(self.divineders & self.alive - self.wolfs) >= 2 or \
                len(set(self.likely_fake_divineders.keys()) & set(self.alive)) - len(set(self.wolfs)) >= 1:
            if (len(self.alive) == len(set(self.wolfs) & set(self.alive)) * 2 + 1):
                self.pp_mode = 1

    def decide_vote_cand(self):
        if len(self.COm) >= 2:
            if set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}:
                return set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}
        true_black = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]['black']
        if self.divineders and true_black - self.wolfs:
            return true_black - self.wolfs
        may_black = set()
        for key in self.divineders - self.fake_divineders:
            may_black |= self.result_all_divineders[key]['black']
        if self.alive & may_black - self.wolfs:
            return self.alive & may_black - self.wolfs

        if self.greys - self.COg - set(self.COm) - self.COs - self.wolfs:
            return self.greys - self.COg - set(self.COm) - self.COs - self.wolfs
        return self.alive - {int(self.base_info['agentIdx'])} - self.wolfs

def max_frequent(l):
    if all(x == 0 for x in l) == True:
        return set()
    else:
        if 0 in l:
            l = [s for s in l if s != 0]
        max_cand = set()
        sorted_res = collections.Counter(l).most_common()
        max_vallot = sorted_res[0][1]
        max_cand.add(sorted_res[0][0])
        for i in range(1, len(sorted_res)):
            if (sorted_res[i][1] == max_vallot):
                max_cand.add(sorted_res[i][0])
            else:
                break
        return max_cand
