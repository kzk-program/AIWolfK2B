import unittest
from aiwolfpy.protocol.contents import *


class ContentFactory(object):
    """Factory class for content
    Example c = ContentFactory.estimate(3, "SEER")
    c.get_text() returns "ESTIMATE Agent[03] SEER"
    """
    # Singleton
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    # 2.1
    @classmethod
    def estimate(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, verb, target, role = 'UNSPEC', 'ESTIMATE', args[0], args[1]
        else:
            subject, verb, target, role = args[0], 'ESTIMATE', args[1], args[2]

        return SVTRContent(subject, verb, target, role)

    @classmethod
    def comingout(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, verb, target, role = 'UNSPEC', 'COMINGOUT', args[0], args[1]
        else:
            subject, verb, target, role = args[0], 'COMINGOUT', args[1], args[2]

        return SVTRContent(subject, verb, target, role)

    # 2.2
    @classmethod
    def divination(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'DIVINATION', args[0]
        else:
            subject, verb, target = args[0], 'DIVINATION', args[1]

        return SVTContent(subject, verb, target)

    @classmethod
    def guard(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'GUARD', args[0]
        else:
            subject, verb, target = args[0], 'GUARD', args[1]

        return SVTContent(subject, verb, target)

    @classmethod
    def vote(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'VOTE', args[0]
        else:
            subject, verb, target = args[0], 'VOTE', args[1]

        return SVTContent(subject, verb, target)

    @classmethod
    def attack(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'ATTACK', args[0]
        else:
            subject, verb, target = args[0], 'ATTACK', args[1]

        return SVTContent(subject, verb, target)

    # 2.3
    @classmethod
    def divined(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, verb, target, species = 'UNSPEC', 'DIVINED', args[0], args[1]
        else:
            subject, verb, target, species = args[0], 'DIVINED', args[1], args[2]

        return SVTSContent(subject, verb, target, species)

    @classmethod
    def identified(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, verb, target, species = 'UNSPEC', 'IDENTIFIED', args[0], args[1]
        else:
            subject, verb, target, species = args[0], 'IDENTIFIED', args[1], args[2]

        return SVTSContent(subject, verb, target, species)

    @classmethod
    def guarded(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'GUARDED', args[0]
        else:
            subject, verb, target = args[0], 'GUARDED', args[1]

        return SVTContent(subject, verb, target)

    @classmethod
    def voted(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'VOTED', args[0]
        else:
            subject, verb, target = args[0], 'VOTED', args[1]

        return SVTContent(subject, verb, target)

    @classmethod
    def attacked(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, target = 'UNSPEC', 'ATTACKED', args[0]
        else:
            subject, verb, target = args[0], 'ATTACKED', args[1]

        return SVTContent(subject, verb, target)

    @classmethod
    def skip(cls, *args):
        assert len(args) == 0 or len(args) == 1
        if len(args) == 0:
            subject, verb = 'UNSPEC', 'SKIP'
        else:
            subject, verb = args[0], 'SKIP'

        return ControlContent(subject, verb)

    @classmethod
    def over(cls, *args):
        assert len(args) == 0 or len(args) == 1
        if len(args) == 0:
            subject, verb = 'UNSPEC', 'OVER'
        else:
            subject, verb = args[0], 'OVER'

        return ControlContent(subject, verb)

    # 3.1
    @classmethod
    def request(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, operator, target, content = 'UNSPEC', "REQUEST", args[0], args[1]
        else:
            subject, operator, target, content = args[0], "REQUEST", args[1], args[2]

        return SOTSContent(subject, operator, target, content)

    @classmethod
    def inquire(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, operator, target, content = 'UNSPEC', "INQUIRE", args[0], args[1]
        else:
            subject, operator, target, content = args[0], "INQUIRE", args[1], args[2]

        return SOTSContent(subject, operator, target, content)

    # 3.2
    @classmethod
    def because(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, operator, content_list = 'UNSPEC', "BECAUSE", [args[0], args[1]]
        else:
            subject, operator, content_list = args[0], "BECAUSE", [args[1], args[2]]

        return SOS2Content(subject, operator, content_list)

    # 3.3
    @classmethod
    def day(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, operator, day, content = 'UNSPEC', "DAY", args[0], args[1]
        else:
            subject, operator, day, content = args[0], "DAY", args[1], args[2]

        return DayContent(subject, operator, day, content)

    # 3.4
    @classmethod
    def not_(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, operator, content_list = 'UNSPEC', "NOT", [args[0]]
        else:
            subject, operator, content_list = args[0], "NOT", [args[1]]

        return SOS1Content(subject, operator, content_list)

    @classmethod
    def and_(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, operator, content_list = 'UNSPEC', "AND", args[0]
        else:
            subject, operator, content_list = args[0], "AND", args[1]

        return SOSSContent(subject, operator, content_list)

    @classmethod
    def or_(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, operator, content_list = 'UNSPEC', "OR", args[0]
        else:
            subject, operator, content_list = args[0], "OR", args[1]

        return SOSSContent(subject, operator, content_list)

    @classmethod
    def xor_(cls, *args):
        assert len(args) == 2 or len(args) == 3
        if len(args) == 2:
            subject, operator, content_list = 'UNSPEC', "XOR", [args[0], args[1]]
        else:
            subject, operator, content_list = args[0], "XOR", [args[1], args[2]]

        return SOS2Content(subject, operator, content_list)


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()