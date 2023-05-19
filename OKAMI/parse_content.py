import re

def parenthetic_contents(string):
    stack = []
    for i, c in enumerate(string):
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1:i])


def parse_text(test):
    test = "("+test+")"
    a = list(parenthetic_contents(test))
    clist = []
    for i, content in a:
        b = re.search('\(([^)]+)', content)
        if b == None:
            if content.startswith("("):
                continue
            clist.append(content)
        else:
            if b.group().startswith("("):
                continue
            clist.append(b.group())
    clist = list(map(lambda i: i, clist))
    return clist
