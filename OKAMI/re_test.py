import re

#l_3 = "DAY 1 GO TO UNKO"
#l_3 = "DAY 13 GO TO TOILET"
#l_3 = "AND (DAY 1 GO TO UNKO) (DAY 13 COME TO UNCHI)"
#l_3 = "AND (DAY 1 (DIVINED Agent[13] HUMAN)) (DAY 92 (DIVINED Agent[15] HUMAN)) (DAY 13 (DIVINED Agent[11] HUMAN)) (DAY 4 (DIVINED Agent[06] HUMAN)) (DAY 15 (DIVINED Agent[14] WEREWOLF))"


day_count = l.count('DAY ')
day_start = []
day_index = []
start = 0
for _ in range(day_count):
    start = l.find("DAY ", start)
    day_start.append(start)
    start += 1

max_length = len(l)
#print(max_length)
for i in day_start:
    if i+4 <= max_length:
        tmp_day_num = str(l[i+4])
    if re.match('[0-9]', l[i+5]):
        if i+5 <= max_length:
            tmp_day_num = tmp_day_num + str(l[i+5])

    print(tmp_day_num)