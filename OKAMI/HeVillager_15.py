import aiwolfpy_old.contentbuilder as cb
import util
import KULASIS

class VillagerBehavior():
    def __init__(self, agent_name, agent_list):
        self.myname = agent_name
        self.todays_vote = None
        self.agent_list = agent_list
        self.agent_name_list = ["OKAMI", "Camellia", "FoxuFoxu", "otsuki", "Sashimi", "wasabi", "takeda", "Tomato", \
                                "daisyo", "Udon", "J0hnDoe", "Tomo", "cube", "PaSeRi", "simipu"]

    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting
        self.player_size = game_setting["playerNum"]
        self.greys = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
        self.alive = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
        self.COs = set()
        self.COm = []
        self.COg = set()
        self.COp = set()
        self.result_all_divineders = {}
        self.result_all_mediums = {}
        self.exed_players = []
        self.ated_players = []
        self.divineders = set()
        self.fake_divineders = set()
        self.likely_fake_divineders = set()
        self.result_guard = set()
        self.under_7_vote = {0: -1}
        self.attack_judge = 0
        self.vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.talk_vote_list = self.vote_list.copy()
        self.yesterday_vote_list = self.vote_list.copy()
        self.likely_black_set = set()
        self.likely_white_set = set()
        self.likely_fake_mediums_set = set()
        self.likely_bodyguard_set = set()
        self.W_COs = set()
        self.W_COm = set()
        self.W_COg = set()
        self.W_vote_cand = set()
        self.W_attack_cand = set()
        self.day_agent = set()
        self.or_agent = set()
        self.and_agent = set()
        self.xor_agent = set()
        self.not_agent = set()
        self.because_agent = set()
        self.request_agent = set()
        self.estimate_agent = set()
        self.agree_agent = set()
        self.disagree_agent = set()
        self.divine_day = {}
        for i in range(15):
            self.divine_day[i + 1] = []
        self.identify_day = {}
        for i in range(15):
            self.identify_day[i + 1] = []
        self.request_divination_agent = set()
        self.request_comingout_seer_agent = set()
        self.request_guard_agent = set()
        self.request_any_vote_agent = set()
        self.request_any_vote_non_and_agent = set()
        self.estimate_werewolf_agent = set()
        self.estimate_non_werewolf_agent = set()
        self.and_day_divined_agent = set()
        self.COv = set()
        self.estimate_villager_agent = set()
        self.Camellia_because_agent = set()
        self.day2_alive = set()

    def update(self, base_info, diff_data, request):
        self.base_info = base_info
        self.diff_data = diff_data
        for i in self.diff_data.iterrows():
            line = i[1]
            KULASIS.log_analytics_main(self, i, line["type"])
        if self.COm:
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                if CO_seer not in self.agent_list[4]:
                    if len(self.COm) == 1:
                        if self.result_all_mediums[self.COm[0]]["black"] & self.result_all_divineders[CO_seer]["white"]:
                            self.fake_divineders.add(CO_seer)
                        if self.result_all_divineders[CO_seer]["black"] & self.result_all_mediums[self.COm[0]]["white"]:
                            self.fake_divineders.add(CO_seer)
                        if self.COm[0] in self.result_all_divineders[CO_seer]["black"]:
                            self.fake_divineders.add(CO_seer)
                    elif len(self.COm) > 1:
                        if self.result_all_mediums[self.COm[0]]["black"] & self.result_all_mediums[self.COm[1]]["black"] \
                                & self.result_all_divineders[CO_seer]["white"]:
                            self.fake_divineders.add(CO_seer)
                        if self.result_all_divineders[CO_seer]["black"] & self.result_all_mediums[self.COm[1]]["white"] \
                                & self.result_all_mediums[self.COm[0]]["white"]:
                            self.fake_divineders.add(CO_seer)
        if self.ated_players:
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                if CO_seer not in self.agent_list[4]:
                    if self.result_all_divineders[CO_seer]["black"] & set(self.ated_players):
                        self.fake_divineders.add(CO_seer)
        if self.divineders:
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                if self.result_all_divineders[CO_seer]["black"] & self.result_all_divineders[CO_seer]["white"]:
                    self.fake_divineders.add(CO_seer)
        if self.base_info["myRole"] == "VILLAGER":
            for CO_seer in list(self.divineders):
                if CO_seer not in self.agent_list[4]:
                    if int(self.base_info['agentIdx']) in self.result_all_divineders[CO_seer]["black"]:
                        self.likely_fake_divineders.add(CO_seer)
        if self.likely_fake_mediums_set:
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                if CO_seer not in self.agent_list[4]:
                    for i in set(self.COm[:2]) - self.likely_fake_mediums_set:
                        if self.result_all_mediums[i]["black"] & self.result_all_divineders[CO_seer]["white"]:
                            self.likely_fake_divineders.add(CO_seer)
                        if self.result_all_divineders[CO_seer]["black"] & self.result_all_mediums[i]["white"]:
                            self.likely_fake_divineders.add(CO_seer)
                        if i in self.result_all_divineders[CO_seer]["black"]:
                            self.likely_fake_divineders.add(CO_seer)
        self.pudding()
        self.alfort()

    def dayStart(self):
        self.talk_turn = 0
        self.todays_vote = None
        self.talk_vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.yesterday_vote_list = self.vote_list[:]
        self.vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if int(self.base_info['day']) == 2:
            self.day2_alive |= self.alive
        return None

    def talk(self):
        if self.base_info["myRole"] == 'VILLAGER':
            if self.talk_turn == 1:
                self.talk_turn += 1
                return cb.comingout(self.base_info['agentIdx'], "VILLAGER")
            else:
                self.talk_turn += 1
        if self.talk_turn < 10:
            return cb.vote(self.vote())
        return cb.over()

    def whisper(self):
        return cb.over()

    def vote(self):
        cands = self.vote_cand()
        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 0)
        return most_voted

    def vote_cand(self):
        if len(self.alive) <= 7 and self.under_7_vote:
            if self.under_7_vote.pop(0, None):
                self.under_7_vote = {i: 0 for i in self.alive}
            for i in set(j + 1 for j in range(15) if self.yesterday_vote_list[j] == self.exed_players[-1]) & self.alive:
                if i in self.under_7_vote:
                    self.under_7_vote[i] += 1
            self.yesterday_vote_list = self.vote_list[:]
            for i in set(self.under_7_vote.keys()) - self.alive:
                self.under_7_vote.pop(i, None)
            if self.result_guard & self.under_7_vote.keys():
                for i in self.result_guard & self.under_7_vote.keys():
                    self.under_7_vote.pop(i, None)
            # 辞書が空でなければ、最多得票者に投票した回数が多い人の集合を返す
            if len(self.under_7_vote):
                under_7_max_vote = {i[0] for i in self.under_7_vote.items() \
                                    if i[1] == max(self.under_7_vote.values())}
                return under_7_max_vote
        true_black = self.alive.copy()
        true_white = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]["black"]
            true_white &= self.result_all_divineders[key]["white"]
        true_white |= self.result_guard & self.alive
        if self.divineders and true_black:
            return true_black
        if len(self.divineders) >= 3:
            if self.divineders & self.alive:
                result_medium_black = set()
                if len(self.COm) == 1:
                    result_medium_black = self.result_all_mediums[self.COm[0]]["black"]
                elif len(self.COm) >= 2:
                    result_medium_black = self.result_all_mediums[self.COm[0]]["black"] \
                                          & self.result_all_mediums[self.COm[1]]["black"]
                if len(self.divineders - result_medium_black) >= 3:
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
        my_greys = not_fake_divineders_greys - self.divineders - self.COs - set(self.COm) \
                   - true_white - {int(self.base_info["agentIdx"])}
        if my_greys:
            return my_greys
        if self.fake_divineders:
            return self.fake_divineders
        return self.alive - {int(self.base_info["agentIdx"])}

    def attack(self):
        return self.base_info['agentIdx']

    def divine(self):
        return self.base_info['agentIdx']

    def guard(self):
        return self.base_info['agentIdx']

    def finish(self):
        return None

    def pudding(self):
        yogurt = False
        if self.agent_list[0] == 1:
            if not self.agent_list[2][1]:
                if len(self.request_divination_agent) == 1:
                    if list(self.request_divination_agent)[0] not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][1] = list(self.request_divination_agent)[0]
                        self.agent_list[6] |= {self.agent_list[2][1]}
                elif len(self.request_comingout_seer_agent) == 1:
                    if list(self.request_comingout_seer_agent)[0] not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][1] = list(self.request_comingout_seer_agent)[0]
                        self.agent_list[6] |= {self.agent_list[2][1]}
                elif len(self.request_guard_agent) == 1:
                    if list(self.request_guard_agent)[0] not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][1] = list(self.request_guard_agent)[0]
                        self.agent_list[6] |= {self.agent_list[2][1]}
                elif len(self.Camellia_because_agent) == 1:
                    if list(self.Camellia_because_agent)[0] not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][1] = list(self.Camellia_because_agent)[0]
                        self.agent_list[6] |= {self.agent_list[2][1]}
                elif self.agent_list[2][3] and self.agent_list[1] > 1:
                    for k, v in self.divine_day.items():
                        if k not in {self.agent_list[2][3]} | {self.agent_list[2][4]} | self.agent_list[5]:
                            if len(v) > 2:
                                if v[-3:] == [1, 2, 3] or v[:3] == [1, 1, 2]:
                                    if k not in self.agent_list[2]:
                                        yogurt = True
                                        self.agent_list[2][1] = k
                                        self.agent_list[6] |= {k}
            if self.agent_list[1] == 1:
                if ((self.xor_agent | self.not_agent | self.because_agent) - self.agent_list[5])\
                        - {self.agent_list[2][4]}:
                    yogurt = True
                    self.agent_list[5] |= self.xor_agent | self.not_agent | self.because_agent
                    self.agent_list[6] |= self.agent_list[5]
                    self.agent_list[7] |= self.agent_list[5]
            if not self.agent_list[2][5] and self.agent_list[1] > 1:
                if len(self.estimate_villager_agent - (self.agent_list[5] & {self.agent_list[2][4]})) == 1:
                    if list(self.estimate_villager_agent - (self.agent_list[5] \
                                                            & {self.agent_list[2][4]}))[0] not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][5] = list(self.estimate_villager_agent \
                                                     - (self.agent_list[5] & {self.agent_list[2][4]}))[0]
                        self.agent_list[6] |= {self.agent_list[2][5]}
            if not self.agent_list[2][3] and self.agent_list[2][5] and self.agent_list[1] > 1:
                if len(self.estimate_agent - (self.agent_list[5] | \
                                              {self.agent_list[2][4]} | {self.agent_list[2][5]})) == 1:
                    if list(self.estimate_agent - (self.agent_list[5] | {self.agent_list[2][4]} \
                                                   | {self.agent_list[2][5]}))[0] not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][3] = list(self.estimate_agent - (self.agent_list[5] | \
                                                                            {self.agent_list[2][4]} | {
                                                                                self.agent_list[2][5]}))[0]
                        self.agent_list[6] |= {self.agent_list[2][3]}
                        self.agent_list[7] |= {self.agent_list[2][3]}
            if not self.agent_list[2][3] and self.agent_list[1] > 1:
                if len(self.and_day_divined_agent - (self.agent_list[5] | {self.agent_list[2][4]})) == 1:
                    if list(self.and_day_divined_agent - (self.agent_list[5] | {self.agent_list[2][4]}))[0] \
                            not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][3] = list(self.and_day_divined_agent - \
                                                     (self.agent_list[5] | {self.agent_list[2][4]}))[0]
                        self.agent_list[6] |= {self.agent_list[2][3]}
                        self.agent_list[7] |= {self.agent_list[2][3]}
        if not self.agent_list[2][4]:
            if self.request_any_vote_non_and_agent & self.agent_list[5]:
                if list(self.request_any_vote_non_and_agent & self.agent_list[5])[0] not in self.agent_list[2]:
                    yogurt = True
                    self.agent_list[2][4] = list(self.request_any_vote_non_and_agent & self.agent_list[5])[0]
                    self.agent_list[5] -= self.request_any_vote_non_and_agent
        if not self.agent_list[2][2]:
            for k, v in self.divine_day.items():
                if len(v) > 2:
                    if v[-3:] == [3, 2, 1] or (v[:3] == [1, 2, 1] and int(self.base_info['day']) == 2):
                        if k not in self.agent_list[2]:
                            yogurt = True
                            self.agent_list[2][2] = k
                            self.agent_list[6] |= {k}
        if not self.agent_list[2][2]:
            for k, v in self.identify_day.items():
                if (len(v) > 1 and v[0] - v[1] == 1) or (len(v) > 2 and v[:3] == [2, 3, 2]):
                    if k not in self.agent_list[2]:
                        yogurt = True
                        self.agent_list[2][2] = k
                        self.agent_list[6] |= {k}
        if not self.agent_list[2][7]:
            if len(self.COv) == 1:
                if list(self.COv)[0] not in self.agent_list[2]:
                    yogurt = True
                    self.agent_list[2][7] = list(self.COv)[0]
                    self.agent_list[6] |= {self.agent_list[2][7]}
                    self.agent_list[7] |= {self.agent_list[2][7]}
        if not self.agent_list[2][8] and int(self.base_info['day']) == 1:
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                if len(self.result_all_divineders[CO_seer]["black"])\
                        + len(self.result_all_divineders[CO_seer]["white"]) > 1:
                    yogurt = True
                    self.agent_list[2][8] = CO_seer
                    self.agent_list[6] |= {self.agent_list[2][8]}
                    self.agent_list[7] |= {self.agent_list[2][8]}
        if self.agent_list[0] == 1:
            if min(self.agent_list[2][:2] + self.agent_list[2][3:6]):
                yogurt = True
                self.agent_list[0] = 2
        elif self.agent_list[0] == 2:
            if self.agent_list[2][2] and self.agent_list[2][7]:
                damito1 = self.agent_list[5] | set(self.agent_list[2][:6])
                if len((self.agent_list[6] & self.agent_list[7]) - damito1) == 3:
                    if len(self.agent_list[6] - self.agent_list[7] - damito1) == 1:
                        yogurt = True
                        self.agent_list[0] = 3
                        if list(self.agent_list[6] - self.agent_list[7] - damito1)[0] not in self.agent_list[2]:
                            self.agent_list[2][9] = list(self.agent_list[6] - self.agent_list[7] - damito1)[0]
                        if self.agent_list[2][7]:
                            if len((self.agent_list[6] & self.agent_list[7]) - damito1 - {self.agent_list[2][7]}) == 2:
                                if not ((self.agent_list[6] & self.agent_list[7]) - damito1 - {self.agent_list[2][7]}) \
                                       & set(self.agent_list[2]):
                                    self.agent_list[2][6] = list((self.agent_list[6] & self.agent_list[7]) \
                                                                 - damito1 - {self.agent_list[2][7]})[0]
                                    self.agent_list[2][8] = list((self.agent_list[6] & self.agent_list[7]) \
                                                                 - damito1 - {self.agent_list[2][7]})[1]
                        shojiki = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15} - self.agent_list[3] \
                                  - self.agent_list[5] - self.agent_list[6] - self.agent_list[7]
                        if shojiki:
                            self.agent_list[4] |= shojiki
        if yogurt:
            self.pudding()

    def alfort(self):
        if len(self.COs & self.divineders) == 2 and len(self.COs & self.divineders & self.agent_list[4]) == 1:
            if not list((self.COs & self.divineders) - self.agent_list[4])[0] in self.agent_list[6]:
                self.tokutei(list((self.COs & self.divineders) - self.agent_list[4])[0], "WEREWOLF")
            else:
                self.tokutei(list((self.COs & self.divineders) - self.agent_list[4])[0], "POSSESSED")
        elif len(self.COs & self.divineders) == 3 and len(self.COs & self.divineders & self.agent_list[4]) == 1:
            self.tokutei(list(self.COs & self.divineders & self.agent_list[4])[0], "SEER")
            if len(self.likely_fake_divineders) == 2 and len(self.likely_fake_divineders - self.agent_list[6]) == 1:
                self.tokutei(list(self.likely_fake_divineders - self.agent_list[6])[0], "WEREWOLF")
        if len(self.COm) == 2 and len(set(self.COm) & self.agent_list[4]) == 1:
            self.tokutei(list(set(self.COm) - self.agent_list[4])[0], "WEREWOLF")
        if self.agent_list[2][1]:
            if self.agent_list[2][1] in self.request_comingout_seer_agent:
                self.tokutei(self.agent_list[2][1], "VILLAGER")
            elif self.agent_list[2][1] in self.request_guard_agent:
                self.tokutei(self.agent_list[2][1], "MEDIUM")
            elif self.agent_list[2][1] in self.Camellia_because_agent:
                self.tokutei(self.agent_list[2][1], "MEDIUM")
            elif self.agent_list[2][1] in self.request_any_vote_agent:
                self.tokutei(self.agent_list[2][1], "WEREWOLF")
            elif self.agent_list[2][1] in self.request_divination_agent:
                self.tokutei(self.agent_list[2][1], "VILLAGER")
            elif self.agent_list[2][1] in self.divineders and self.divine_day[self.agent_list[2][1]]:
                self.tokutei(self.agent_list[2][1], "SEER")
            elif self.agent_list[2][1] in self.divineders and not self.divine_day[self.agent_list[2][1]]:
                self.tokutei(self.agent_list[2][1], "POSSESSED")
        if self.agent_list[2][4]:
            if self.agent_list[2][4] in self.request_any_vote_non_and_agent:
                self.tokutei(self.agent_list[2][4], "VILLAGER")
        if self.agent_list[2][7]:
            if self.agent_list[2][7] in self.COv:
                self.tokutei(self.agent_list[2][7], "WEREWOLF")
        if len(self.COs & self.divineders) == 3:
            if self.agent_list[2][6] and self.agent_list[2][6] in self.COs & self.divineders & self.likely_black_set:
                self.likely_white_set |= self.result_all_divineders[self.agent_list[2][6]]["black"]
                self.likely_black_set |= self.result_all_divineders[self.agent_list[2][6]]["white"]
            if self.agent_list[2][8] and self.agent_list[2][8] in self.COs & self.divineders & self.likely_black_set:
                self.likely_white_set |= self.result_all_divineders[self.agent_list[2][8]]["black"]
                self.likely_black_set |= self.result_all_divineders[self.agent_list[2][8]]["white"]
        if self.agent_list[2][8] and int(self.base_info['day']) == 1:
            if len(self.result_all_divineders[self.agent_list[2][8]]["black"])\
                        + len(self.result_all_divineders[self.agent_list[2][8]]["white"]) > 1:
                self.tokutei(self.agent_list[2][8], "POSSESSED")

    def tokutei(self, target=0, target_role="VILLAGER"):
        if target not in range(1, 16) or target == int(self.base_info['agentIdx']):
            return
        if target_role == "SEER" and self.base_info["myRole"] != "SEER":
            self.likely_fake_divineders |= self.divineders - {target}
        elif target_role == "MEDIUM" and self.base_info["myRole"] != "MEDIUM":
            self.likely_fake_mediums_set |= set(self.COm[:2]) - {target}
        elif target_role == "BODYGUARD" and self.base_info["myRole"] != "BODYGUARD":
            self.likely_bodyguard_set |= {target}
            self.likely_white_set |= {target}
        elif target_role == "WEREWOLF" and self.base_info["myRole"] != "WEREWOLF":
            self.likely_black_set |= {target}
            if target in self.divineders:
                self.likely_fake_divineders |= {target}
            if target in self.COm[:2]:
                self.likely_fake_mediums_set |= {target}
        elif target_role == "POSSESSED" and self.base_info["myRole"] != "POSSESSED":
            self.likely_fake_divineders |= {target}
        elif target_role == "VILLAGER":
            self.likely_white_set |= {target}
