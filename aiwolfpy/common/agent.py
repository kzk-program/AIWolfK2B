class Agent(object):

    def __init__(self, agent_idx: int):
        assert 0 <= agent_idx <= 99
        self.agent_idx = agent_idx

    def __str__(self):
        return 'Agent[%s]' % "{0:02d}".format(self.agent_idx)


def agent(i: int):
    assert 0 <= i <= 99
    return 'Agent[%s]' % "{0:02d}".format(i)


if __name__ == '__main__':
    a = Agent(2)
    assert str(a) == "Agent[02]"
    assert str(Agent(0)) == "Agent[00]"
    print("OK")
