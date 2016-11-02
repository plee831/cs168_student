# -*- coding: utf-8 -*-
import os
import re
import subprocess
import numpy as np
import time


def run_traceroute(hostnames, num_packets, output_filename):
    f = open(output_filename, 'w+')
    timestamp = str(time.clock())
    f.write("{\"timestamp\": " + timestamp + ", \n");
    for i in range(0, len(hostnames)):
        f.write("HOSTNAME: " + hostnames[i] + "\n")
        tr = subprocess.Popen(
            ["traceroute", "-a", "-q", str(num_packets), hostnames[i]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, error = tr.communicate()
        f.write(out);
    f.close()


def parse_traceroute(raw_traceroute_filename, output_filename):
    PATTERN_ASN = re.compile("(\d+)\]")
    PATTERN_IP = re.compile("\((.*?)\)")
    str_none = "\"None\""

    f = open(output_filename, 'w+');
    raw = open(raw_traceroute_filename, 'r+')
    lines = raw.readlines();

    for j in range(0, len(lines)):
        str_line = lines[j];
        line = lines[j].split();

        first = line[0];

        if first == "{\"timestamp\":":
            f.write(line[0] + " " + line[1] + " ");
            continue;
        elif first == "HOSTNAME:":
            f.write("\"" + line[1] + "\": [")
            continue;
        # new hop
        elif first.isdigit():
            # if router does not respond
            # f.write(first)
            if line[1] == "*":
                f.write("[{\"name\": " + str_none + ", \"ip\": " + str_none + ", \"asn\": " + str_none + "}");

                for k in range(2, len(line)):
                    if line[k] == "*":
                        f.write(", {\"name\": " + str_none + ", \"ip\": " + str_none + ", \"asn\": " + str_none + "}");
                    elif (PATTERN_ASN.search(line[k]) != None):
                        f.write(
                            ", {\"name\": \"" + line[k + 1] + "\", \"ip\": \"" + PATTERN_IP.search(str_line).groups()[
                                0] + "\", \"asn\": \"" + PATTERN_ASN.search(str_line).groups()[0] + "\"}");
                    else:
                        continue;

            # if router responds
            else:
                f.write("[{\"name\": \"" + line[2] + "\", \"ip\": \"" + PATTERN_IP.search(str_line).groups()[
                    0] + "\", \"asn\": \"" + PATTERN_ASN.search(str_line).groups()[0] + "\"}");

        # same hop, different router
        else:
            if first == "*":
                f.write("{\"name\": " + str_none + ", \"ip\": " + str_none + ", \"asn\": " + str_none + "}");

                for k in range(2, len(line)):
                    if line[k] == "*":
                        f.write(", {\"name\": " + str_none + ", \"ip\": " + str_none + ", \"asn\": " + str_none + "}");
                    elif (PATTERN_ASN.search(line[k]) != None):
                        f.write(
                            ", {\"name\": \"" + line[k + 1] + "\", \"ip\": \"" + PATTERN_IP.search(str_line).groups()[
                                0] + "\", \"asn\": \"" + PATTERN_ASN.search(str_line).groups()[0] + "\"}");
                    else:
                        continue;

            else:
                f.write("{\"name\": \"" + line[1] + "\", \"ip\": \"" + PATTERN_IP.search(str_line).groups()[
                    0] + "\", \"asn\": \"" + PATTERN_ASN.search(str_line).groups()[0] + "\"}");

        if j == (len(lines) - 1):
            f.write("]]}");
        elif lines[j + 1].split()[0] == "HOSTNAME:":
            f.write("]], ")
        elif lines[j + 1].split()[0].isdigit():
            f.write("], ");
        else:
            f.write(", ");

# if __name__ == "__main__":
# hostnames = ["google.com"]
# sites_a = ["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"]
# sites_b = ["tpr-route-server.saix.net", "route-server.ip-plus.net", "route-views.oregon-ix.net", "route-server.eastern.allstream.com"]
# run_traceroute(hostnames, 1, "test.txt")
# run_traceroute(sites_a, 3, "tr_part_a.txt")
# run_traceroute(sites_b, 3, "tr_part_b.txt")

# parse_traceroute("test.txt", "test.json")
# parse_traceroute("tr_part_a.txt", "tr_part_a.json")
# parse_traceroute("tr_part_b.txt", "tr_part_b.json")

# python project3_tests.py --tr-part-b "tr_part_b.json"
