# -*- coding: utf-8 -*-
import os
import re
import subprocess
import numpy as np
import matplotlib.pyplot as plot
from matplotlib.backends import backend_pdf

# "youtube.com": [": [14.475,


def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
    PATTERN_PACKET_LOSS_PER = re.compile("\d+ packets transmitted, \d+ packets received, (\d+.\d+)% packet loss")
    PATTERN_TOTAL_RTT = re.compile("round-trip min\/avg\/max\/stddev = (\d+.\d+)\/(\d+.\d+)\/(\d+.\d+)\/(\d+.\d+) ms")
    PATTERN_RTT = re.compile("\d+ bytes from \d+.\d+.\d+.\d+: icmp_seq=(\d+) ttl=\d+ time=(\d+.\d+) ms")
    PATTERN_DROPED_PACKET = re.compile("Request timeout for icmp_seq (\d+)")

    f1 = open(raw_ping_output_filename, 'w+')
    f1.write('{')
    f2 = open(aggregated_ping_output_filename, 'w+')
    f2.write('{')

    for i in range(0, len(hostnames)):
        print hostnames[i]
        f1.write("\""+hostnames[i]+"\": [")
        ping = subprocess.Popen(
            ["ping", "-c", str(num_packets), hostnames[i]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, error = ping.communicate()
        last_seen = 0
        done_with_ttls = False
        for line in out.split("\n"):
            if PATTERN_RTT.match(line):
                rtt_details = PATTERN_RTT.search(line).groups()
                last_seen = rtt_details[0]
                if int(rtt_details[0]) == int(num_packets) - 1:
                    f1.write(rtt_details[1])
                else:
                    f1.write(rtt_details[1] + ", ")
            elif PATTERN_PACKET_LOSS_PER.match(line):
                ping_info = PATTERN_PACKET_LOSS_PER.search(line).groups()
                f2.write("\"" + hostnames[i] + "\": {\"drop_rate\": " + ping_info[0] + ", ")
                if float(ping_info[0]) == 100.0:
                    f2.write("\"max_rtt\": "+str(float(0.0))+", \"median_rtt\": +"+str(float(0.0))+"}")
                    if not i == len(hostnames) - 1:
                        f2.write(", ")
            elif PATTERN_TOTAL_RTT.match(line):
                ping_info = PATTERN_TOTAL_RTT.search(line).groups()
                f2.write("\"max_rtt\": " + ping_info[3] + ", \"median_rtt\": " + ping_info[2] + "}")
                if not i == len(hostnames) - 1:
                    f2.write(", ")
            elif PATTERN_DROPED_PACKET.match(line):
                dropped_packet = PATTERN_DROPED_PACKET.search(line).groups()[0]
                last_seen = dropped_packet
                if not dropped_packet == int(num_packets) - 1:
                    f1.write("-1.0, ")
                else:
                    f1.write("-1.0")
                    done_with_ttls = True
            else:
                if not done_with_ttls:
                    if int(last_seen) == int(num_packets) - 2:
                        f1.write("-1.0")
                        done_with_ttls = True
        if i == len(hostnames) - 1:
            f1.write("]")
        else:
            f1.write("], ")
    f1.write('}')
    f1.close()
    f2.write('}')
    f2.close()


"""
this function should take in a filename with the json formatted aggregated 
ping data and plot a CDF of the median RTTs for each website that responds to ping
"""


def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):
    file = open(agg_ping_results_filename, 'r')
    AGGS_PATTERN = re.compile("\n?\t?\w+: {\"\w+\": (\d+.?\d*), \"w+\": (\d+.?\d*), \"\w+\": (\d+.?\d*)},?")
    median_rtts = []
    for m in re.finditer(AGGS_PATTERN, file.read()):
        median_rtts.append(m.group(2))
    sorted_median_rtts = sorted(median_rtts)
    y_values = []
    for x_value in median_rtts:
        y_values[median_rtts.index(x_value)] = sorted_median_rtts.index(x_value)+1 / len(sorted_median_rtts)
    plot.plot(y_values, median_rtts, label='Median RTT CDF')
    plot.legend()  # This shows the legend on the plot.
    plot.grid()  # Show grid lines, which makes the plot easier to read.
    plot.xlabel("Median RTT's")  # Label the x-axis.
    plot.ylabel("Cumulative Fraction")  # Label the y-axis.
    plot.show()
    my_file_path = os.path.abspath(output_cdf_filename)
    with backend_pdf.PdfPages(my_file_path) as pdf:
        pdf.savefig()


"""
this function should take in a filename with the json formatted
raw ping data for a particular hostname, and plot a CDF of the RTTs
"""


def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
    file = open(raw_ping_results_filename, 'r')
    RAW_RTT_PATTERN = re.compile("\[[(\d+.?\d*),? ?]*\]")
    raw_rtts = []
    for m in re.finditer(RAW_RTT_PATTERN, file.read()):
        for i in range(0, len(m.groups())):
            raw_rtts.append(m.group(i))
    sorted_raw_rtts = sorted(raw_rtts)
    y_values = []
    for x_value in raw_rtts:
        y_values[raw_rtts.index(x_value)] = sorted_raw_rtts.index(x_value) + 1 / len(sorted_raw_rtts)
    y_values = [0.5]
    plot.plot(y_values, raw_rtts, label='Ping CDF')
    plot.legend()  # This shows the legend on the plot.
    plot.grid()  # Show grid lines, which makes the plot easier to read.
    plot.xlabel("RTTs")  # Label the x-axis.
    plot.ylabel("Cumulative Fraction")  # Label the y-axis.
    plot.show()
    my_file_path = os.path.abspath(output_cdf_filename)
    with backend_pdf.PdfPages(my_file_path) as pdf:
        pdf.savefig()

if __name__ == "__main__":
    f = open("alexa_top_100", "r")
    alexa = [x for x in f.read().split("\n")]
    alexa.remove("")
    # print ("part a starting")
    # run_ping(alexa, '10', 'rtt_a_raw.json', 'rtt_a_agg.json')
    print ("part b starting")
    run_ping(["google.com", "todayhumor.co.kr", "zanvarsity.ac.tz", "taobao.com"], '500', 'rtt_b_raw.json', 'rtt_b_agg.json')

# sites_a = ["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"]
# sites_b = ["tpr-route-server.saix.net", "route-server.ip-plus.net", "route-views.oregon-ix.net", "route-server.eastern.allstream.com"]
# run_traceroute(hostnames, 1, "test.txt")
# run_traceroute(sites_a, 3, "tr_part_a.txt")
# run_traceroute(sites_b, 3, "tr_part_b.txt")

# parse_traceroute("test.txt", "test.json")
# parse_traceroute("tr_part_a.txt", "tr_part_a.json")
# parse_traceroute("tr_part_b.txt", "tr_part_b.json")
# python project3_tests.py
# python project3_tests.py --tr-part-b "tr_part_b.json"