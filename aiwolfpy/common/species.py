class Species(object):

    # Singleton
    _instance = None

    human = 'HUMAN'
    werewolf = 'WEREWOLF'
    any = 'ANY'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance


if __name__ == '__main__':
    species = Species()
    assert species.human == 'HUMAN'
    assert species.werewolf == 'WEREWOLF'
    assert species.any == 'ANY'
    print("OK")
