import re, subprocess
import numpy as np

def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
	PATTERN_PACKET_LOSS_PER = re.compile("\d+ packets transmitted, \d+ packets received, (\d+.\d+)% packet loss")
	PATTERN_TOTAL_RTT = re.compile("round-trip min\/avg\/max\/stddev = (\d+.\d+)\/(\d+.\d+)\/(\d+.\d+)\/(\d+.\d+) ms")
	PATTERN_RTT = re.compile("\d+ bytes from \d+.\d+.\d+.\d+: icmp_seq=(\d+) ttl=\d+ time=(\d+.\d+) ms")
	PATTERN_DROPED_PACKET = re.compile("Request timeout for icmp_seq (\d+)")
	
	f1 = open(raw_ping_output_filename, 'w+')
	f1.write('{')
	f2 = open(aggregated_ping_output_filename, 'w+')
	f2.write('{')	

	for hostname in hostnames:
		f1.write(hostname+": [")
		ping = subprocess.Popen(
			["ping", "-c", str(num_packets), hostname],
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
				f2.write(hostname+": {\"drop_rate\": "+ping_info[0]+", ")
			elif PATTERN_TOTAL_RTT.match(line):
				ping_info = PATTERN_TOTAL_RTT.search(line).groups()
				f2.write("\"max_rtt\": "+ping_info[3]+", \"median_rtt\": "+ping_info[2]+"}, ")
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
		f1.write("], ")
	f1.write('}')
	f1.close()
	f2.write('}')
	f2.close()

def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):


# def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename): 