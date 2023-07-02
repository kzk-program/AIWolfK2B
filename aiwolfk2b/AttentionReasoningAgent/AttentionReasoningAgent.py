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

from aiwolfk2b.utils.helper import load_default_config
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import *
from aiwolfk2b.AttentionReasoningAgent.SimpleModules import *
from aiwolfk2b.AttentionReasoningAgent.Modules import *


CONTENT_SKIP: Content = Content(SkipContentBuilder())


#現在のプログラムが置かれているディレクトリを取得
import pathlib
current_dir = pathlib.Path(__file__).resolve().parent

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
        self.role_estimation_model:AbstractRoleEstimationModel = BERTRoleEstimationModel(self.config)
        self.role_inference_module:AbstractRoleInferenceModule = BERTRoleInferenceModule(self.config,self.role_estimation_model)
        self.strategy_module:AbstractStrategyModule = StrategyModule(self.config,self.role_estimation_model,self.role_inference_module)
        self.request_processing_module:AbstractRequestProcessingModule = SimpleRequestProcessingModule(self.config,self.role_estimation_model,self.strategy_module)
        self.question_processing_module:AbstractQuestionProcessingModule = QuestionProcessingModule(self.config,self.role_inference_module,self.strategy_module)
        self.influence_consideration_module:AbstractInfluenceConsiderationModule = InfluenceConsiderationModule(self.config,self.request_processing_module,self.question_processing_module)
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

    def talk(self) -> str:
        strategy_plan = self.strategy_module.talk(self.game_info,self.game_setting)
        influenced,influenced_plan = self.influence_consideration_module.check_influence(self.game_info,self.game_setting)
        executed_plan:OneStepPlan = None
        if influenced:
            #他者影響モジュールのplanを採用
            executed_plan = influenced_plan
        else:
            #戦略立案モジュールのplanを採用
            executed_plan = strategy_plan
        text = executed_plan.action
        rich_text = self.speaker_module.enhance_speech(text)
        self.strategy_module.update_history(self.game_info,self.game_setting,executed_plan)
        return rich_text

    def vote(self) -> Agent:
        plan = self.strategy_module.vote(self.game_info,self.game_setting)
        self.strategy_module.update_history(self.game_info,self.game_setting,plan)
        return plan.action

    def attack(self) -> Agent:
        plan = self.strategy_module.attack(self.game_info,self.game_setting)
        self.strategy_module.update_history(self.game_info,self.game_setting,plan)
        return plan.action

    def divine(self) -> Agent:
        plan = self.strategy_module.divine(self.game_info,self.game_setting)
        self.strategy_module.update_history(self.game_info,self.game_setting,plan)
        return plan.action
    
    def guard(self) -> Agent:
        plan = self.strategy_module.guard(self.game_info,self.game_setting)
        self.strategy_module.update_history(self.game_info,self.game_setting,plan)
        return plan.action

    def whisper(self) -> str:
        plan = self.strategy_module.whisper(self.game_info,self.game_setting)
        text = plan.action
        rich_text = self.speaker_module.enhance_speech(text)
        self.strategy_module.update_history(self.game_info,self.game_setting,plan)
        return rich_text

    def finish(self) -> None:
        pass
    
# run
if __name__ == '__main__':
    # read args
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-p', type=int, action='store', dest='port')
    parser.add_argument('-h', type=str, action='store', dest='hostname')
    parser.add_argument('-r', type=str, action='store', dest='role', default='none')
    parser.add_argument('-n', type=str, action='store', dest='name', default='k2b_ara')
    input_args = parser.parse_args()
    
    # config
    config_ini = load_default_config()

    agent: AbstractPlayer = AttentionReasoningAgent(config_ini)
    
    client = TcpipClient(agent, input_args.name, input_args.hostname, input_args.port, input_args.role, socket_timeout=1200)
    client.connect()