import math

l09 = - math.log10(0.9)
l05 = - math.log10(0.5)
l03 = - math.log10(0.3)

def calc_rel_prob_divine(x):
    """update rel_prob given current divine information
    core for prediction
    """
    rel_lpdvn = 0.0
    # possessed might not divine werewolf as werewolf
    rel_lpdvn += x.dvn_cnt[2][1][1] * l09
    # werewolf might not divine possessed as werewolf
    rel_lpdvn += x.dvn_cnt[1][2][1] * l05
    # werewolf would not divine werewolf as werewolf
    rel_lpdvn += x.dvn_cnt[1][1][1] * 1
    # village Seer should not tell a lie
    rel_lpdvn += (x.dvn_cnt[0][0][1] + x.dvn_cnt[0][1][0] + x.dvn_cnt[0][2][1]) * 2
    return math.pow(10, -rel_lpdvn)

def calc_rel_prob_inquest(x):
    """update rel_prob given current inquest information
    core for prediction
    """
    # village Medium should not tell a lie
    return math.pow(0.01, x.inq_cnt[0][0][1] + x.inq_cnt[0][1][0] + x.inq_cnt[0][2][1])

def calc_rel_prob_vote(x):
    """update part of rel_prob given current vote information
    core for prediction
    """
    rel_lpvt = 0.0
    # werewolf might not vote possessed
    rel_lpvt += x.vote_cnt[1][2] * l09
    # possessed might not vote werewolf
    rel_lpvt += x.vote_cnt[2][1] * l09
    # werewolf would not vote werewolf
    rel_lpvt += x.vote_cnt[1][1] * l05
    return math.pow(10, -rel_lpvt)

def calc_rel_prob_attack(x):
    """update part of rel_prob given current attack information
    core for prediction
    """
    # werewolves are never to be attacked
    if x.atc_cnt[1] > 0:
        return 0.0
    else:
        return 1.0

def calc_rel_prob_co(x):
    """update part of rel_prob given current CO information
    core for prediction
    """
    rel_lpco = 0.0
    # village Seer would comingout
    if x.co_cnt[2][0] + x.co_cnt[1][0] > 0 and x.co_cnt[0][0] == 0:
        rel_lpco += 2.0
    # village Medium would comingout
    if x.co_cnt[2][1] + x.co_cnt[1][1] > 0 and x.co_cnt[0][1] == 0:
        rel_lpco += 2.0
    # TODO:bodyguard
    # possessed would comingout
    if sum(x.co_cnt[2]) == 0:
        rel_lpco += 1.0
    # werewolves might not comingout
    rel_lpco += (x.co_cnt[1][0] + x.co_cnt[1][1] + x.co_cnt[1][2]) * l05
    # villagers must not comingout
    if x.co_cnt[0][0] > 1:
        rel_lpco += 3.0
    if x.co_cnt[0][1] > 1:
        rel_lpco += 3.0
    if x.co_cnt[0][2] > 1:
        rel_lpco += 3.0
    return math.pow(10, -rel_lpco)

class EnemyCase(object):
    """object for each case who are werewolves and who is possessed
    get information and update fitness
    basic concept is Bayes' theorem : P(B|A) = P(B) * (P(A|B) / P(A))
    B: this case is true, A: Information
    rel_prob stands for P(B|A)
    """
    def __init__(self, ww, ps, vilsize):
        # P(B|A)
        self.rel_prob = 1.0
        self.rel_prob_co = 1.0
        self.rel_prob_vote = 1.0
        self.rel_prob_divine = 1.0
        self.rel_prob_inquest = 1.0
        self.rel_prob_attack = 1.0
        
        # member
        self.hm_idx = [idx for idx in range(1, vilsize+1) if idx != ps and idx not in ww]
        self.ww_idx = ww # werewolves
        self.ps_idx = [ps] # possessed
        self.dict_idx = dict()
        
        for idx in range(1, vilsize+1):
            if idx in self.hm_idx:
                self.dict_idx[idx] = 0
            elif idx in self.ww_idx:
                self.dict_idx[idx] = 1
            else:
                self.dict_idx[idx] = 2
        
        # vote
        # count, 0:villager, 1:werewolf, 2:possessed
        self.vote_cnt = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        # likelyhood
        # TODO 1
        
        # co 0:seer, 1:medium, 2:bodyguard
        self.co_cnt = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        # divine
        # count
        self.dvn_cnt = [[[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]]]
        # entropy
        # TODO 2
        
        # inquest
        # count
        self.inq_cnt = [[[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]]]
        # entropy
        # TODO?
        
        # attacked
        self.atc_cnt = [0, 0, 0]
    
    
    def initialize(self):
        # P(B|A)
        self.rel_prob = 1.0
        self.rel_prob_co = 1.0
        self.rel_prob_vote = 1.0
        self.rel_prob_divine = 1.0
        self.rel_prob_inquest = 1.0
        self.rel_prob_attack = 1.0
        
        # vote
        # count, 0:villager, 1:werewolf, 2:possessed
        self.vote_cnt = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        # likelyhood
        # TODO 1
        # co 0:seer, 1:medium, 2:bodyguard
        self.co_cnt = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        # divine
        # count
        self.dvn_cnt = [[[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]]]
        # entropy
        # TODO 2
        
        # inquest
        # count
        self.inq_cnt = [[[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0]]]
        # entropy
        # TODO?
        
        # attacked
        self.atc_cnt = [0, 0, 0]
    
    def return_rel_prob(self):
        """return rel_prob
        """
        return self.rel_prob
    
    def update_rel_prob(self):
        """update rel_prob given current information
        """
        self.rel_prob = self.rel_prob_co * self.rel_prob_vote * self.rel_prob_divine * self.rel_prob_inquest * self.rel_prob_attack
    
    def show_status(self):
        """for debug
        returns currrent status
        """
        # todo
        pass
    
    def get_votelist(self, votelist):
        """get votelist as list of list [[x, y],...]
        x:agent, y:target
        """
        for vote in votelist:
            self.vote_cnt[self.dict_idx[vote[0]]][self.dict_idx[vote[1]]] += 1
        # update rel_prob_vote
        self.rel_prob_vote = calc_rel_prob_vote(self)
        rel_lpvt = 0.0
    
    def get_colist(self, colist):
        """get list of new co made from talklist in form [[x, role]]
        x:agent, role:role, 0:seer, 1:medium, 2:bodyguard
        """
        for co in colist:
            self.co_cnt[self.dict_idx[co[0]]][co[1]] += 1
        # update rel_prob_co
        self.rel_prob_co = calc_rel_prob_co(self)
    
    def get_divine_list(self, divinelist):
        """get new divine result list made from talklist in form [[x, y, race]]
        x:agent, y:target, race:0:"HUMAN", 1:"WEREWOLF"
        """
        for divine in divinelist:
            self.dvn_cnt[self.dict_idx[divine[0]]][self.dict_idx[divine[1]]][divine[2]] += 1
        # update rel_prob_divine
        self.rel_prob_divine = calc_rel_prob_divine(self)
    
    def get_inquest_list(self, inquestlist):
        """get new inquest result list made from talklist in form [[x, y, race]]
        x:agent, y:target, race:0:"HUMAN", 1:"WEREWOLF"
        """
        for inquest in inquestlist:
            self.inq_cnt[self.dict_idx[inquest[0]]][self.dict_idx[inquest[1]]][inquest[2]] += 1
        # update rel_prob_inquest
        self.rel_prob_inquest = calc_rel_prob_inquest(self)

    def get_attacked(self, x):
        """get agentid newly attacked by werewolves
        x:agent
        """
        self.atc_cnt[self.dict_idx[x]] += 1
        # update rel_prob_attack
        self.rel_prob_attack = calc_rel_prob_attack(self)