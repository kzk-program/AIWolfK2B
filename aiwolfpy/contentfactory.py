import unittest
from abc import ABCMeta, abstractmethod


class Content(metaclass=ABCMeta):
    """Abstract content class : ver. 2019"""

    def __init__(
            self, subject='UNSPEC', target=None, role=None, species=None, verb=None, talk_number=(None, None),
            operator=None, day=None, children=[]
    ):
        # subject
        if str(subject) in ['UNSPEC', 'ANY']:
            self.subject = subject
        elif str(subject).isdigit():
            assert 0 <= int(subject) <= 99
            self.subject = 'Agent[%s]' % "{0:02d}".format(int(subject))
        else:
            assert str(subject)[6:8].isdigit()
            assert str(subject) == 'Agent[%s]' % str(subject)[6:8]
            self.subject = subject

        # target
        if target is None:
            self.target = None
        elif str(target) in ['ANY']:
            self.target = target
        elif str(target).isdigit():
            assert 0 <= int(target) <= 99
            self.target = 'Agent[%s]' % "{0:02d}".format(int(target))
        else:
            assert str(target)[6:8].isdigit()
            assert str(target) == 'Agent[%s]' % str(target)[6:8]
            self.target = target

        # role
        # add FOX and FREEMASON if necessary
        if role is None:
            self.role = None
        else:
            assert str(role) in ['VILLAGER', 'SEER', 'MEDIUM', 'BODYGUARD', 'WEREWOLF', 'POSSESSED', 'ANY']
            self.role = role

        # species
        # add something if necessary
        if species is None:
            self.species = None
        else:
            assert str(species) in ['HUMAN', 'WEREWOLF', 'ANY']
            self.species = species

        # verb
        if verb is None:
            self.verb = None
        else:
            assert str(verb) in [
                'ESTIMATE', 'COMINGOUT', 'DIVINATION', 'GUARD', 'VOTE',
                'ATTACK', 'DIVINED', 'IDENTIFIED', 'GUARDED', 'VOTED',
                'ATTACKED', 'AGREE', 'DISAGREE', 'Skip', 'Over'
            ]
            self.verb = verb

        # TODO
        # talk number
        assert len(talk_number) == 2
        if talk_number[0] is None:
            self.talk_number = (None, None)
        else:
            assert str(talk_number[0]).isdigit()
            assert str(talk_number[1]).isdigit()
            self.talk_number = talk_number

        # day
        self.day = day

        # operator
        if operator is None:
            self.operator = None
        else:
            assert str(operator) in [
                'REQUEST', 'INQUIRE', 'BECAUSE', 'DAY',
                'NOT', 'AND', 'OR', 'XOR'
            ]
            self.operator = str(operator)
        if operator is None:
            self.is_operator = False
        else:
            self.is_operator = True
        self.is_control = False
        self.children = children

    @abstractmethod
    def _get_text(self):
        return ''

    def get_text(self):
        res = self._get_text()
        if str(self.subject) == 'UNSPEC' or res == 'Skip' or res == 'Over':
            return res
        else:
            return str(self.subject) + ' ' + res

    def __str__(self):
        return self.get_text()

    def get_children(self):
        return self.children


# children of Content
class SVTRContent(Content):
    """Content class in the form [subject] [verb] [target] [role]
    ESTIMATE and COMINGOUT
    """

    def __init__(self, subject, verb, target, role):
        super().__init__(subject=subject, verb=verb, target=target, role=role)

    def _get_text(self):
        return '%s %s %s' % (str(self.verb), str(self.target), str(self.role))


class SVTContent(Content):
    """Content class in the form [subject] [verb] [target]
    DIVINATION, GUARD, VOTE, ATTACK, GUARDED, VOTED and ATTACKED
    """

    def __init__(self, subject, verb, target):
        super().__init__(subject=subject, verb=verb, target=target)

    def _get_text(self):
        return '%s %s' % (str(self.verb), str(self.target))


class SVTSContent(Content):
    """Content class in the form [subject] [verb] [target] [species]
    DIVINED and IDENTIFIED
    """

    def __init__(self, subject, verb, target, species):
        super().__init__(subject=subject, verb=verb, target=target, species=species)

    def _get_text(self):
        return '%s %s %s' % (str(self.verb), str(self.target), str(self.species))


class AgreeContent(Content):
    """Content class in the form [subject] [verb] [talk_number]
    AGREE and DISAGREE
    """

    def __init__(self, subject, verb, talk_number):
        super().__init__(subject=subject, verb=verb, talk_number=talk_number)

    def _get_text(self):
        return '%s day%s ID:%s' % (str(self.verb), str(self.talk_number[0]), str(self.talk_number[1]))


class ControlContent(Content):
    """Content class for Skip and Over"""

    def __init__(self, subject, verb):
        super().__init__(subject=subject, verb=verb)
        self.is_control = True

    def _get_text(self):
        return self.verb


class SOTSContent(Content):
    """Content class in the form [subject] [operator] [target] [sentence]
    REQUEST and INQUIRE
    """

    def __init__(self, subject, operator, target, content):
        super().__init__(subject=subject, operator=operator, target=target, children=[content])

    def _get_text(self):
        return '%s %s (%s)' % (self.operator, self.target, self.get_child().get_text())

    def get_child(self):
        return self.children[0]


class SOS1Content(Content):
    """Content class in the form [subject] [operator] [sentence]
    NOT
    """

    def __init__(self, subject, operator, content_list):
        super().__init__(subject=subject, operator=operator, children=content_list)

    def _get_text(self):
        return '%s ' % self.operator + " ".join(['(%s)' % c.get_text() for c in self.children])

    def get_child(self):
        return self.children[0]


class SOS2Content(Content):
    """Content class in the form [subject] [operator] [sentence_1] [sentence_2]
    BECAUSE, XOR
    """

    def __init__(self, subject, operator, content_list):
        super().__init__(subject=subject, operator=operator, children=content_list)

    def _get_text(self):
        return '%s ' % self.operator + " ".join(['(%s)' % c.get_text() for c in self.children])

    def get_child_1(self):
        return self.children[0]

    def get_child_2(self):
        return self.children[1]


class SOSSContent(Content):
    """Content class in the form [subject] [operator] [sentence_1] [sentence_2]
    AND, OR
    """

    def __init__(self, subject, operator, content_list):
        super().__init__(subject=subject, operator=operator, children=content_list)

    def _get_text(self):
        return '%s ' % self.operator + " ".join(['(%s)' % c.get_text() for c in self.children])


class DayContent(Content):
    """Content class for day"""

    def __init__(self, subject, operator, day, content):
        super().__init__(subject=subject, day=day, operator=operator, children=[content])

    def _get_text(self):
        return '%s %s (%s)' % (self.operator, str(self.day), self.get_child().get_text())

    def get_child(self):
        return self.children[0]


# content factory
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
    def agree(cls, *args):
        assert len(args) == 1 or len(args) == 2
        if len(args) == 1:
            subject, verb, talk_number = 'UNSPEC', 'AGREE', args[0]
        else:
            subject, verb, talk_number = args[0], 'AGREE', args[1]

        return AgreeContent(subject, verb, talk_number)

    @classmethod
    def skip(cls, *args):
        assert len(args) == 0 or len(args) == 1
        if len(args) == 0:
            subject, verb = 'UNSPEC', 'Skip'
        else:
            subject, verb = args[0], 'Skip'

        return ControlContent(subject, verb)

    @classmethod
    def over(cls, *args):
        assert len(args) == 0 or len(args) == 1
        if len(args) == 0:
            subject, verb = 'UNSPEC', 'Over'
        else:
            subject, verb = args[0], 'Over'

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


# unit test
class MyTestCase(unittest.TestCase):

    def test_estimate(self):
        cf = ContentFactory()
        self.assertEqual(cf.estimate(10, 'BODYGUARD').get_text(), 'ESTIMATE Agent[10] BODYGUARD')
        self.assertEqual(
            cf.estimate('Agent[13]', 'Agent[03]', 'MEDIUM').get_text(),
            'Agent[13] ESTIMATE Agent[03] MEDIUM'
        )

    def test_comingout(self):
        cf = ContentFactory()
        self.assertEqual(cf.comingout(1, 'SEER').get_text(), 'COMINGOUT Agent[01] SEER')
        self.assertEqual(
            cf.comingout('Agent[03]', 'Agent[03]', 'SEER').get_text(),
            'Agent[03] COMINGOUT Agent[03] SEER'
        )

    def test_divination(self):
        cf = ContentFactory()
        self.assertEqual(cf.divination(5).get_text(), 'DIVINATION Agent[05]')
        self.assertEqual(cf.divination('13', 'Agent[12]').get_text(),'Agent[13] DIVINATION Agent[12]')

    def test_guard(self):
        cf = ContentFactory()
        self.assertEqual(cf.guard('Agent[07]').get_text(), 'GUARD Agent[07]')
        self.assertEqual(cf.guard(11, 5).get_text(),'Agent[11] GUARD Agent[05]')

    def test_vote(self):
        cf = ContentFactory()
        self.assertEqual(cf.vote('Agent[07]').get_text(), 'VOTE Agent[07]')
        self.assertEqual(cf.vote(10, 1).get_text(), 'Agent[10] VOTE Agent[01]')

    def test_attack(self):
        cf = ContentFactory()
        self.assertEqual(cf.attack('Agent[17]').get_text(), 'ATTACK Agent[17]')
        self.assertEqual(cf.attack('10', '0').get_text(), 'Agent[10] ATTACK Agent[00]')

    def test_divined(self):
        cf = ContentFactory()
        self.assertEqual(cf.divined(1, 'HUMAN').get_text(), 'DIVINED Agent[01] HUMAN')
        self.assertEqual(cf.divined(1, 2, 'WEREWOLF').get_text(),'Agent[01] DIVINED Agent[02] WEREWOLF')

    def test_identified(self):
        cf = ContentFactory()
        self.assertEqual(cf.identified('Agent[01]', 'HUMAN').get_text(), 'IDENTIFIED Agent[01] HUMAN')
        self.assertEqual(cf.identified(7, '12', 'WEREWOLF').get_text(), 'Agent[07] IDENTIFIED Agent[12] WEREWOLF')

    def test_guarded(self):
        cf = ContentFactory()
        self.assertEqual(cf.guarded('Agent[11]').get_text(), 'GUARDED Agent[11]')
        self.assertEqual(cf.guarded(97, '32').get_text(), 'Agent[97] GUARDED Agent[32]')

    def test_voted(self):
        cf = ContentFactory()
        self.assertEqual(cf.voted('10').get_text(), 'VOTED Agent[10]')
        self.assertEqual(cf.voted('Agent[02]', 3).get_text(), 'Agent[02] VOTED Agent[03]')

    def test_attacked(self):
        cf = ContentFactory()
        self.assertEqual(cf.attacked(2).get_text(), 'ATTACKED Agent[02]')
        self.assertEqual(cf.attacked('7', 'Agent[06]').get_text(), 'Agent[07] ATTACKED Agent[06]')

    def test_agree(self):
        cf = ContentFactory()
        self.assertEqual(cf.agree((2, 4)).get_text(), 'AGREE day2 ID:4')
        self.assertEqual(cf.agree('7', (0, 4)).get_text(), 'Agent[07] AGREE day0 ID:4')

    def test_skip(self):
        cf = ContentFactory()
        self.assertEqual(cf.skip('Agent[10]').get_text(), 'Skip')
        self.assertEqual(cf.skip().get_text(), 'Skip')

    def test_over(self):
        cf = ContentFactory()
        self.assertEqual(cf.over(9).get_text(), 'Over')
        self.assertEqual(cf.over().get_text(), 'Over')


if __name__ == '__main__':
    unittest.main()
