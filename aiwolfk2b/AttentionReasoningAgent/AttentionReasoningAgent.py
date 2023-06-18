# pythonのprotocol用のエージェントのインスタンスを渡して、NLのエージェントとして使えるようにするラッパー.
import argparse
import configparser
import errno

import os
import random
import sys
from logging import FileHandler, Formatter, StreamHandler, getLogger

import pandas as pd
from aiwolf import TcpipClient


from typing import Dict, List
from aiwolf import (AbstractPlayer, Agent, Content, GameInfo, GameSetting,
                    Judge, Role, Species, Status, Talk, Topic,
                    VoteContentBuilder,SkipContentBuilder)
from aiwolf.constant import AGENT_NONE

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import *
from aiwolfk2b.AttentionReasoningAgent.SimpleModules import *

CONTENT_SKIP: Content = Content(SkipContentBuilder())

class AttentionReasoningAgent(AbstractPlayer):
    """Sample villager agent."""

    me: Agent
    """Myself."""
    vote_candidate: Agent
    """Candidate for voting."""
    game_info: GameInfo
    """Information about current game."""
    game_setting: GameSetting
    """Settings of current game."""
    comingout_map: Dict[Agent, Role]
    """Mapping between an agent and the role it claims that it is."""
    divination_reports: List[Judge]
    """Time series of divination reports."""
    identification_reports: List[Judge]
    """Time series of identification reports."""
    talk_list_head: int
    """Index of the talk to be analysed next."""

    def __init__(self,config) -> None:
        """Initialize a new instance of SampleVillager."""

        self.me = AGENT_NONE
        self.vote_candidate = AGENT_NONE
        self.game_info = None  # type: ignore
        self.comingout_map = {}
        self.divination_reports = []
        self.identification_reports = []
        self.talk_list_head = 0
        self.config = config
        #各モジュールの生成
        self.role_estimation_model:AbstractRoleEstimationModel = RandomRoleEstimationModel(self.config)
        self.role_inference_module:AbstractRoleInferenceModule = SimpleRoleInferenceModule(self.config,self.role_estimation_model)
        self.strategy_module:AbstractStrategyModule = SimpleStrategyModule(self.config,self.role_estimation_model,self.role_inference_module)
        self.request_processing_module:AbstractRequestProcessingModule = SimpleRequestProcessingModule(self.config,self.role_estimation_model,self.strategy_module)
        self.question_processing_module:AbstractQuestionProcessingModule = SimpleQuestionProcessingModule(self.config,self.role_inference_module,self.strategy_module)
        self.influence_consideration_module:AbstractInfluenceConsiderationModule = SimpleInfluenceConsiderationModule(self.config,self.request_processing_module,self.question_processing_module)
        self.speaker_module:AbstractSpeakerModule = SimpleSpeakerModule(self.config)

    def is_alive(self, agent: Agent) -> bool:
        """Return whether the agent is alive.

        Args:
            agent: The agent.

        Returns:
            True if the agent is alive, otherwise false.
        """
        return self.game_info.status_map[agent] == Status.ALIVE

    def get_others(self, agent_list: List[Agent]) -> List[Agent]:
        """Return a list of agents excluding myself from the given list of agents.

        Args:
            agent_list: The list of agent.

        Returns:
            A list of agents excluding myself from agent_list.
        """
        return [a for a in agent_list if a != self.me]

    def get_alive(self, agent_list: List[Agent]) -> List[Agent]:
        """Return a list of alive agents contained in the given list of agents.

        Args:
            agent_list: The list of agents.

        Returns:
            A list of alive agents contained in agent_list.
        """
        return [a for a in agent_list if self.is_alive(a)]

    def get_alive_others(self, agent_list: List[Agent]) -> List[Agent]:
        """Return a list of alive agents that is contained in the given list of agents
        and is not equal to myself.

        Args:
            agent_list: The list of agents.

        Returns:
            A list of alie agents that is contained in agent_list
            and is not equal to mysef.
        """
        return self.get_alive(self.get_others(agent_list))

    def random_select(self, agent_list: List[Agent]) -> Agent:
        """Return one agent randomly chosen from the given list of agents.

        Args:
            agent_list: The list of agents.

        Returns:
            A agent randomly chosen from agent_list.
        """
        return random.choice(agent_list) if agent_list else AGENT_NONE

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        self.game_info = game_info
        self.game_setting = game_setting
        self.me = game_info.me
        # Clear fields not to bring in information from the last game.
        self.comingout_map.clear()
        self.divination_reports.clear()
        self.identification_reports.clear()
        #各モジュールの初期化
        self.role_estimation_model.initialize(game_info,game_setting)
        self.role_inference_module.initialize(game_info,game_setting)
        self.strategy_module.initialize(game_info,game_setting)
        self.request_processing_module.initialize(game_info,game_setting)
        self.question_processing_module.initialize(game_info,game_setting)
        self.influence_consideration_module.initialize(game_info,game_setting)
        self.speaker_module.initialize(game_info,game_setting)

    def day_start(self) -> None:
        self.talk_list_head = 0
        self.vote_candidate = AGENT_NONE

    def update(self, game_info: GameInfo) -> None:
        self.game_info = game_info  # Update game information.
        for i in range(self.talk_list_head, len(game_info.talk_list)):  # Analyze talks that have not been analyzed yet.
            tk: Talk = game_info.talk_list[i]  # The talk to be analyzed.
            talker: Agent = tk.agent
            if talker == self.me:  # Skip my talk.
                continue
            content: Content = Content.compile(tk.text)
            if content.topic == Topic.COMINGOUT:
                self.comingout_map[talker] = content.role
            elif content.topic == Topic.DIVINED:
                self.divination_reports.append(Judge(talker, game_info.day, content.target, content.result))
            elif content.topic == Topic.IDENTIFIED:
                self.identification_reports.append(Judge(talker, game_info.day, content.target, content.result))
        self.talk_list_head = len(game_info.talk_list)  # All done.

    def talk(self) -> Content:
        # # Choose an agent to be voted for while talking.
        # #
        # # The list of fake seers that reported me as a werewolf.
        # fake_seers: List[Agent] = [j.agent for j in self.divination_reports
        #                            if j.target == self.me and j.result == Species.WEREWOLF]
        # # Vote for one of the alive agents that were judged as werewolves by non-fake seers.
        # reported_wolves: List[Agent] = [j.target for j in self.divination_reports
        #                                 if j.agent not in fake_seers and j.result == Species.WEREWOLF]
        # candidates: List[Agent] = self.get_alive_others(reported_wolves)
        # # Vote for one of the alive fake seers if there are no candidates.
        # if not candidates:
        #     candidates = self.get_alive(fake_seers)
        # # Vote for one of the alive agents if there are no candidates.
        # if not candidates:
        #     candidates = self.get_alive_others(self.game_info.agent_list)
        # # Declare which to vote for if not declare yet or the candidate is changed.
        # if self.vote_candidate == AGENT_NONE or self.vote_candidate not in candidates:
        #     self.vote_candidate = self.random_select(candidates)
        #     if self.vote_candidate != AGENT_NONE:
        #         return Content(VoteContentBuilder(self.vote_candidate))
        # return CONTENT_SKIP
        strategy_content = self.strategy_module.talk(self.game_info,self.game_setting)
        influenced = self.influence_consideration_module.check_influence(self.game_info,self.game_setting)
        if influenced[0]:
            return influenced[1].reason
        else:
            return strategy_content

    def vote(self) -> Agent:
        return self.strategy_module.vote(self.game_info,self.game_setting)
        #return self.vote_candidate if self.vote_candidate != AGENT_NONE else self.me

    def attack(self) -> Agent:
        return self.strategy_module.attack(self.game_info,self.game_setting)
        #return self.vote_candidate if self.vote_candidate != AGENT_NONE else self.me

    def divine(self) -> Agent:
        return self.strategy_module.divine(self.game_info,self.game_setting)
        #return self.vote_candidate if self.vote_candidate != AGENT_NONE else self.me
    
    def guard(self) -> Agent:
        return self.strategy_module.guard(self.game_info,self.game_setting)
        #return self.vote_candidate if self.vote_candidate != AGENT_NONE else self.me

    def whisper(self) -> Content:
        text =self.strategy_module.whisper(self.game_info,self.game_setting)
        rich_text = self.speaker_module.enhance_speech(text)
        return rich_text
        #return CONTENT_SKIP

    def finish(self) -> None:
        pass
    
# run
if __name__ == '__main__':
    # read args
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-p', type=int, action='store', dest='port')
    parser.add_argument('-h', type=str, action='store', dest='hostname')
    parser.add_argument('-r', type=str, action='store', dest='role', default='none')
    parser.add_argument('-n', type=str, action='store', dest='name', default='default_sample_python')
    input_args = parser.parse_args()
    
    # config
    config_ini = configparser.ConfigParser()
    config_ini_path = '/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/config.ini'

    # iniファイルが存在するかチェック
    if os.path.exists(config_ini_path):
        # iniファイルが存在する場合、ファイルを読み込む
        with open(config_ini_path, encoding='utf-8') as fp:
            config_ini.read_file(fp)
    else:
        # iniファイルが存在しない場合、エラー発生
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)

    agent: AbstractPlayer = AttentionReasoningAgent(config_ini)
    
    client = TcpipClient(agent, input_args.name, input_args.hostname, input_args.port, input_args.role)
    client.connect()