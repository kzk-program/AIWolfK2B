from abc import ABCMeta, abstractmethod


class Content(metaclass=ABCMeta):
    """Abstract content class"""

    def __init__(
            self, subject='UNSPEC', target=None, role=None, species=None, verb=None, talk_number=(None, None),
            operator=None, day=None, children=[]
    ):
        if str(subject).isdigit():
            self.subject = 'Agent[%s]' % "{0:02d}".format(int(subject))
        else:
            self.subject = subject
        if str(target).isdigit():
            self.target = 'Agent[%s]' % "{0:02d}".format(int(target))
        else:
            self.target = target
        self.role = role
        self.species = species
        self.verb = verb
        self.talk_number = talk_number
        self.day = day
        self.operator = operator
        if operator is None:
            self.is_operator = False
        else:
            self.is_operator = True
        self.is_control = False
        self.children = children

    @abstractmethod
    def get_text(self):
        return ''

    def __str__(self):
        return self.get_text()

    def get_children(self):
        return self.children
