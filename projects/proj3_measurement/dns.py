# -*- coding: utf-8 -*-
import os
import re
import subprocess
import numpy as np
import time
import json

# KEYS FROM utils.py
NAME_KEY = "\"Name\": "
SUCCESS_KEY = "\"Success\": "
TIME_KEY = "\"Time in millis\": "
ANSWERS_KEY = "\"Answers\": "
QUERIES_KEY = "\"Queries\": "
QUERIED_NAME_KEY = "\"Queried name\": "
TTL_KEY = "\"TTL\": "
TYPE_KEY = "\"Type\": "
ANSWER_DATA_KEY = "\"Data\": "

"""
resolve each address 5 times
hostname_filename: the file containing the list of hostnames, e.g. alexa_top_100
output_filename: name of the json output file
dns_query_server: an optional argument that specifies the DNS server to query
"""


def run_dig(hostname_filename, output_filename, dns_query_server=None):
    f = open(output_filename, 'w+')

    host_file = open(hostname_filename, 'r')
    hostnames = host_file.readlines()

    f.write("[")
    for i in range(0, len(hostnames)):
        for j in range(0, 5):
            tr = subprocess.Popen(
                ["dig", "+trace", "+tries=1", "+nofail", hostnames[i].split("\n")[0]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, error = tr.communicate()
            success = "true"
            tbr = ""
            blocks = out.split("\n\n")
            for b in range(0, len(blocks)):
                block = blocks[b]
                body = ""
                block_split = block.split("\n")
                for k in range(0, len(block_split)):
                    line = block_split[k]
                    line_split = line.split()
                    # IF FIRST LINE OF QUERY
                    if len(line_split) == 0 or line_split[0] == ";":
                        continue
                    elif line_split[0] == ";;":
                        if line_split[1] == "Received":
                            body = "{" + TIME_KEY + line_split[len(line_split) - 2] + ", " \
                                   + ANSWERS_KEY + "[" + body + "]}"
                            if b < (len(blocks) - 2):
                                body += ", "
                        else:
                            # did not receive the packet
                            success = 'false'
                            continue
                    else:
                        queried_name = line_split[0]
                        ttl_ = line_split[1]
                        type_ = line_split[3]
                        data_ = line_split[4]
                        body = body + "{" + QUERIED_NAME_KEY + "\"" + queried_name + "\", " \
                            + ANSWER_DATA_KEY + "\"" + data_ + "\", " + TYPE_KEY \
                            + "\"" + type_ + "\", " + TTL_KEY + ttl_ + "}"

                    if k < (len(block_split) - 2):
                        body += ", "

                tbr += body
            n = "{" + NAME_KEY + "\"" + hostnames[i].split("\n")[0] + "\", " + SUCCESS_KEY \
                + success + ", " + QUERIES_KEY + "["
            tbr = n + tbr + "]}"
            if not (j == 4 and i == len(hostnames) - 1):
                tbr += ", "
            f.write(tbr)
    f.write("]")
    f.close()


"""
result format: [average_root_ttl, average_TLD_ttl, average_other_ttl, average_terminating_ttl]
"""


def get_average_ttls(filename):
    f = open(filename, 'r')
    parsed_json = json.loads(f.read())
    average_ttl_for_root = 0
    average_ttl_for_tld = 0
    average_ttl_for_other = 0
    average_ttl_for_cname_or_a = 0
    for name_index in range(0, len(parsed_json)):
        queries = parsed_json[name_index]['Queries']
        query_ttls_root_sum = 0
        query_ttls_tld_sum = 0
        query_ttls_other_sum = 0
        query_ttls_cname_or_a_sum = 0
        for query_index in range(0, len(queries)):
            answers = queries[query_index]['Answers']
            ttls_for_root = 0
            ttls_for_tld = 0
            ttls_for_other = 0
            ttls_for_cname_or_a = 0
            for answer_index in range(0, len(answers)):
                queried_name = answers[answer_index]['Queried name']
                type = answers[answer_index]['Type']
                ttl = answers[answer_index]['TTL']
                if queried_name == '.':
                    ttls_for_root += ttl
                elif queried_name == 'com.':
                    ttls_for_tld += ttl
                else:
                    ttls_for_other += ttl
                if type == 'CNAME' or type == 'A':
                    ttls_for_cname_or_a += ttl
            query_ttls_root_sum += ttls_for_root / len(answers)
            query_ttls_tld_sum += ttls_for_tld / len(answers)
            query_ttls_other_sum += ttls_for_other / len(answers)
            query_ttls_cname_or_a_sum += ttls_for_cname_or_a / len(answers)
        average_ttl_for_root += query_ttls_root_sum / len(queries)
        average_ttl_for_tld += query_ttls_tld_sum / len(queries)
        average_ttl_for_other += query_ttls_other_sum / len(queries)
        average_ttl_for_cname_or_a += query_ttls_cname_or_a_sum / len(queries)
    return [average_ttl_for_root, average_ttl_for_tld, average_ttl_for_other, average_ttl_for_cname_or_a]


"""
This function should accept the name of a json file with output as specified above as input. It should
return a 2-item list that contains the following averages, in this order:
"""


def get_average_times(filename):
    f = open(filename, 'r')
    parsed_json = json.loads(f.read())
    sum_total_time = 0
    sum_final_time = 0
    num_of_finals = 0
    for name_index in range(0, len(parsed_json)):
        queries = parsed_json[name_index]['Queries']
        for query_index in range(0, len(queries)):
            time = queries[query_index]['Time in millis']
            answers = queries[query_index]['Answers']
            for answer_index in range(0, len(answers)):
                type = answers[answer_index]['Type']
                if type == 'CNAME' or type == 'A':
                    sum_final_time += time
                    num_of_finals += 1
                sum_total_time += time
    # printed results - [3791, 86]
    return [sum_total_time / len(parsed_json), sum_final_time / num_of_finals]



"""
This function should accept json_filename, the name of a json file with output as specified above as input.
It should generate a graph with a CDF of the distribution of each of the values described in the previous
function (the total time to resolve a site and the time to resolve just the final request) and save it to
output_filename. It should not return anything.
"""


def generate_time_cdfs(json_filename, output_filename):

    pass

if __name__ == "__main__":
    # run_dig("alexa_top_100", "test_result.json")
    # get_average_ttls("test_result.json")
    get_average_times("test_result.json")
    pass
