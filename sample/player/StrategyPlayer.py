import caselist.EnemyCaseList
from caselist.EnemyCaseList import EnemyCaseList

debug_mode = 'n'
def print_debug(x):
    if debug_mode == 'y':
        print(x)

class StrategyPlayer(object):
    
    
    def __init__(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
        self.agentnames = ['Agent[00]',
                           'Agent[01]', 'Agent[02]', 'Agent[03]', 'Agent[04]', 'Agent[05]',
                           'Agent[06]', 'Agent[07]', 'Agent[08]', 'Agent[09]', 'Agent[10]',
                           'Agent[11]', 'Agent[12]', 'Agent[13]', 'Agent[14]', 'Agent[15]'
                           ]
        # self.agentnames[0] = 'Agent[00]' in order to avoid bug
        self.prob_ww = [0.0]*16
        self.prob_ww_wn = [0.0]*16
        self.role = game_info['roleMap'][str(self.agentIdx)]
        self.werewolves = []
        for agent_str in game_info['roleMap'].keys():
            if game_info['roleMap'][agent_str] == "WEREWOLF":
                self.werewolves.append(int(agent_str))
        self.comingout = None
        self.not_reported = False
        self.divine_result = []
        self.inquest_result = []
        self.cum_colist = []
        self.votelist = []
        self.colist = []
        self.divinelist = []
        self.inquestlist = []
        self.status_map = {"1":"ALIVE", "2":"ALIVE", "3":"ALIVE", "4":"ALIVE", "5":"ALIVE", "6":"ALIVE", "7":"ALIVE", "8":"ALIVE", "9":"ALIVE", "10":"ALIVE", "11":"ALIVE", "12":"ALIVE", "13":"ALIVE", "14":"ALIVE", "15":"ALIVE"}
        self.day = 0
        self.vote_declare = False
        self.attack_declare = False
        self.eclist = EnemyCaseList()
        self.eclist.initialize()
        self.divined_flag = [0]*16
        print_debug('NEW GAME')
        
    
    def update(self, game_info, talk_history):
        # print_debug(game_info)
        # find day
        if game_info.has_key('day'):
            self.day = game_info["day"]
        # find result
        # divine_result
        if self.role == 'SEER' and game_info.has_key('divineResult'):
            if game_info['divineResult'] is not None:
                if game_info['divineResult']["result"] == "HUMAN":
                    self.divine_result = [game_info['divineResult']["target"], 0]
                else:
                    self.divine_result = [game_info['divineResult']["target"], 1]
                self.divined_flag[game_info['divineResult']["target"]] = 1
                self.not_reported = True
        # inquest_result
        elif self.role == 'MEDIUM' and game_info.has_key('mediumResult'):
            if game_info['mediumResult'] is not None:
                if game_info['mediumResult']["result"] == "HUMAN":
                    self.inquest_result = [game_info['mediumResult']["target"], 0]
                else:
                    self.inquest_result = [game_info['mediumResult']["target"], 1]
                self.not_reported = True
        # find attacked
        attacked_agent = -1 # -1 means none
        if game_info.has_key('attackedAgent'):
            attacked_agent = game_info['attackedAgent']
            if attacked_agent != -1:
                if self.status_map[str(attacked_agent)] == "DEAD":
                    attacked_agent = -1
        # update statusmap
        if game_info.has_key('statusMap'):
            self.status_map.update(game_info['statusMap'])
        # find votelist
        if game_info.has_key('voteList'):
            if len(game_info['voteList']) > 0:
                self.votelist = [[vote_json['agent'], vote_json['target']] for vote_json in game_info['voteList'] if str(vote_json['target']) in self.status_map.keys()]
        # find comingout, divined, inquested, guarded from talk
        if len(talk_history) > 0:
            for talk_json in talk_history:
                content = talk_json['content'].split()
                # COMINGOUT
                if content[0] == 'COMINGOUT':
                    if content[2] == 'SEER':
                        co_role_no = 0
                    elif content[2] == 'MEDIUM':
                        co_role_no = 1
                    elif content[2] == 'BODYGUARD':
                        co_role_no = 2
                    else:
                        # ignore werewolf_co etc
                        co_role_no = 9
                    newco = [talk_json['agent'], co_role_no]
                    # check if it is new
                    if newco not in self.cum_colist and newco[1] != 9:
                        self.cum_colist.append(newco)
                        self.colist.append(newco)
                # DIVINED
                elif content[0] == 'DIVINED':
                    # REGARD CO SEER
                    newco = [talk_json['agent'], 0]
                    if newco not in self.cum_colist and newco[1] != 9:
                        self.cum_colist.append(newco)
                        self.colist.append(newco)
                    # new divine
                    if content[2] == 'WEREWOLF' and content[1] in self.agentnames:
                        self.divinelist.append([talk_json['agent'], self.agentnames.index(content[1]), 1])
                    elif content[1] in self.agentnames:
                        self.divinelist.append([talk_json['agent'], self.agentnames.index(content[1]), 0])
                # INQUESTED
                elif content[0] == 'INQUESTED':
                    # REGARD CO MEDIUM
                    newco = [talk_json['agent'], 1]
                    if newco not in self.cum_colist and newco[1] != 9:
                        self.cum_colist.append(newco)
                        self.colist.append(newco)
                    # new inquest
                    if content[2] == 'WEREWOLF' and content[1] in self.agentnames:
                        self.inquestlist.append([talk_json['agent'], self.agentnames.index(content[1]), 1])
                    elif content[1] in self.agentnames:
                        self.inquestlist.append([talk_json['agent'], self.agentnames.index(content[1]), 0])
                # GUARDED
                elif content[0] == 'GUARDED':
                    # REGARD CO BODYGUARD
                    newco = [talk_json['agent'], 2]
                    if newco not in self.cum_colist and newco[1] != 9:
                        self.cum_colist.append(newco)
                        self.colist.append(newco)
        #  what to do
        if attacked_agent != -1:
            print_debug('agent ' + str(attacked_agent) + 'is attacked')
            self.eclist.get_attacked(attacked_agent)
            print_debug('get votelist')
            print_debug(self.votelist)
            self.eclist.get_votelist(self.votelist)
            self.vote_declare = False
            self.votelist = []
        elif len(self.colist) > 0:
            print_debug('get colist')
            print_debug(self.colist)
            self.eclist.get_colist(self.colist)
            self.vote_declare = False
            self.colist = []
        elif len(self.divinelist) > 0:
            print_debug('get divinelist')
            print_debug(self.divinelist)
            self.eclist.get_divine_list(self.divinelist)
            self.vote_declare = False
            self.divinelist = []
        elif len(self.inquestlist) > 0:
            print_debug('get inquestlist')
            print_debug(self.inquestlist)
            self.eclist.get_inquest_list(self.inquestlist)
            self.vote_declare = False
            self.inquestlist = []
        else:
            # print_debug('Over')
            pass
        # due to 0.1s limit, only 1 action
        return None
    
    def dayStart(self):
        # possesed lie
        if self.role == 'POSSESSED' and self.day > 0:
            # who is most likely werewolf
            self.eclist.update_rel_prob()
            for i in range(1,16):
                self.prob_ww_wn[i] = self.eclist.prob_now_wn(i, self.agentIdx)[2]
            self.prob_ww_wn[0] = 0.0
            print_debug(self.prob_ww_wn)
            # do not divine dead agent
            for i in range(1,16):
                if self.status_map[str(i)] == "DEAD":
                    self.prob_ww_wn[i] = 0.0
            # do not divine self(not nesessary)
            self.prob_ww_wn[self.agentIdx] = 0.0
            # do not divine again
            for i in range(1,16):
                if self.divined_flag[i] == 1:
                    self.prob_ww_wn[i] = 0.0
            divine_target = self.prob_ww_wn.index(max(self.prob_ww_wn))
            self.divine_result = [divine_target, 0]
            self.not_reported = True
        # all roles
        # vote_declare flag
        self.vote_declare = False
        # attack_declare flag
        self.attack_declare = False
        return None
    
    def finish(self):
        return None
    
    def vote(self):
        # who is most likely werewolf
        self.eclist.update_rel_prob()
        for i in range(1,16):
            self.prob_ww_wn[i] = self.eclist.prob_now_wn(i, self.agentIdx)[2]
        self.prob_ww_wn[0] = 0.0
        print_debug(self.prob_ww_wn)
        # do not vote dead agent
        for i in range(1,16):
            if self.status_map[str(i)] == "DEAD":
                self.prob_ww_wn[i] = 0.0
        # do not vote self(not nesessary)
        self.prob_ww_wn[self.agentIdx] = 0.0
        # werewolves do not vote werewolves
        for i in range(1,16):
            if i in self.werewolves:
                self.prob_ww_wn[i] /= 2.0
        return self.prob_ww_wn.index(max(self.prob_ww_wn))
    
    def attack(self):
        # who is least likely to be werewolf
        self.eclist.update_rel_prob()
        for i in range(1,16):
            self.prob_ww[i] = self.eclist.prob_now(i)[2]
        self.prob_ww[0] = 1.0
        print_debug(self.prob_ww)
        # do not attack dead agent
        for i in range(1,16):
            if self.status_map[str(i)] == "DEAD":
                self.prob_ww[i] = 1.0
        # do not attack werewolves
        for i in range(1,16):
            if i in self.werewolves:
                self.prob_ww[i] = 1.0
        return self.prob_ww.index(min(self.prob_ww))
    
    def guard(self):
        # who is least likely to be werewolf
        self.eclist.update_rel_prob()
        for i in range(1,16):
            self.prob_ww_wn[i] = self.eclist.prob_now_wn(i, self.agentIdx)[2]
        self.prob_ww_wn[0] = 1.0
        print_debug(self.prob_ww_wn)
        # do not guard dead agent
        for i in range(1,16):
            if self.status_map[str(i)] == "DEAD":
                self.prob_ww_wn[i] = 1.0
        # do not guard self
        self.prob_ww_wn[self.agentIdx] = 1.0
        return self.prob_ww_wn.index(min(self.prob_ww_wn))
    
    def divine(self):
        # who is most likely werewolf
        self.eclist.update_rel_prob()
        for i in range(1,16):
            self.prob_ww_wn[i] = self.eclist.prob_now_wn(i, self.agentIdx)[2]
        self.prob_ww_wn[0] = 0.0
        print_debug(self.prob_ww_wn)
        # do not divine dead agent
        for i in range(1,16):
            if self.status_map[str(i)] == "DEAD":
                self.prob_ww_wn[i] = 0.0
        # do not divine self(not nesessary)
        self.prob_ww_wn[self.agentIdx] = 0.0
        # do not divine again
        for i in range(1,16):
            if self.divined_flag[i] == 1:
                self.prob_ww_wn[i] = 0.0
        return self.prob_ww_wn.index(max(self.prob_ww_wn))
    
    def talk(self):
        # comingout anyway
        if self.role == 'SEER' and self.comingout is None:
            self.comingout = 'SEER'
            return 'COMINGOUT ' + self.agentnames[self.agentIdx] + ' SEER'
        elif self.role == 'MEDIUM' and self.comingout is None:
            self.comingout = 'MEDIUM'
            return 'COMINGOUT ' + self.agentnames[self.agentIdx] + ' MEDIUM'
        elif self.role == 'POSSESSED' and self.comingout is None:
            self.comingout = 'SEER'
            return 'COMINGOUT ' + self.agentnames[self.agentIdx] + ' SEER'
        # report
        if self.role == 'SEER' and self.not_reported:
            self.not_reported = False
            if self.divine_result[1] == 0:
                return 'DIVINED ' + self.agentnames[self.divine_result[0]] + ' HUMAN'
            else:
                return 'DIVINED ' + self.agentnames[self.divine_result[0]] + ' WEREWOLF'
        elif self.role == 'MEDIUM' and self.not_reported:
            self.not_reported = False
            if self.inquest_result[1] == 0:
                return 'INQUESTED ' + self.agentnames[self.inquest_result[0]] + ' HUMAN'
            else:
                return 'INQUESTED ' + self.agentnames[self.inquest_result[0]] + ' WEREWOLF'
        elif self.role == 'POSSESSED' and self.not_reported:
            self.not_reported = False
            if self.divine_result[1] == 0:
                return 'DIVINED ' + self.agentnames[self.divine_result[0]] + ' HUMAN'
            else:
                return 'DIVINED ' + self.agentnames[self.divine_result[0]] + ' WEREWOLF'
        # not thought enough
        elif len(self.colist) > 0 or len(self.divinelist) > 0 or len(self.inquestlist) > 0:
            return 'Skip'
        elif self.vote_declare == False:
            # vote_declare
            self.vote_declare = True
            self.eclist.update_rel_prob()
            for i in range(1,16):
                self.prob_ww_wn[i] = self.eclist.prob_now_wn(i, self.agentIdx)[2]
            self.prob_ww_wn[0] = 0.0
            print_debug(self.prob_ww_wn)
            # do not vote dead agent
            for i in range(1,16):
                if self.status_map[str(i)] == "DEAD":
                    self.prob_ww_wn[i] = 0.0
            # do not vote self(not nesessary)
            self.prob_ww_wn[self.agentIdx] = 0.0
            # werewolves do not vote werewolves
            for i in range(1,16):
                if i in self.werewolves:
                    self.prob_ww_wn[i] /= 2.0
            return 'VOTE ' + self.agentnames[self.prob_ww_wn.index(max(self.prob_ww_wn))]
        else:
            return 'Over'
    
    def whisper(self):
        # not thought enough
        if len(self.colist) > 0 or len(self.divinelist) > 0 or len(self.inquestlist) > 0:
            return 'Skip'
        elif self.attack_declare == False:
            # attack_declare
            self.attack_declare = True
            # who is least likely to be werewolf
            self.eclist.update_rel_prob()
            for i in range(1,16):
                self.prob_ww[i] = self.eclist.prob_now(i)[2]
            self.prob_ww[0] = 1.0
            print_debug(self.prob_ww)
            # do not attack dead agent
            for i in range(1,16):
                if self.status_map[str(i)] == "DEAD":
                    self.prob_ww[i] = 1.0
            # do not attack werewolves
            for i in range(1,16):
                if i in self.werewolves:
                    self.prob_ww[i] = 1.0
            return 'ATTACK ' + self.agentnames[self.prob_ww.index(min(self.prob_ww))]
        else:
            return 'Over'

    def getName(self):
        return self.name

