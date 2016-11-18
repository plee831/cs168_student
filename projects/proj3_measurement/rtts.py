import os
import re
import subprocess
import numpy as np
import matplotlib.pyplot as plot
from mathplotlib.backends import backend_pdf

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
		f1.write("\""+hostnames[i]+"\": [")
		ping = subprocess.Popen(
			["ping", "-c", str(num_packets), hostnames[i]],
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE
		)
		out, error = ping.communicate()
		last_seen = 0
		done_with_ttls = False
		for line in out.split("\n"):
			if PATTERN_RTT.match(line):
				rtt_details = PATTERN_RTT.search(line).groups()
				last_seen = rtt_details[0]
				if int(rtt_details[0]) == int(num_packets)-1:
					f1.write(rtt_details[1])
				else:
					f1.write(rtt_details[1]+", ")			
			elif PATTERN_PACKET_LOSS_PER.match(line):
				ping_info = PATTERN_PACKET_LOSS_PER.search(line).groups()
				f2.write("\""+hostnames[i]+"\": {\"drop_rate\": "+ping_info[0]+", ")
			elif PATTERN_TOTAL_RTT.match(line):
				ping_info = PATTERN_TOTAL_RTT.search(line).groups()
				f2.write("\"max_rtt\": "+ping_info[3]+", \"median_rtt\": "+ping_info[2]+"}")
				if not i == len(hostnames)-1:
					f2.write(", ")
			elif PATTERN_DROPED_PACKET.match(line):
				dropped_packet = PATTERN_DROPED_PACKET.search(line).groups()[0]
				last_seen = dropped_packet
				if not dropped_packet == int(num_packets)-1:
					f1.write("-1, ")
				else:
					f1.write("-1")
					done_with_ttls = True
			else:
				if not done_with_ttls:
					if int(last_seen) == int(num_packets)-2:
						f1.write("-1")
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
	plot.plot(y_values, x_values, label=”Median RTT CDF”)
	plot.legend() # This shows the legend on the plot.
 	plot.grid() # Show grid lines, which makes the plot easier to read.
 	plot.xlabel("x axis!") # Label the x-axis.
 	plot.ylabel("y axis!") # Label the y-axis.
 	plot.show()
	my_filepath = os.path.abspath(output_cdf_filename)
 	with backendpdf.PdfPages(my_filepath) as pdf:
    	pdf.savefig()

# """
# this function should take in a filename with the json formatted 
# raw ping data for a particular hostname, and plot a CDF of the RTTs
# """
def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename): 
	plot.plot(y_values, x_values, label=”Ping CDF”)
	plot.legend() # This shows the legend on the plot.
 	plot.grid() # Show grid lines, which makes the plot easier to read.
 	plot.xlabel("x axis!") # Label the x-axis.
 	plot.ylabel("y axis!") # Label the y-axis.
 	plot.show()
 	my_filepath = os.path.abspath(output_cdf_filename)
 	with backendpdf.PdfPages(my_filepath) as pdf:
    	pdf.savefig()

