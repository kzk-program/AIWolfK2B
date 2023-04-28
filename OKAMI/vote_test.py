def vote(absolute_black, absolute_white, greys):
    """
    占い師の投票戦略
    村人と同様にtargetを定めた後、確定黒リストと確定白リストを用いて修正する
    """
    target = 'Agent[02]'
    if len(absolute_black) > 0:  # 確定黒リストに人がいたら
        print(list(absolute_black)[0])
        return list(absolute_black)[0]  # その中で最初に確定黒になった人に投票
    if target in absolute_white:
        if len(greys) > 0:  # targetが確定白リストに入っていたら
            print(list(absolute_black)[0])
            return list(greys)[0]  # 他のgreyから選んで投票．1番目を確定させる？修正．random 抽出の方がいいと思う．
    print(target)
    return target

