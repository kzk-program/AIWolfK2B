# -*- coding: utf-8 -*-
"""
TemplateWhisperFactory

@author: KeiHarada
Date:2016/05/03
"""

def attack(target):
    return 'ATTACK Agent[' + "{0:02d}".format(target) + ']'


def estimate(target, role):
    return 'ESTIMATE Agent[' + "{0:02d}".format(target) + '] ' + role


def comingout(target, role):
    return 'COMINGOUT Agent[' + "{0:02d}".format(target) + '] ' + role


def divined(target, species):
    return 'DIVINED Agent[' + "{0:02d}".format(target) + '] ' + species


def identified(target, species):
    return 'IDENTIFIED Agent[' + "{0:02d}".format(target) + '] ' + species


def guarded(target):
    return 'GUARDED Agent[' + "{0:02d}".format(target) + ']'


def vote(target):
    return 'VOTE Agent[' + "{0:02d}".format(target) + ']'


def agree(talktype, day, id):
    return 'AGREE '+ talktype + ' day' + str(day) + ' ID:' + str(id)


def disagree(talktype, day, id):
    return 'DISAGREE '+ talktype + ' day' + str(day) + ' ID:' + str(id)


def skip():
    return 'Skip'


def over():
    return 'Over'



