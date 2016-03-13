#!/usr/bin/env python
from __future__ import print_function
import argparse
from net.Client import AIWOLFPythonClient
### begin edit ###
# import your class here
from player.base import BasePlayer as AgentClass
# your name here
your_name = 'your_name'
### end edit ###

# parse Args
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-p', type=int, action='store', dest='port')
parser.add_argument('-h', type=str, action='store', dest='hostname')
input_args = parser.parse_args()

aiwolf_host = input_args.hostname
aiwolf_port = input_args.port

# run
if __name__ == '__main__':
    AIWOLFPythonClient(AgentClass, aiwolf_host, aiwolf_port, your_name)