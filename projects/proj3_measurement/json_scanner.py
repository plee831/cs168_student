import os, re


def no_response(filename):
    f = open(filename, 'r')
    print f.read()
    AGGS_PATTERN = re.compile("\"\w+.?\w+.?\w+?\": \{\"\w+\": (\d+.?\d*?), \"\w+\": (\d+.?\d*), \"\w+\": (\d+.?\d*)")
    all_failed = 0
    at_least_one_failed = 0
    st = re.findall(AGGS_PATTERN, f.read())
    total_number = len(st)
    for m in st:
        if float(m.group(0)) <= 100.0:
            if float(m.group(0)) == 100.0:
                all_failed += 1
            if float(m.group(0)) != 0.0:
                at_least_one_failed += 1
    return [all_failed/total_number, at_least_one_failed/total_number]
