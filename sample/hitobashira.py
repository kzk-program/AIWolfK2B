#!/usr/bin/env python
from __future__ import print_function
import argparse

from player.StrategyPlayer import StrategyPlayer
from net.Client import AIWOLFPythonClient

debug_mode = 'n'
def print_debug(x):
    if debug_mode == 'y':
        print(x)

# version info, comment out this
print_debug('this is ver0307')

# parse Args
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-p', type=int, action='store', dest='port')
parser.add_argument('-h', type=str, action='store', dest='hostname')
input_args = parser.parse_args()
aiwolf_host = input_args.hostname
aiwolf_port = input_args.port

# agent class
AgentClass = StrategyPlayer




# run
if __name__ == '__main__':
    AIWOLFPythonClient(AgentClass, aiwolf_host, aiwolf_port, 'cash')