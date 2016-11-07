# -*- coding: utf-8 -*-
import re
import subprocess
import numpy as np
import matplotlib.pyplot as plot


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
        f1.write("\"" + hostnames[i] + "\": [")
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
                    f2.write("\"max_rtt\": " + str(float(0.0)) + ", \"median_rtt\": +" + str(float(0.0)) + "}")
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
    AGGS_PATTERN = re.compile("\"median_rtt\": (\+?\d+.?\d*)")
    median_rtts = []
    mat = re.findall(AGGS_PATTERN, file.read())
    for i in range(0, len(mat)):
        median = mat[i]
        median_rtts.append(float(median))
    sorted_median_rtts = sorted(median_rtts)
    y_values = [0 for x in range(0, len(median_rtts))]
    for x_value in median_rtts:
        temp = float(sorted_median_rtts.index(x_value) + 1) / float(len(sorted_median_rtts))
        y_values[sorted_median_rtts.index(x_value)] = temp
    print sorted_median_rtts
    print y_values
    plot.plot(sorted_median_rtts, y_values, label='Median RTT\'s')
    plot.legend(loc=4)  # This shows the legend on the plot.
    plot.grid()  # Show grid lines, which makes the plot easier to read.
    plot.xlabel("Milliseconds")  # Label the x-axis.
    plot.ylabel("Cumulative Fraction")  # Label the y-axis.
    plot.title("Median RTT CDF")
    # plot.show()
    plot.savefig(output_cdf_filename)


"""
this function should take in a filename with the json formatted
raw ping data for a particular hostname, and plot a CDF of the RTTs
"""


def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
    file = open(raw_ping_results_filename, 'r')

    RAW_RTT_PATTERN = re.compile("\"\w+.?\w+.?\w*\": \[[-?\d+.?\d*,? ?]*\]")
    m = re.findall(RAW_RTT_PATTERN, file.read())
    RTTS_PATTERN = re.compile("-?\d+.?\d*")
    HOSTNAME_PATTERN = re.compile("\"\w+.?\w+.?\w*\"")
    for i in range(0, len(m)):
        line = m[i]
        hostname = re.findall(HOSTNAME_PATTERN, line)[0].split("\"")[1]
        rtt_matcher = re.findall(RTTS_PATTERN, line)
        rtts = []
        for j in range(0, len(rtt_matcher)):
            if float(rtt_matcher[j]) != -1.0:
                rtts.append(float(rtt_matcher[j]))
        sorted_rtts = sorted(rtts)
        y_values = []
        for x_value in sorted_rtts:
            temp = float(sorted_rtts.index(x_value) + 1) / float(len(sorted_rtts))
            y_values.append(temp)
        plot.plot(sorted_rtts, y_values, label=hostname)
    plot.legend(loc=4)  # This shows the legend on the plot.
    plot.grid()  # Show grid lines, which makes the plot easier to read.
    plot.xlabel("Milliseconds")  # Label the x-axis.
    plot.ylabel("Cumulative Fraction")  # Label the y-axis.
    plot.title("RTT CDF")
    # plot.show()
    plot.savefig(output_cdf_filename)


if __name__ == "__main__":
    plot_median_rtt_cdf("rtt_a_agg.json", "rtt_a_agg_ping_results.pdf")
    # plot_ping_cdf("rtt_b_raw.json", "rtt_b_raw_results.pdf")

    # f = open("alexa_top_100", "r")
    # alexa = [x for x in f.read().split("\n")]
    # alexa.remove("")
    # print ("part a starting")
    # run_ping(alexa, '10', 'rtt_a_raw.json', 'rtt_a_agg.json')
    # print ("part b starting")
    # run_ping(["google.com", "todayhumor.co.kr", "zanvarsity.ac.tz", "taobao.com"], '500', 'rtt_b_raw.json', 'rtt_b_agg.json')
