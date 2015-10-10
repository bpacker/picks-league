import csv

ats_filename = "var/cache/ats.csv"

ats_margins = {}
with open(ats_filename, 'r') as f:
    reader = csv.reader(f.read().splitlines())
    for row in reader:
        ats_margins[float(row[0])] = map(float,filter(lambda x:x != '',row[1:]))

def chance_of_winning(original_line, current_line):
    if original_line<current_line:
        filter_min = 0
        filter_max = current_line-original_line
    else:
        filter_min = current_line-original_line
        filter_max = 0
    #print filter_min
    #print filter_max
    extra_wins = filter(lambda x: x >= filter_min and x <= filter_max,
                        ats_margins[current_line])
    #print extra_wins
    #print len(extra_wins)
    #print len(ats_margins[current_line])
    extra_win_percent = float(len(extra_wins))/len(ats_margins[current_line])
    return 0.5 + extra_win_percent/2

print chance_of_winning(1.5, 2.5)
print chance_of_winning(2.5, 1.5)
print chance_of_winning(2.5, 3.5)
print chance_of_winning(3.5, 2.5)
print chance_of_winning(3.5, 4.5)
print chance_of_winning(4.5, 3.5)
print chance_of_winning(4.5, 5.5)
print chance_of_winning(5.5, 4.5)
print chance_of_winning(5.5, 6.5)
print chance_of_winning(6.5, 5.5)
print chance_of_winning(6.5, 7.5)
print chance_of_winning(7.5, 6.5)
