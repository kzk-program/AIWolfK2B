import HeVillager_15 as VillagerBehavior
import random
class BodyguardBehavior(VillagerBehavior.VillagerBehavior):
    def __init__(self, agent_name, agent_list):
        super().__init__(agent_name, agent_list)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.ated_players_num = 0
        self.guarded_player = 0
        self.added_player_to_result_guard = False
        self.number_killed_in_previous_turn = 0
        self.number_alive_in_previous_turn = len(self.alive)
        for CO_seer in list(self.divineders - self.fake_divineders):
            if CO_seer not in self.agent_list[4]:
                if int(self.base_info['agentIdx']) in self.result_all_divineders[CO_seer]["black"]:
                    self.likely_fake_divineders.add(CO_seer)
                if self.result_guard & self.result_all_divineders[CO_seer]["black"]:
                    self.likely_fake_divineders.add(CO_seer)

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

    def dayStart(self):
        super().dayStart()
        self.added_player_to_result_guard = False
        self.number_killed_in_previous_turn = len(self.alive) - self.number_alive_in_previous_turn
        self.number_alive_in_previous_turn = len(self.alive)
        return None

    def talk(self):
        self.talk_turn += 1
        if self.talk_turn == 1:
            if (not self.added_player_to_result_guard) and self.ated_players_num == len(self.ated_players):
                self.result_guard.add(self.guarded_player)
                self.added_player_to_result_guard = True
            self.ated_players_num = len(self.ated_players)

        return super().talk()

    def vote(self):
        return super().vote()

    def guard(self):
        if self.number_killed_in_previous_turn == 1:
            return self.guarded_player
        true_black = self.alive.copy()
        true_white = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]["black"]
            true_white &= self.result_all_divineders[key]["white"]
        true_white |= self.result_guard & self.alive
        if len(self.divineders) >= 3:
            if set(self.COm[:1]) & self.alive:
                target = random.choice(list(set(self.COm[:1]) & self.alive))
                self.guarded_player = target
                return target
        if self.base_info["day"] == 1:
            divined_black = set()
            for key in self.divineders:
                divined_black |= self.result_all_divineders[key]["black"]
            if self.exed_players and self.exed_players[0] in divined_black:
                if len(self.COm) == 1 and self.COm[0] in self.alive:
                    target = self.COm[0]
                    self.guarded_player = target
                    return target
        if self.alive & self.divineders - self.fake_divineders - self.likely_fake_divineders:
            target = random.choice(list(self.alive & self.divineders - self.fake_divineders - self.likely_fake_divineders))
            self.guarded_player = target
            return target
        if len(self.COm) == 1 and self.COm[0] in self.alive:
            target = self.COm[0]
            self.guarded_player = target
            return target
        if true_white:
            target = random.choice(list(true_white))
            self.guarded_player = target
            return target
        if self.alive - {int(self.base_info['agentIdx'])} - true_black\
                - self.fake_divineders - self.likely_fake_divineders:
            target = random.choice(list(self.alive - {int(self.base_info['agentIdx'])}\
                    - true_black - self.fake_divineders - self.likely_fake_divineders))
            self.guarded_player = target
            return target
        target = random.choice(list(self.alive - {int(self.base_info['agentIdx'])}))
        self.guarded_player = target
        return target

    def finish(self):
        return None
