import unittest
import aiwolfpy
from aiwolfpy import agent as ag


cf = aiwolfpy.ContentFactory()
rl = aiwolfpy.Role()
sp = aiwolfpy.Species()


# unit test
class MyTestCase(unittest.TestCase):

    def test_case1(self):
        self.assertEqual(
            'ESTIMATE Agent[10] BODYGUARD',
            cf.estimate(ag(10), rl.bodyguard).get_text()
        )

    def test_estimate(self):
        self.assertEqual(cf.estimate(10, 'BODYGUARD').get_text(), 'ESTIMATE Agent[10] BODYGUARD')
        self.assertEqual(
            cf.estimate('Agent[13]', 'Agent[03]', 'MEDIUM').get_text(),
            'Agent[13] ESTIMATE Agent[03] MEDIUM'
        )

    def test_comingout(self):
        self.assertEqual(cf.comingout(1, 'SEER').get_text(), 'COMINGOUT Agent[01] SEER')
        self.assertEqual(
            cf.comingout('Agent[03]', 'Agent[03]', 'SEER').get_text(),
            'Agent[03] COMINGOUT Agent[03] SEER'
        )

    def test_divination(self):
        self.assertEqual(cf.divination(5).get_text(), 'DIVINATION Agent[05]')
        self.assertEqual(cf.divination('13', 'Agent[12]').get_text(),'Agent[13] DIVINATION Agent[12]')

    def test_guard(self):
        self.assertEqual(cf.guard('Agent[07]').get_text(), 'GUARD Agent[07]')
        self.assertEqual(cf.guard(11, 5).get_text(),'Agent[11] GUARD Agent[05]')

    def test_vote(self):
        self.assertEqual(cf.vote('Agent[07]').get_text(), 'VOTE Agent[07]')
        self.assertEqual(cf.vote(10, 1).get_text(), 'Agent[10] VOTE Agent[01]')

    def test_attack(self):
        self.assertEqual(cf.attack('Agent[17]').get_text(), 'ATTACK Agent[17]')
        self.assertEqual(cf.attack('10', '0').get_text(), 'Agent[10] ATTACK Agent[00]')

    def test_divined(self):
        self.assertEqual(cf.divined(1, 'HUMAN').get_text(), 'DIVINED Agent[01] HUMAN')
        self.assertEqual(cf.divined(1, 2, 'WEREWOLF').get_text(),'Agent[01] DIVINED Agent[02] WEREWOLF')

    def test_identified(self):
        self.assertEqual(cf.identified('Agent[01]', 'HUMAN').get_text(), 'IDENTIFIED Agent[01] HUMAN')
        self.assertEqual(cf.identified(7, '12', 'WEREWOLF').get_text(), 'Agent[07] IDENTIFIED Agent[12] WEREWOLF')

    def test_guarded(self):
        self.assertEqual(cf.guarded('Agent[11]').get_text(), 'GUARDED Agent[11]')
        self.assertEqual(cf.guarded(97, '32').get_text(), 'Agent[97] GUARDED Agent[32]')

    def test_voted(self):
        self.assertEqual(cf.voted('10').get_text(), 'VOTED Agent[10]')
        self.assertEqual(cf.voted('Agent[02]', 3).get_text(), 'Agent[02] VOTED Agent[03]')

    def test_attacked(self):
        self.assertEqual(cf.attacked(2).get_text(), 'ATTACKED Agent[02]')
        self.assertEqual(cf.attacked('7', 'Agent[06]').get_text(), 'Agent[07] ATTACKED Agent[06]')

    def test_agree(self):
        self.assertEqual(cf.agree((2, 4)).get_text(), 'AGREE day2 ID:4')
        self.assertEqual(cf.agree('7', (0, 4)).get_text(), 'Agent[07] AGREE day0 ID:4')

    def test_skip(self):
        self.assertEqual(cf.skip('Agent[10]').get_text(), 'Skip')
        self.assertEqual(cf.skip().get_text(), 'Skip')

    def test_over(self):
        self.assertEqual(cf.over(9).get_text(), 'Over')
        self.assertEqual(str(cf.over()), 'Over')

    def test_request(self):
        self.assertEqual(
            cf.request(9, cf.estimate(2, "POSSESSED")).get_text(),
            'REQUEST Agent[09] (ESTIMATE Agent[02] POSSESSED)'
        )
        self.assertEqual(
            str(cf.request(1, 'ANY', cf.vote('ANY', 'Agent[09]'))),
            'Agent[01] REQUEST ANY (ANY VOTE Agent[09])'
        )

    def test_inquire(self):
        self.assertEqual(
            cf.inquire(9, cf.comingout(9, "ANY")).get_text(),
            'INQUIRE Agent[09] (COMINGOUT Agent[09] ANY)'
        )
        self.assertEqual(
            str(cf.inquire('Agent[02]', 'Agent[01]', cf.estimate('Agent[01]', 'Agent[02]', 'WEREWOLF'))),
            'Agent[02] INQUIRE Agent[01] (Agent[01] ESTIMATE Agent[02] WEREWOLF)'
        )

    def test_because(self):
        self.assertEqual(
            cf.because(cf.voted(1, 4), cf.estimate(1, "WEREWOLF")).get_text(),
            'BECAUSE (Agent[01] VOTED Agent[04]) (ESTIMATE Agent[01] WEREWOLF)'
        )
        self.assertEqual(
            str(cf.because(cf.divined(4, 24, 'WEREWOLF'), cf.request('ANY', cf.vote('Agent[24]')))),
            'BECAUSE (Agent[04] DIVINED Agent[24] WEREWOLF) (REQUEST ANY (VOTE Agent[24]))'
        )


if __name__ == '__main__':
    unittest.main()
