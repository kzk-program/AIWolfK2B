
def talk_check(talk):
    """check talk and return talk if OK, 
    else return Over
    for 15 agents only, agree/disagree not implemented
    """
    content = talk.split(" ")
    namelist = ['Agent[01]', 'Agent[02]', 'Agent[03]', 'Agent[04]', 'Agent[05]',
                'Agent[06]', 'Agent[07]', 'Agent[08]', 'Agent[09]', 'Agent[10]',
                'Agent[11]', 'Agent[12]', 'Agent[13]', 'Agent[14]', 'Agent[15]']
    rolelist = ['VILLAGER', 'SEER', 'MEDIUM', 'BODYGUARD', 'POSSESSED', 'WEREWOLF']
    racelist = ['HUMAN', 'WEREWOLF']
    # VOTE
    if content[0] == 'VOTE':
        if len(content) == 2:
            if content[1] in namelist:
                return talk
            else:
                print('Invalid talk '+talk+' returned Over')
                return 'Over'
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # COMINGOUT
    elif content[0] == 'COMINGOUT':
        if len(content) == 3:
            if content[1] in namelist and content[2] in rolelist:
                return talk
            else:
                print('Invalid talk '+talk+' returned Over')
                return 'Over'
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # ESTIMATE
    elif content[0] == 'ESTIMATE':
        if len(content) == 3:
            if content[1] in namelist and content[2] in rolelist:
                return talk
            else:
                print('Invalid talk '+talk+' returned Over')
                return 'Over'
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # DIVINED
    elif content[0] == 'DIVINED':
        if len(content) == 3:
            if content[1] in namelist and content[2] in racelist:
                return talk
            else:
                print('Invalid talk '+talk+' returned Over')
                return 'Over'
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # INQUESTED
    elif content[0] == 'INQUESTED':
        if len(content) == 3:
            if content[1] in namelist and content[2] in racelist:
                return talk
            else:
                print('Invalid talk '+talk+' returned Over')
                return 'Over'
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # GUARDED
    elif content[0] == 'GUARDED':
        if len(content) == 2:
            if content[1] in namelist:
                return talk
            else:
                print('Invalid talk '+talk+' returned Over')
                return 'Over'
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # SKIP
    elif content[0] == 'Skip':
        if len(content) == 1:
            return talk
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    # OVER
    elif content[0] == 'Over':
        if len(content) == 1:
            return talk
        else:
            print('Invalid talk '+talk+' returned Over')
            return 'Over'
    else:
        print('Invalid talk '+talk+' returned Over')
        return 'Over'

def whisper_check(whisper):
    """check whisper and return whisper if OK,
    else return Over
    for 15 agents only, agree/disagree not implemented
    """
    content = whisper.split(" ")
    namelist = ['Agent[01]', 'Agent[02]', 'Agent[03]', 'Agent[04]', 'Agent[05]',
                'Agent[06]', 'Agent[07]', 'Agent[08]', 'Agent[09]', 'Agent[10]',
                'Agent[11]', 'Agent[12]', 'Agent[13]', 'Agent[14]', 'Agent[15]']
    rolelist = ['VILLAGER', 'SEER', 'MEDIUM', 'BODYGUARD', 'POSSESSED', 'WEREWOLF']
    racelist = ['HUMAN', 'WEREWOLF']
    # VOTE
    if content[0] == 'VOTE':
        if len(content) == 2:
            if content[1] in namelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # ATTACK
    if content[0] == 'ATTACK':
        if len(content) == 2:
            if content[1] in namelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # COMINGOUT
    elif content[0] == 'COMINGOUT':
        if len(content) == 3:
            if content[1] in namelist and content[2] in rolelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # ESTIMATE
    elif content[0] == 'ESTIMATE':
        if len(content) == 3:
            if content[1] in namelist and content[2] in rolelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # DIVINED
    elif content[0] == 'DIVINED':
        if len(content) == 3:
            if content[1] in namelist and content[2] in racelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # INQUESTED
    elif content[0] == 'INQUESTED':
        if len(content) == 3:
            if content[1] in namelist and content[2] in racelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # GUARDED
    elif content[0] == 'GUARDED':
        if len(content) == 2:
            if content[1] in namelist:
                return whisper
            else:
                print('Invalid whisper '+whisper+' returned Over')
                return 'Over'
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # SKIP
    elif content[0] == 'Skip':
        if len(content) == 1:
            return whisper
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    # OVER
    elif content[0] == 'Over':
        if len(content) == 1:
            return whisper
        else:
            print('Invalid whisper '+whisper+' returned Over')
            return 'Over'
    else:
        print('Invalid whisper '+whisper+' returned Over')
        return 'Over'