
class BasePlayer(object):
    
    
    def __init__(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
    
    def update(self, game_info, talk_history):
        return None
    
    def dayStart(self):
        return None
    
    def finish(self):
        return None
    
    def vote(self):
        return self.agentIdx
    
    def attack(self):
        return self.agentIdx
    
    def guard(self):
        return self.agentIdx
    
    def divine(self):
        return self.agentIdx
    
    def talk(self):
        return 'Over'
    
    def whisper(self):
        return 'Over'

