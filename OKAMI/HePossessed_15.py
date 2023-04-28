import random
import collections
import aiwolfpy_old.contentbuilder as cb
import util
import HeVillager_15 as VillagerBehavior
class PossessedBehavior(VillagerBehavior.VillagerBehavior):

    def __init__(self, agent_name, agent_list):
        super().__init__(agent_name, agent_list)

    def initialize(self, base_info, diff_data, game_setting):
        self.kurodashi = set()
        self.ts_kurodashi = []
        self.shirodashi = set()
        self.result_seer = {"white":set(), "black":set()}
        self.SP = 0
        self.SP_target = 0
        super().initialize(base_info, diff_data, game_setting)

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

    def dayStart(self):
        super().dayStart()
        self.talk_turn = 0
        return None

    def talk(self):
        self.talk_turn += 1
        if self.base_info["day"] == 1:
            if self.talk_turn == 1:
                CO_SEER = cb.comingout(self.base_info['agentIdx'], "VILLAGER")
                return CO_SEER
            if self.talk_turn == 2:
                return cb.request(cb.guard(self.myname))
            if self.talk_turn == 3:
                if len(self.COs) == 3:
                    vote_cand = self.COs - {int(self.base_info["agentIdx"])} - self.likely_fake_divineders
                    target = random.choice(list(vote_cand))
                    self.ts_kurodashi.append(target)
                    self.kurodashi.add(target)
                    fake_divine_res = cb.divined(target, "WEREWOLF")
                    return fake_divine_res
                else:
                    vote_cand = self.alive - self.COs - set(self.COm) - self.divineders - self.likely_black_set
                    target = random.choice(list(vote_cand))
                    self.ts_kurodashi.append(target)
                    self.kurodashi.add(target)
                    fake_divine_res = cb.divined(target, "WEREWOLF")
                    return fake_divine_res
            else:
                return super().talk()
        if self.base_info["day"] >= 2:
            if len(self.alive) > 7:
                if self.talk_turn == 1:
                    if self.ts_kurodashi[-1] not in self.alive:
                        result_all_white = set()
                        non_me_divineders = self.divineders - {int(self.base_info["agentIdx"])}
                        for i in non_me_divineders:
                            result_all_white |= self.result_all_divineders[i]['white']
                        result_all_white &= self.alive
                        result_all_white -= set(self.COm)
                        result_all_white -= {int(self.base_info["agentIdx"])}
                        if result_all_white:
                            target = random.choice(list(result_all_white))
                            self.ts_kurodashi.append(target)
                            self.kurodashi.add(target)
                            self.result_seer["black"] = self.kurodashi
                            fake_divine_res = cb.divined(target, "WEREWOLF")
                            return fake_divine_res
                        else:
                            stupid = YMBV(self.vote_list, self.ts_kurodashi[-1])
                            if self.ated_players:
                                if stupid - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}:
                                    target = random.choice(list(stupid - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}))
                                elif self.alive - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}:
                                    target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}))
                                else:
                                    target = random.choice(list(self.alive - {int(self.base_info["agentIdx"])}))
                                self.kurodashi.add(target)
                                self.ts_kurodashi.append(target)
                                fake_divine_res = cb.divined(target, "WEREWOLF")
                                return fake_divine_res
                            else:
                                if stupid - self.COs - set(self.COm) - self.divineders:
                                    target = random.choice(list(stupid - self.COs - set(self.COm) - self.divineders))
                                elif self.alive - self.COs - set(self.COm) - self.divineders:
                                    target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders))
                                else:
                                    target = random.choice(list(self.alive - {int(self.base_info["agentIdx"])}))
                                self.kurodashi.add(target)
                                self.ts_kurodashi.append(target)
                                fake_divine_res = cb.divined(target, "WEREWOLF")
                                return fake_divine_res
                    else:
                        noMAX_vote_list = [s for s in self.vote_list if s != self.exed_players[-1]]
                        noME_noMAX_vote_list = [s for s in noMAX_vote_list if s != int(self.base_info["agentIdx"])]
                        cand = max_frequent(noME_noMAX_vote_list)
                        if cand:
                            target = random.choice(list(cand))
                        else:
                            target = random.choice(list(self.alive - {int(self.base_info["agentIdx"])}))
                        self.shirodashi.add(target)
                        self.result_seer["white"] = self.shirodashi
                        fake_divine_res = cb.divined(target, "HUMAN")
                        return fake_divine_res
                else:
                    return super().talk()
            else:
                self.SP = 1
                if self.talk_turn == 1:
                    CO_POSSESSED = cb.comingout(self.base_info['agentIdx'], "POSSESSED")
                    return CO_POSSESSED
                if self.talk_turn >= 2:
                    likely_true_divineders = self.divineders - self.fake_divineders - {int(self.base_info["agentIdx"])}
                    if likely_true_divineders:
                        sac = set()
                        for i in likely_true_divineders:
                            sac &= self.result_all_divineders[i]['white']
                        if sac:
                            target = random.choice(list(sac))
                            self.SP_target = target
                            return cb.vote(target)
                        else:
                            cands = self.alive - {int(self.base_info["agentIdx"])}
                            target = util.max_frequent_2(self.talk_vote_list, cands, 1)
                            self.SP_target = target
                            return cb.vote(target)
                    else:
                        cands = self.alive - {int(self.base_info["agentIdx"])}
                        target = util.max_frequent_2(self.talk_vote_list, cands, 1)
                        self.SP_target = target
                        return cb.vote(target)
        return super().talk()

    def vote(self):
        if self.SP == 0:
            most_voted = util.max_frequent_2(self.talk_vote_list, self.decide_vote_cand(), 1)
            return most_voted
        else:
            return self.SP_target

    def finish(self):
        return None

    def decide_vote_cand(self):
        if max_frequent(self.talk_vote_list) & self.alive\
                & (self.COs | self.divineders | set(self.COm)) - {int(self.base_info['agentIdx'])}:
            target = max_frequent(self.talk_vote_list) & self.alive\
                & (self.COs | self.divineders | set(self.COm)) - {int(self.base_info['agentIdx'])}
            return target
        if self.kurodashi & self.alive:
            target = self.kurodashi & self.alive
            return target
        black_cand = set()
        for key in self.divineders - self.fake_divineders - {int(self.base_info['agentIdx'])}:
            black_cand |= self.result_all_divineders[key]['black']
        if black_cand:
            target = self.alive - black_cand - {int(self.base_info["agentIdx"])}
            return target
        if (self.likely_white_set & self.alive) - self.shirodashi - self.divineders - self.COm:
            return (self.likely_white_set & self.alive) - self.shirodashi - self.divineders - self.COm
        target = self.alive - self.divineders - self.shirodashi - set(self.COm[:1])
        if target:
            return target
        if self.divineders - {int(self.base_info['agentIdx'])} & self.alive:
            target = self.divineders - {int(self.base_info['agentIdx'])} & self.alive
            return target
        if self.shirodashi & self.alive:
            target = self.shirodashi & self.alive
            return target
        if set(self.COm[:1]) & self.alive:
            target = set(self.COm[:1]) & self.alive
            return target
        target = self.alive - {int(self.base_info['agentIdx'])}
        return target

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
            if(sorted_res[i][1] == max_vallot):
                max_cand.add(sorted_res[i][0])
            else:
                break
        return max_cand

def YMBV(l, p):
    QP = set()
    for i in range(len(l)):
        if p == l[i]:
            QP_parse = i + 1
            QP.add(QP_parse)
    return QP

