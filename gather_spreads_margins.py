__author__ = 'ben.packer'

import csv
from lxml import html
import numpy as np
import pandas as pd
import re
import requests
import sys

ats_filename = "var/cache/ats.csv"

ats_margins = {}
with open(ats_filename, 'r') as f:
    reader = csv.reader(f.read().splitlines())
    for row in reader:
        ats_margins[float(row[0])] = map(float, filter(lambda x: x != '', row[1:]))

margin_filename = "var/cache/margins.csv"

margins = pd.read_csv(margin_filename)["Margin"]
margins = margins[margins > 0]
histogram = np.histogram(margins, bins=range(0, 73), density=True)


def chance_of_winning(original_line, current_line, debug=False):
    if current_line < 0:
        current_line *= -1
        original_line *= -1
    if current_line not in ats_margins:
        print str(current_line) + " not found"
        return 0.5
    if original_line < current_line:
        filter_min = 0
        filter_max = current_line-original_line
    else:
        filter_min = current_line-original_line
        filter_max = 0
    extra_wins = filter(lambda x: filter_min <= x <= filter_max, ats_margins[current_line])
    extra_win_percent = float(len(extra_wins))/len(ats_margins[current_line])

    if current_line == int(current_line):
        exact_push = filter(lambda x: x == 0, ats_margins[current_line])
        push_percent = float(len(exact_push))/len(ats_margins[current_line])
        if debug:
            print "Debug: %d, %f" % (len(exact_push), push_percent)
        one_side_win_percent = (1 - push_percent)/2.0
    else:
        one_side_win_percent = 0.5
    if debug:
        print "Debug (%0.1f, %0.1f): %d, %d, %f, %f, %f" % (original_line, current_line, len(extra_wins),
                                                            len(ats_margins[current_line]), extra_win_percent,
                                                            one_side_win_percent,
                                                            one_side_win_percent + extra_win_percent)
    return one_side_win_percent + extra_win_percent


def get_percentage(pick1, pick2):
    #pick1, pick2 = abs(pick1), abs(pick2)
    if pick2 < pick1:
        pick1, pick2 = pick2, pick1
    spreads = np.arange(pick1, pick2+0.5, 0.5)
    total_percentage = 0
    for i, spread in enumerate(spreads):
        factor = 0.5 if (i == 0 or i == len(spreads)-1) else 1.0
        if int(spread) == spread:
            percentage = histogram[0][abs(spread)]
            #print "%f * %f" % (factor, percentage)
            total_percentage += percentage*factor

    return total_percentage


def main():
    spreads_url = 'http://www.vegasinsider.com/college-football/odds/las-vegas/'
    season = 2
    week = 6
    row_start = 1
    num_rows = 151
    picks_filename = "/Users/ben.packer/other/fantasy/picks/season%d_week%d_picks.html" % (season, week)
    team_name_filename = "var/cache/team_names.csv"

    spreads = {}

    page = requests.get(spreads_url)
    tree = html.fromstring(page.text)

    #for row in xrange(row_start, num_rows + 1, 2):
    for row in xrange(row_start, num_rows + 1):
        #print row
        try:
            teams = [tree.xpath('/html/body/table/tr/td[2]/table[3]/tr[2]/td/table[2]/tr[%d]/td[1]/b[1]/a/text()' % row)[0],
                     tree.xpath('/html/body/table/tr/td[2]/table[3]/tr[2]/td/table[2]/tr[%d]/td[1]/b[2]/a/text()' % row)[0]]
            #print teams
            top_line = tree.xpath('/html/body/table/tr/td[2]/table[3]/tr[2]/td/table[2]/tr[%d]/td[3]/a/text()' % row)[1]
            #print "top"
            #print top_line
            bottom_line = tree.xpath('/html/body/table/tr/td[2]/table[3]/tr[2]/td/table[2]/tr[%d]/td[3]/a/text()' % row)[2]
            #print "bottom"
            #print bottom_line
        except IndexError:
            #print "Bad row"
            #print row
            continue
        #print teams
        if top_line[0] == "-":
            favorite = 0
            spread_line = top_line
        elif bottom_line[0] == "-":
            favorite = 1
            spread_line = bottom_line
        elif top_line[0:2] == "PK" or bottom_line[0:2] == "PK":
            spreads[teams[0]] = 0
            spreads[teams[0]] = 0
            continue
        else:
            print "Error in row %d: %s, %s" % (row, bottom_line, top_line)
            continue

        match = re.match("\-\d+", spread_line).group(0)
        spread = int(match)
        if spread_line[len(match)] == u'\xbd':
            spread -= 0.5

        #print "%s is favored by %0.1f" % (teams[favorite], spread)
        spreads[teams[favorite]] = spread
        #spreads[teams[1-favorite]] = -spread

    team_names = {}
    for row in csv.reader(open(team_name_filename, "r")):
        team_names[row[0]] = row[1]

    picks_html = open(picks_filename, "r").read()
    differences = {}
    for (team_name, vegas_spread) in spreads.items():
        if team_name in team_names.keys():
            team_name = team_names[team_name]
        else:
            team_name = re.sub("State", "St.", team_name, 1)
        print "Checking team %s" % team_name
        try:
            pick_spread = float(re.search("(>|\d )%s \(.*\) ([\+\-]\d+\.5)" % team_name, picks_html, flags=re.I).group(2))
            #differences[team_name] = [vegas_spread - pick_spread, get_percentage(vegas_spread, pick_spread), pick_spread]
            differences[team_name] = [vegas_spread - pick_spread, chance_of_winning(pick_spread, vegas_spread), pick_spread]
        except AttributeError:
            #print "Skipping"
            continue

        #if pick_spread != vegas_spread:
        #    print "Difference of %0.1f for %s: pick sheet has %0.1f while current spread is %0.1f" % (
        #        differences[team_name], team_name, pick_spread, vegas_spread
        #    )
        #else:
        #    print "%s has a matching spread of %0.1f (%0.1f)" % (team_name, pick_spread, vegas_spread)

    sorted_differences = sorted(differences.iteritems(), key=lambda x: abs(x[1][1]), reverse=True)
    for i, item in enumerate(sorted_differences):
        if item[1][0] < 0:
            bet_str = "Bet on"
        else:
            bet_str = "Bet against"
        print "%s %s: %0.1f%% (%0.1f, %0.1f)" % (bet_str, item[0], item[1][1]*100, item[1][2], item[1][0])
        if i == 9:
            print "--------------------"
        if i > 25:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print chance_of_winning(float(sys.argv[2]), float(sys.argv[3]), debug=True)
    else:
        main()
