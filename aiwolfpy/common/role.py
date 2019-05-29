class Role(object):

    # Singleton
    _instance = None

    villager = 'VILLAGER'
    seer = 'SEER'
    medium = 'MEDIUM'
    bodyguard = 'BODYGUARD'
    werewolf = 'WEREWOLF'
    possessed = 'POSSESSED'
    any = 'ANY'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance


if __name__ == '__main__':
    role = Role()
    assert role.villager == 'VILLAGER'
    assert role.seer == 'SEER'
    assert role.medium == 'MEDIUM'
    assert role.bodyguard == 'BODYGUARD'
    assert role.werewolf == 'WEREWOLF'
    assert role.possessed == 'POSSESSED'
    assert role.any == 'ANY'
    print("OK")
