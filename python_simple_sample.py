#!/usr/bin/env python
from __future__ import print_function, division

# This sample script connects to the AIWolf server, but
# does not do anything else. It will choose itself as the
# target for any actions requested by the server, (voting,
# attacking ,etc) forcing the server to choose a random target.

import aiwolfpy
import aiwolfpy.contentbuilder as cb

myname = 'sample_python'

class SampleAgent(object):
    def __init__(self, agent_name):
        # myname
        self.myname = agent_name

    def getName(self):
        return self.myname

    # new game (no return)
    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting
        # print(base_info)
        # print(diff_data)

    # new information (no return)
    def update(self, base_info, diff_data, request):
        self.base_info = base_info
        # print(base_info)
        # print(diff_data)

    # Start of the day (no return)
    def dayStart(self):
        return None

    # conversation actions: require a properly formatted
    # protocol string as the return.
    def talk(self):
        return cb.over()

    def whisper(self):
        return cb.over()

    # targetted actions: Require the id of the target
    # agent as the return
    def vote(self):
        return self.base_info['agentIdx']

    def attack(self):
        return self.base_info['agentIdx']

    def divine(self):
        return self.base_info['agentIdx']

    def guard(self):
        return self.base_info['agentIdx']

    # Finish (no return)
    def finish(self):
        return None

agent = SampleAgent(myname)

# run
if __name__ == '__main__':
    aiwolfpy.connect_parse(agent)
