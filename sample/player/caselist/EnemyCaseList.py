from case.EnemyCase import EnemyCase

# pre_calculate
glocbal_import_case_list = []
vilsize = 15
glocbal_import_case_list = []
for ps in range(1, vilsize+1):
    for w1 in range(1,vilsize-1):
        for w2 in range(w1+1, vilsize):
            for w3 in range(w2+1, vilsize+1):
                if ps not in [w1, w2, w3]:
                    glocbal_import_case_list.append(EnemyCase([w1, w2, w3], ps, vilsize))


class EnemyCaseList(object):
    """
    """
    def __init__(self, vilsize=15):
        # main object
        self.case_list = glocbal_import_case_list
    
    def initialize(self):
        for ec in self.case_list:
            ec.initialize()

    def update_rel_prob(self):
        """update rel_prob given current information
        """
        for ec in self.case_list:
            ec.update_rel_prob()

    # to return 1
    # each agent
    def prob_now(self, agent_idx):
        """return [P(agent_idx = VILLAGER), P(agent_idx = POSSESSED), P(agent_idx = WEREWOLF)]
        """
        rel_p_hm = sum([x.rel_prob for x in self.case_list if agent_idx in x.hm_idx])
        rel_p_ps = sum([x.rel_prob for x in self.case_list if agent_idx in x.ps_idx])
        rel_p_ww = sum([x.rel_prob for x in self.case_list if agent_idx in x.ww_idx])
        rel_psum = sum([x.rel_prob for x in self.case_list])
        return [rel_p_hm / rel_psum, rel_p_ps / rel_psum, rel_p_ww / rel_psum]
    
    # to return 2
    # each agent | Watashi Ninngen!
    def prob_now_wn(self, agent_idx, agent_idy):
        """return [P(agent_idx = VILLAGER), P(agent_idx = POSSESSED), P(agent_idx = WEREWOLF)]
        in condition that agent_idy = VILLAGER
        """
        rel_p_hm = sum([x.rel_prob for x in self.case_list if agent_idx in x.hm_idx and agent_idy in x.hm_idx])
        rel_p_ps = sum([x.rel_prob for x in self.case_list if agent_idx in x.ps_idx and agent_idy in x.hm_idx])
        rel_p_ww = sum([x.rel_prob for x in self.case_list if agent_idx in x.ww_idx and agent_idy in x.hm_idx])
        rel_psum = max(0.0000000001, sum([x.rel_prob for x in self.case_list if agent_idy in x.hm_idx]))
        return [rel_p_hm / rel_psum, rel_p_ps / rel_psum, rel_p_ww / rel_psum]
    # to return d1 (for debug)
    # prob for special case
    def prob_special_case(self, ww, ps):
        pel_p_spc = sum([x.rel_prob for x in self.case_list if ps in x.ps_idx and sorted(x.ww_idx) == sorted(ww)])
        rel_psum = sum([x.rel_prob for x in self.case_list])
        return  pel_p_spc / rel_psum

    def get_votelist(self, votelist):
        """get votelist as list of list [[x, y],...]
        x:agent, y:target
        """
        for ec in self.case_list:
            ec.get_votelist(votelist)

    def get_colist(self, colist):
        """get list of new co made from talklist in form [[x, role]]
        x:agent, role:role
        """
        for ec in self.case_list:
            ec.get_colist(colist)
        
    def get_divine_list(self, divinelist):
        """get new divine result list made from talklist in form [[x, y, race, p]]
        x:agent, y:target, race:"WEREWOLF" or "HUMAN", p=P(y is werewolf|x is human)
        """
        for ec in self.case_list:
            ec.get_divine_list(divinelist)

    def get_inquest_list(self, inquestlist):
        """get new inquest result list made from talklist in form [[x, y, race]]
        x:agent, y:target, race:"WEREWOLF" or "HUMAN"
        """
        for ec in self.case_list:
            ec.get_inquest_list(inquestlist)
        
    def get_attacked(self, x):
        """get agentid newly attacked by werewolves
        x:agent
        """
        for ec in self.case_list:
            ec.get_attacked(x)