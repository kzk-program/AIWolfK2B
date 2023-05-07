from typing import Dict, List, Set, Deque, Tuple
from collections import deque
import re

#LL(1)文法を扱うクラス
class LL1Grammar:
    def __init__(self, non_terminals: Set[str], terminals: Set[str], start_symbol: str, production_rules: Dict[str, List[str]]):
        self.non_terminals = non_terminals
        self.terminals = terminals
        self.start_symbol = start_symbol
        self.production_rules = production_rules
        self.first_sets = self.compute_first_sets()
        self.follow_sets = self.compute_follow_sets()
        self.parse_table = self.construct_parse_table()

    def __repr__(self):
        return f"LL1Grammar(non_terminals={self.non_terminals}, terminals={self.terminals}, start_symbol={self.start_symbol}, production_rules={self.production_rules})"
    
    def add_production_rule(self, non_terminal, production):
        if non_terminal in self.non_terminals:
            self.production_rules[non_terminal].append(production)
        else:
            raise ValueError(f"Non-terminal '{non_terminal}' not found in grammar.")

    def remove_production_rule(self, non_terminal, production):
        if non_terminal in self.non_terminals:
            if production in self.production_rules[non_terminal]:
                self.production_rules[non_terminal].remove(production)
            else:
                raise ValueError(f"Production '{production}' not found for non-terminal '{non_terminal}'.")
        else:
            raise ValueError(f"Non-terminal '{non_terminal}' not found in grammar.")

    def compute_first_sets(self) -> Dict[str, Set[str]]:
        first_sets = {nt: set() for nt in self.non_terminals}
        change = True

        while change:
            change = False
            for nt in self.non_terminals:
                for prod in self.production_rules[nt]:
                    prod_symbols = prod.split()  # Update here
                    if prod_symbols[0] in self.terminals:
                        if prod_symbols[0] not in first_sets[nt]:
                            first_sets[nt].add(prod_symbols[0])
                            change = True
                    else:
                        for symbol in prod_symbols:
                            if symbol in self.terminals:
                                break
                            for first in first_sets[symbol]:
                                if first not in first_sets[nt]:
                                    first_sets[nt].add(first)
                                    change = True
                            if 'ε' not in first_sets[symbol]:
                                break
        return first_sets

    def compute_follow_sets(self) -> Dict[str, Set[str]]:
        follow_sets = {nt: set() for nt in self.non_terminals}
        follow_sets[self.start_symbol].add('$')

        change = True
        while change:
            change = False
            for nt in self.non_terminals:
                for prod in self.production_rules[nt]:
                    prod_symbols = prod.split()  # Update here
                    # A -> αBβ
                    for i, symbol in enumerate(prod_symbols[:-1]):
                        # Bを見つける(symbol = B)
                        if symbol in self.non_terminals:
                            for next_sym in prod_symbols[i + 1:]:
                                # β in Terminal
                                if next_sym in self.terminals:
                                    if next_sym not in follow_sets[symbol]:
                                        follow_sets[symbol].add(next_sym)
                                        change = True
                                    break
                                # β in Non-Terminal
                                else:
                                    for first in self.first_sets[next_sym]:
                                        if first not in follow_sets[symbol] and first != 'ε':
                                            follow_sets[symbol].add(first)
                                            change = True
                                    # εが含まれていない場合、prodによって生じるBのfollowが確定するのでbreak
                                    if 'ε' not in self.first_sets[next_sym]:
                                        break
                            else:# prodの最後までεが含まれていた場合、A(nt)のfollowをB(symbol)に追加
                                for follow in follow_sets[nt]:
                                    if follow not in follow_sets[symbol]:
                                        follow_sets[symbol].add(follow)
                                        change = True
                                        
                    # A -> αBの場合、AのfollowをBに追加
                    if prod_symbols[-1] in self.non_terminals:
                        for follow in follow_sets[nt]:
                            if follow not in follow_sets[prod_symbols[-1]]:
                                follow_sets[prod_symbols[-1]].add(follow)
                                change = True
                        
        return follow_sets

    def construct_parse_table(self) -> Dict[str, Dict[str, str]]:
        parse_table = {nt: {t: '' for t in self.terminals} for nt in self.non_terminals}
        parse_table.update({nt: {t: '' for t in self.terminals} for nt in ['$']})

        # アイディア：A -> BCの場合、Bのfirstをparse_table[A][first(B)] = BCとする。
        #もし、Bのfirstにεが含まれている場合、Cのfirstをparse_table[A][fisrt(C))] = BCとする。
        #さらに、Cのfirstにεが含まれている場合、Aのfollowをparse_table[A][follow(A)] = BCとする。
        for nt, prods in self.production_rules.items():
            for prod in prods:
                prod_symbols = prod.split()
                first_symbols = set()
                for symbol in prod_symbols:
                    # B in Terminal
                    if symbol in self.terminals:
                        first_symbols.add(symbol)
                        break
                    else:
                        first_symbols |= self.first_sets[symbol]
                        if 'ε' not in first_symbols:
                            break
                # εが含まれている場合、parse_table[A][follow(A)] = BCを追加
                if 'ε' in first_symbols:
                    for terminal in self.follow_sets[nt]:
                        if terminal != '$':
                            parse_table[nt][terminal] = prod
                        
                first_symbols -= {'ε'}
                #実際にparse_tableに追加
                for terminal in first_symbols:
                    parse_table[nt][terminal] = prod


        return parse_table
    
    def parse(self, input_str: str) -> Tuple[bool, List[str]]:
        stack:Deque = deque()
        stack.append(self.start_symbol)
        input_symbols = input_str.split() + ['$']
        input_symbols = deque(input_symbols)
        parse_steps = []

        while stack:
            top = stack[-1]
            current_input = input_symbols[0]
            
            if top in self.non_terminals:
                stack.pop()
                if current_input == '$':
                    if "ε" in self.first_sets[top]:
                        continue
                    else:
                        return False, parse_steps
                else:
                    rule = self.parse_table[top][current_input]
                    if rule == "":
                        if "ε" in self.first_sets[top]:
                            continue
                        return False, parse_steps
                    else:
                        prod_symbols = rule.split()
                        stack.extend(reversed(prod_symbols))
            if top in self.terminals:
                if top == current_input:
                    stack.pop()
                    input_symbols.popleft()
                    parse_steps.append(f"Match {top}") 
                elif top == "ε":
                    stack.pop()
                else:
                    return False, parse_steps

        return True, parse_steps
    
    def get_next_terminals(self, input_str: str) -> Set[str]:
        #方針:入力が空になるまで構文解析を行い、入力が空になったときのスタックから、次に来る可能性のある終端記号を取得する
        stack:Deque = deque()
        stack.append(self.start_symbol)
        input_symbols = input_str.split() + ['$']
        input_symbols = deque(input_symbols)

        while stack and input_symbols[0] != '$':
            top = stack[-1]
            current_input = input_symbols[0]
            
            # 非終端記号であれば生成規則を展開
            if top in self.non_terminals:
                stack.pop()
                rule = self.parse_table[top][current_input]
                if rule == "":
                    if "ε" in self.first_sets[top]:
                        continue
                    raise Exception("error: no production rule")
                else:
                    prod_symbols = rule.split()
                    stack.extend(reversed(prod_symbols))
            #終端記号であれば、一致しているかを確認
            if top in self.terminals:
                if top == current_input:
                    stack.pop()
                    input_symbols.popleft() 
                elif top == "ε":
                    stack.pop()
                else:
                    raise Exception("error: no production rule")
                
        next_terminals:Set = set()
        #もしスタックが空でなければ、文が完全に一致していないので、次に来る可能性のある終端記号を取得する
        while stack:
            top = stack[-1]
            stack.pop()
            #取り出した記号が終端記号であれば、次に来る可能性のある終端記号として追加
            if top in self.terminals and top != "ε":
                next_terminals.add(top)
                break
            #取り出した記号が非終端記号であれば、その非終端記号から生成される終端記号を取得する
            if top in self.non_terminals:
                next_terminals |= self.first_sets[top]
                if "ε" not in next_terminals:
                    break
                elif stack: #最後の記号であれば、次に来る記号がないケースもあるので、その場合は空は追加したままにする
                    next_terminals.remove("ε")

        return next_terminals
    
def aiwolf_protocol_grammar():
    """
    sentence ::= Skip | Over | Agent [agent_number] VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY | ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY | VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY 
    VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ::= ESTIMATE TR | COMMINGOUT TR | DIVINATION T | GUARD T | VOTE T | ATTACK T | GUARDED T | VOTED T | ATTACKED T 
            | DIVINED TSp | IDENTIFIED TSp | AGREE talk_number | DISAGREE talk_number | REQUEST TSe | INQUIRE TSe | NOT ( sentence ) 
            | BECAUSE ( S2 | XOR ( S2 | AND ( SS | OR ( SS | DAY number ( sentence )
    TR ::= Agent agent_number role | ANY role 
    T ::= Agent agent_number | ANY
    TSp ::= Agent agent_number species | ANY species 
    TSe ::= Agent agent_number ( sentence ) | ANY ( sentence )
    S2 ::= Skip ) | Over ) | Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( sentence ) | ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( sentence ) | VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( sentence )

    SS ::= Skip ) | Over ) | Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( recsentence | ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( recsentence | VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( recsentence 
    recsentence ::= Skip ) | Over ) | Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence | ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence | VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) rec2sentence 
    rec2sentence ::= Skip ) | Over ) | Agent agent_number  VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence | ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence | VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence | )

    species ::= HUMAN | WEREWOLF | ANY
    role ::= VILLAGER| SEER | MEDIUM | BODYGUARD | WEREWOLF | POSSESSED
    agent_number ::= 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15
    talk_number ::= day number ID number 
    number ::= (0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9) rec_number
    rec_number ::= (0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 ) rec_number | eps

    """
    non_terminals = {"sentence","VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY","TR","T","TSp","TSe","S2","SS",
                    "recsentence","rec2sentence","species","role",
                    "talk_number","agent_number","number","rec_number"}
    terminals = {"Skip", "Over", "Agent","ESTIMATE", "COMMINGOUT", "DIVINATION", "GUARD", "VOTE", 
                    "ATTACK", "GUARDED", "VOTED", "ATTACKED", "DIVINED", "IDENTIFIED","AGREE", "DISAGREE", 
                    "REQUEST", "INQUIRE", "NOT", "BECAUSE", "XOR", "AND", "OR", "DAY",
                    "HUMAN", "WEREWOLF", "ANY", 
                    "VILLAGER", "SEER", "MEDIUM", "BODYGUARD", "POSSESSED", 
                    "day", "ID","(",")", "0","1","2","3","4","5","6","7","8","9",
                    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11","12", "13", "14", "15", "ε"}

    start_symbol = "sentence"
    production_rules = {
        "sentence": ["Skip", "Over", "Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY", "ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY", "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY"],
        "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY": ["ESTIMATE TR", "COMMINGOUT TR", "DIVINATION T", "GUARD T", "VOTE T", "ATTACK T", "GUARDED T", "VOTED T", "ATTACKED T", 
                                            "DIVINED TSp", "IDENTIFIED TSp", "AGREE talk_number", "DISAGREE talk_number", "REQUEST TSe", "INQUIRE TSe", "NOT ( sentence )", 
                                            "BECAUSE ( S2", "XOR ( S2", "AND ( SS", "OR ( SS", "DAY number ( sentence )"],
        "TR": ["Agent agent_number role", "ANY role"],
        "T": ["Agent agent_number", "ANY"],
        "TSp": ["Agent agent_number species", "ANY species"],
        "TSe": ["Agent agent_number ( sentence )", "ANY ( sentence )"],
        "S2" : ["Skip )", "Over )", "Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( sentence )", "ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( sentence )", "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( sentence )"],
        "SS" : ["Skip )", "Over )", "Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( recsentence", "ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( recsentence", "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( recsentence"],
        "recsentence" :["Skip )", "Over )", "Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence", "ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence", "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence"],
        "rec2sentence":["Skip )", "Over )", "Agent agent_number VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence", "ANY VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence", "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY ) ( rec2sentence", ")"],
        "species": ["HUMAN", "WEREWOLF", "ANY"],
        "role":["VILLAGER", "SEER", "MEDIUM", "BODYGUARD", "WEREWOLF", "POSSESSED"],
        "agent_number":["01", "02", "03", "04", "05", "06", "07", "08", "09", "10","11","12", "13", "14", "15"],
        "talk_number":["day number ID number"],
        "number":["0 rec_number ","1 rec_number","2 rec_number","3 rec_number","4 rec_number","5 rec_number","6 rec_number","7 rec_number","8 rec_number","9 rec_number"],
        "rec_number":["0 rec_number","1 rec_number","2 rec_number","3 rec_number","4 rec_number","5 rec_number","6 rec_number","7 rec_number","8 rec_number","9 rec_number","ε"],
    }

    grammar = LL1Grammar(non_terminals, terminals, start_symbol, production_rules)
    # for key, value in grammar.parse_table.items():
    #     print(key, value)
        # #ファイルに書き込み
        # with open('parse_table.txt', 'a') as f:
        #     print(key, value, file=f)
        
    return grammar

    
def test_LL1Grammar1():
    print("case 1")
    grammar = LL1Grammar(
        non_terminals={'E', 'T', 'F', 'E1', 'T1'},
        terminals={'+', '*', '(', ')', 'id', 'ε'},
        start_symbol='E',
        production_rules={
            'E': ['T E1'],
            'E1': ['+ T E1', 'ε'],
            'T': ['F T1'],
            'T1': ['* F T1', 'ε'],
            'F': ['( E )', 'id']
        }
    )
    test_print_LL1Grammer(grammar)
    
    return grammar

def test_LL1Grammar2():
    print("case 2")
    non_terminals = {'S', 'A', 'B'}
    terminals = {'a', 'b', 'c', 'd', 'ε'}
    start_symbol = 'S'
    production_rules = {
        'S': ['A B'],
        'A': ['a A', 'b', 'ε'],
        'B': ['c B', 'd', 'ε']
    }
    grammar = LL1Grammar(non_terminals, terminals, start_symbol, production_rules)
    
    test_print_LL1Grammer(grammar)
    return grammar
    

def test_print_LL1Grammer(grammar:LL1Grammar):
    print(grammar)
    print("first sets:",grammar.first_sets)
    print("follow sets:",grammar.follow_sets)
    for key, value in grammar.parse_table.items():
        print(key, value)

#first_set, follow_set, parse_tableのテスト
def test_LL1Grammars():
    test_LL1Grammar1()
    test_LL1Grammar2()
    
#テスト
def test_parser(grammar:LL1Grammar, input_str: str):
    print("parser test")
    next_terminals = grammar.parse(input_str)
    print(next_terminals)

#パーサーのテスト
def test_grammar_parsers():
    grammar2 = test_LL1Grammar2()
    aiwolf_grammar = aiwolf_protocol_grammar()
    test_parser(grammar2, "a")
    test_parser(grammar2, "a a")
    test_parser(grammar2, "a b")
    test_parser(grammar2, "a a b d c")
    test_parser(grammar2, "a a b c d")

    test_parser(aiwolf_grammar, "Agent 01 ESTIMATE Agent 02 VILLAGER")
    test_parser(aiwolf_grammar, "Agent 02 INQUIRE Agent 01 ( Agent 01 ESTIMATE Agent 02 WEREWOLF ) ")
    test_parser(aiwolf_grammar, "REQUEST ANY ( DISAGREE day 1 ID 1 0 )")

#テスト
def test_get_next_terminals(grammar:LL1Grammar, input_str: str):
    print("next terminals")
    next_terminals = grammar.get_next_terminals(grammar, input_str)
    print(next_terminals)

def test_grammar_get_next_terminals():
    grammar2 = test_LL1Grammar2()
    aiwolf_grammar = aiwolf_protocol_grammar()
    test_get_next_terminals(grammar2, "a")

    test_get_next_terminals(aiwolf_grammar, "Agent 01 ESTIMATE Agent 02") #元々：Agent 01 ESTIMATE Agent 02 VILLAGER
    test_get_next_terminals(aiwolf_grammar, "Agent 02 INQUIRE Agent 01 ( Agent 01 ESTIMATE Agent ") #元々：Agent 02 INQUIRE Agent 01 ( Agent 01 ESTIMATE Agent 02 WEREWOLF )
    test_get_next_terminals(aiwolf_grammar, "REQUEST ANY ( DISAGREE day 1 ID 1") # 元々：REQUEST ANY ( DISAGREE day 1 ID 1 0 )


    test_get_next_terminals(aiwolf_grammar, "Agent 01 ESTIMATE Agent 02 VILLAGER")
    test_get_next_terminals(aiwolf_grammar, "Agent 02 INQUIRE Agent 01 ( Agent 01 ESTIMATE Agent 02 WEREWOLF ) ")
    test_get_next_terminals(aiwolf_grammar, "REQUEST ANY ( DISAGREE day 1 ID 1 0 )")
        
    
#元々のプロトコルをパースできる表現に変更
def convert_protocol_to_ll1(s : str) -> str:
    #Agentの表記を変更： "Agent[数字]" を "Agent [数字]" に変換
    s = convert_agent(s)
    # '(' と ')' の前後に半角スペース ' ' を追加
    s = convert_parentheses(s)
    #日付の表記を変更： "day[数字]" を "day [各数字]" に変換
    s = convert_day(s)
    #IDの表記を変更： "ID[数字]" を "ID [各数字]" に変換
    s = convert_ID(s)

    return s

#パースできる表現を元々のプロトコルに戻す
def convert_ll1_to_protocol(s : str) -> str:
    #Agentの表記を変更： "Agent [数字]" を "Agent[数字]" に変換
    s = revert_agent(s)
    # '(' と ')' の前後の半角スペース ' ' を削除
    s = revert_parentheses(s)
    #日付の表記を変更："day [各数字]" を "day[数字]" に変換
    s = revert_day(s)
    #IDの表記を変更："ID [各数字]" を "ID:[数字]" に変換
    s = revert_ID(s)
    
    return s
    
def convert_agent(s):
    # 文字列中の '[' と ']' を半角スペース ' ' に変換
    s = s.replace('[', ' ').replace(']', '')
    return s

def revert_agent(s):
    # "Agent [数字]" を "Agent[数字]" に変換する正規表現
    pattern = r"(Agent) (\d+)"

    # 文字列内のパターンにマッチする部分を変換する関数
    agent_str =""
    digits = ""
    def replace_func(match):
        agent_str = match.group(1)
        digits = match.group(2)

        return f"{agent_str}[{digits}]"
    print(agent_str, digits)

    # 文字列内のパターンにマッチする部分を変換
    s = re.sub(pattern, replace_func, s)

    return s

def convert_parentheses(s):
    # '(' と ')' の前後に半角スペース ' ' を追加
    s = s.replace('(', '( ').replace(')', ' )')
    return s

def revert_parentheses(s):
    # '(' と ')' の前後の半角スペース ' ' を削除
    s = s.replace('( ', '(').replace(' )', ')')
    return s

def convert_day(s):
    # "day[数字]" を "day [各数字]" に変換する正規表現
    pattern = r"(day)(\d+)"

    # 文字列内のパターンにマッチする部分を変換する関数
    def replace_func(match):
        day_str = match.group(1)
        digits = match.group(2)

        # 数字を1桁ずつスペースで区切る
        spaced_digits = ' '.join(list(digits))

        return f"{day_str} {spaced_digits}"

    # 文字列内のパターンにマッチする部分を変換
    s = re.sub(pattern, replace_func, s)

    return s
    
    
def revert_day(s):
    # "day [各数字]" を "day[数字]" に変換する正規表現
    pattern = r"(day)(?:\s+(\d))+"

    # 文字列内のパターンにマッチする部分を変換する関数
    def replace_func(match):
        day_str = match.group(1)

        # スペースで区切られた数字を連結
        concatenated_digits = ''.join(match.groups()[1:])

        return f"{day_str}{concatenated_digits}"

    # 文字列内のパターンにマッチする部分を変換
    s = re.sub(pattern, replace_func, s)

    return s

def convert_ID(s):
    # 文字列中の 'ID:' を'ID ' に変換
    s = s.replace('ID:', 'ID ')
    # "ID [数字]" を "ID [各数字]" に変換する正規表現
    pattern = r"(ID)(\d+)"

    # 文字列内のパターンにマッチする部分を変換する関数
    def replace_func(match):
        ID_str = match.group(1)
        digits = match.group(2)

        # 数字を1桁ずつスペースで区切る
        spaced_digits = ' '.join(list(digits))

        return f"{ID_str} {spaced_digits}"

    # 文字列内のパターンにマッチする部分を変換
    s = re.sub(pattern, replace_func, s)

    return s

def revert_ID(s):
    # "ID [各数字]" を "ID[数字]" に変換する正規表現
    pattern = r"(ID)(?:\s+(\d))+"

    # 文字列内のパターンにマッチする部分を変換する関数
    def replace_func(match):
        ID_str = match.group(1)
        # スペースで区切られた数字を連結
        concatenated_digits = ''.join(match.groups()[1:])

        return f"{ID_str}{concatenated_digits}"

    # 文字列内のパターンにマッチする部分を変換
    s = re.sub(pattern, replace_func, s)

    # 文字列中の 'ID' を'ID:' に変換
    s = s.replace('ID', 'ID:')
    return s
    
if __name__ == "__main__":
    #first_set, follow_set, parse_tableのテスト
    test_LL1Grammars()
    #パーサーのテスト
    test_grammar_parsers()
    
    aiwolf_grammar = aiwolf_protocol_grammar()
    
    # 使用例1
    partial_sentence = "Agent[01] ESTIMATE Agent[02]"
    #convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence)) == partial_sentenceかどうかを確認
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    # 使用例2
    partial_sentence = "Agent[04] AGREE day4"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    
    # 使用例3
    partial_sentence = "Agent[05] BECAUSE (Agent[06]"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    # 使用例4
    partial_sentence = "BECAUSE (Agent[06]"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    # 使用例5
    partial_sentence = "Agent[07] BECAUSE"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    # 使用例6
    partial_sentence = "VOTE Agent[01]"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    # 使用例7
    partial_sentence = "VOTE"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    # 使用例8:
    partial_sentence = "AND (NOT (VOTE Agent[01])) (VOTE Agent[02])"
    assert (convert_ll1_to_protocol(convert_protocol_to_ll1(partial_sentence))== partial_sentence)
    print(f"{partial_sentence}:",aiwolf_grammar.get_next_terminals(convert_protocol_to_ll1(partial_sentence)))
    
