from aiwolfpy.player import BasePlayer
import aiwolfpy.templatetalkfactory as ttf
import aiwolfpy.templatewhisperfactory as twf



class SimplePlayer(BasePlayer):
    
    
    def __init__(self, game_info, game_setting):
        self.agentIdx = game_info['agent']
    
    def talk(self, talk_history, whisper_history):
        return ttf.over()
    
    def whisper(self, talk_history, whisper_history):
        return twf.over()

