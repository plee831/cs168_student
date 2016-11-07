# -*- coding: utf-8 -*-
import os
import re
import subprocess
import numpy as np
import time

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
    pass


if __name__ == "__main__":
    run_dig("alexa_top_100", "test_result.json")
    pass
