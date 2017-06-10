from __future__ import print_function, division 
import pandas as pd

class PandasParser(object):
    
    def __init__(self):
        pass        
        
    # pandas
    def initialize(self, game_info, game_setting):
        # me
        self.agentIdx = game_info['agent']
        self.myRole =  game_info["roleMap"][str(self.agentIdx)]
        # ROLEMAP on INITIAL
        self.gameDataFrame = pd.DataFrame({
                'agent': [int(k) for k in game_info["roleMap"].keys()], 
                'text': ['COMINGOUT Agent[' + "{0:02d}".format(int(k)) + '] ' + game_info["roleMap"][k] for k in game_info["roleMap"].keys()], 
                'day': game_info["day"], 
                'turn': 0, 
                'idx': [int(k) for k in game_info["roleMap"].keys()], 
                'type': 'initialize'
    
            }).sort_values('idx')
        self.gameDataFrame[['agent', 'day', 'turn', 'idx']] = self.gameDataFrame[['agent', 'day', 'turn', 'idx']].astype(int)
        self.gameDataFrame = self.gameDataFrame[['day', 'type', 'idx', 'turn', 'agent', 'text']]
        
    def update(self, game_info, talk_history, whisper_history, request):
        # talk, whisper
        if len(talk_history) > 0:
            temp_df = pd.DataFrame(talk_history)
            temp_df['type'] = 'talk'
            # ignore after death
            if self.agentIdx in temp_df['agent'].values:
                self.gameDataFrame = self.gameDataFrame.append(temp_df).drop_duplicates().reset_index(drop=True)
        if len(whisper_history) > 0:
            temp_df = pd.DataFrame(whisper_history)
            temp_df['type'] = 'whisper'
            # ignore after death
            if self.agentIdx in temp_df['agent'].values:
                self.gameDataFrame = self.gameDataFrame.append(temp_df).drop_duplicates().reset_index(drop=True)
        
        if 'whisperList' in game_info.keys():
            if len(game_info['whisperList']) > 0:
                temp_df = pd.DataFrame(game_info['whisperList'])
                temp_df['type'] = 'whisper'
                self.gameDataFrame = self.gameDataFrame.append(temp_df).drop_duplicates().reset_index(drop=True)
                self.gameDataFrame[['agent', 'day', 'turn', 'idx']] = self.gameDataFrame[['agent', 'day', 'turn', 'idx']].astype(int)
                self.gameDataFrame = self.gameDataFrame[['day', 'type', 'idx', 'turn', 'agent', 'text']]
    
        if request == 'DAILY_INITIALIZE':
            # VOTE
            if len(game_info['voteList']) > 0:
                # valid vote
                vote_df_ = pd.DataFrame(game_info['voteList'])
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': vote_df_['target'], 
                        'text': ['VOTE Agent[' + "{0:02d}".format(k) + '] ' for k in vote_df_['target']], 
                        'day': vote_df_['day'], 
                        'turn': 0, 
                        'idx': vote_df_['agent'], 
                        'type': 'vote' 
                    })).drop_duplicates().reset_index(drop=True)
            # EXECUTE
            if game_info['executedAgent'] != -1:
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': game_info['executedAgent'],
                        'text': 'Over', 
                        'day': game_info['day'] - 1, 
                        'turn': 0, 
                        'idx': 0, 
                        'type': 'execute' 
                    }, index=[0])).drop_duplicates().reset_index(drop=True)
            # IDENTIFY
            if game_info['mediumResult'] is not None:
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': game_info['executedAgent'], 
                        'text': 'IDENTIFIED Agent[' + "{0:02d}".format(game_info['mediumResult']['target']) + '] ' + game_info['mediumResult']['result'], 
                        'day': game_info['mediumResult']['day'], 
                        'turn': 0, 
                        'idx': game_info['mediumResult']['agent'], 
                        'type': 'identify'
                    }, index=[0])).drop_duplicates().reset_index(drop=True)
            # DIVINE
            if game_info['divineResult'] is not None:
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': game_info['divineResult']['target'], 
                        'text': 'DIVINED Agent[' + "{0:02d}".format(game_info['divineResult']['target']) + '] ' + game_info['divineResult']['result'], 
                        'day': game_info['divineResult']['day'] - 1, 
                        'turn': 0, 
                        'idx': game_info['divineResult']['agent'], 
                        'type': 'divine'
                    }, index=[0])).drop_duplicates().reset_index(drop=True)
            # GUARD
            if game_info['guardedAgent'] != -1:
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': game_info['guardedAgent'], 
                        'text': 'GUARDED Agent[' + "{0:02d}".format(game_info['guardedAgent']) + ']', 
                        'day': game_info['day'] - 1, 
                        'turn': 0, 
                        'idx': self.agentIdx, 
                        'type': 'guard'
                    }, index=[0])).drop_duplicates().reset_index(drop=True)
            # ATTACK_VOTE
            if len(game_info['attackVoteList']) > 0:
                # valid attack_vote
                attack_df_ = pd.DataFrame(game_info['attackVoteList'])
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': attack_df_['target'], 
                        'text': ['ATTACK Agent[' + "{0:02d}".format(k) + '] ' for k in attack_df_['target']], 
                        'day': attack_df_['day'], 
                        'turn': 0, 
                        'idx': attack_df_['agent'], 
                        'type': 'attack_vote' 
                    })).drop_duplicates().reset_index(drop=True)
            # ATTACK
            if game_info['attackedAgent'] != -1:
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': game_info['attackedAgent'], 
                        'text': 'ATTACK Agent[' + "{0:02d}".format(game_info['attackedAgent']) + ']', 
                        'day': game_info['day'] - 1, 
                        'turn': 0, 
                        'idx': 0, 
                        'type': 'attack'
                    }, index=[0])).drop_duplicates().reset_index(drop=True)
            # DEAD
            if len(game_info['lastDeadAgentList']) > 0:
                self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': game_info['lastDeadAgentList'], 
                        'text': 'Over', 
                        'day': game_info['day'], 
                        'turn': 0, 
                        'idx': list(range(len(game_info['lastDeadAgentList']))), 
                        'type': 'dead' 
                    })).drop_duplicates().reset_index(drop=True)
        # VOTE/EXECUTE before action
        if request in ['DIVINE', 'ATTACK', 'GUARD', 'WHISPER']:
            # VOTE
            if 'latestVoteList' in game_info.keys():
                if len(game_info['latestVoteList']) > 0:
                    # valid vote
                    vote_df_ = pd.DataFrame(game_info['latestVoteList'])
                    self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': vote_df_['target'], 
                        'text': ['VOTE Agent[' + "{0:02d}".format(k) + '] ' for k in vote_df_['target']], 
                        'day': vote_df_['day'], 
                        'turn': 0, 
                        'idx': vote_df_['agent'], 
                        'type': 'vote' 
                    })).drop_duplicates().reset_index(drop=True)
            # EXECUTE
            if 'latestExecutedAgent' in game_info.keys():
                if game_info['latestExecutedAgent'] != -1:
                    self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                            'agent': game_info['latestExecutedAgent'], 
                            'text': 'Over', 
                            'day': game_info['day'], 
                            'turn': 0, 
                            'idx': 0, 
                            'type': 'execute' 
                        }, index=[0])).drop_duplicates().reset_index(drop=True)
        # REVOTE
        if request == 'VOTE':
            # VOTE
            if 'latestVoteList' in game_info.keys():
                if len(game_info['latestVoteList']) > 0:
                    # 2nd vote requested
                    vote_df_ = pd.DataFrame(game_info['latestVoteList'])
                    self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                        'agent': vote_df_['target'], 
                        'text': ['VOTE Agent[' + "{0:02d}".format(k) + '] ' for k in vote_df_['target']], 
                        'day': vote_df_['day'], 
                        'turn': -1, 
                        'idx': vote_df_['agent'], 
                        'type': 'vote' 
                    })).drop_duplicates().reset_index(drop=True)
        # REATTACKVOTE
        if request == 'ATTACK':
            if 'latestAttackVoteList' in game_info.keys():
                if len(game_info['latestAttackVoteList']) > 0:
                    # 2nd attack_vote requested
                    attack_df_ = pd.DataFrame(game_info['latestAttackVoteList'])
                    self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                            'agent': attack_df_['target'], 
                            'text': ['ATTACK Agent[' + "{0:02d}".format(k) + '] ' for k in attack_df_['target']], 
                            'day': attack_df_['day'], 
                            'turn': -1, 
                            'idx': attack_df_['agent'], 
                            'type': 'attack_vote' 
                        })).drop_duplicates().reset_index(drop=True)
        # FINISH
        if request == 'FINISH':
            self.gameDataFrame = self.gameDataFrame.append(pd.DataFrame({
                    'agent': [int(k) for k in game_info["roleMap"].keys()], 
                    'text': ['COMINGOUT Agent[' + "{0:02d}".format(int(k)) + '] ' + game_info["roleMap"][k] for k in game_info["roleMap"].keys()], 
                    'day': game_info["day"], 
                    'turn': 0, 
                    'idx': [int(k) for k in game_info["roleMap"].keys()], 
                    'type': 'finish'
        
                }).sort_values('idx')).drop_duplicates().reset_index(drop=True)
        self.gameDataFrame[['agent', 'day', 'turn', 'idx']] = self.gameDataFrame[['agent', 'day', 'turn', 'idx']].astype(int)
        self.gameDataFrame = self.gameDataFrame[['day', 'type', 'idx', 'turn', 'agent', 'text']]

