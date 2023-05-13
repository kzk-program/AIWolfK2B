#三層構造モデルにおけるlistenerの抽象クラス
from abc import ABCMeta, abstractmethod
from typing import List

class JPToProtocolConverter(metaclass=ABCMeta):
    @abstractmethod
    def convert(self, text_list : List[str]) -> List[str]:
        """
        自然言語をプロトコルに変換する関数
        
        Parameters
        ----------
        text_list : List[str]
            変換する自然言語のリスト。各要素は1文に相当。各要素は独立していて互いの文脈は考慮しない

        Returns
        -------
        List[str]
            得られたプロトコルのリスト。各要素は1プロトコルに相当。各要素は独立していて互いの文脈は考慮しない
        """
        pass