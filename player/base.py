
class BasePlayer(object):
    
    
    def __init__(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
    
    def dayStart(self, game_info):
        return None
    
    def dayFinish(self, talk_history, whisper_history):
        return None
    
    def finish(self, game_info):
        return None
    
    def vote(self, talk_history, whisper_history):
        return self.agentIdx
    
    def attack(self):
        return self.agentIdx
    
    def guard(self):
        return self.agentIdx
    
    def divine(self):
        return self.agentIdx
    
    def talk(self, talk_history, whisper_history):
        return 'Over'
    
    def whisper(self, talk_history, whisper_history):
        return 'Over'

