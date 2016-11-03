# -*- coding: utf-8 -*-
import os
import re
import subprocess
import numpy as np
import time

def run_traceroute(hostnames, num_packets, output_filename):
	f = open(output_filename, 'w+')
	timestamp = str(time.time())
	f.write("{\"timestamp\": "  + timestamp + ", \n");
	for i in range(0, len(hostnames)):
		f.write("HOSTNAME: " + hostnames[i] +"\n")
		tr = subprocess.Popen(
			["traceroute", "-A", "-q", str(num_packets), hostnames[i]],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		out, error = tr.communicate()
		f.write(out);
	f.close()

def parse_traceroute(raw_traceroute_filename, output_filename):
	PATTERN_ASN = re.compile("(\d+)\]")
	PATTERN_IP = re.compile("\b(?:\d{1,3}\.){3}\d{1,3}\b")
	PATTERN_HOSTNAME = re.compile("^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$")
	str_none = "\"None\""

	f = open(output_filename, 'w+');
	raw = open(raw_traceroute_filename, 'r+')
	lines = raw.readlines();

	for j in range(0, len(lines)):
		str_line = lines[j];
		line = lines[j].split();


		first = line[0];

		#HANDLING ALL NON-HOP/ROUTER LINES
		if first == "traceroute":
			continue;
		elif first == "{\"timestamp\":":
			f.write(line[0] + " " + line[1] + " ");
			continue;
		elif first == "HOSTNAME:":
			f.write("\"" + line[1] + "\": [")
			continue;

		#IF WE HAVE A NEW HOP
		if first.isdigit():
			f.write("[")

		#HANDLES ALL ROUTER LINES
		name_tbr = "None"
		ip_tbr = "None"
		asn_tbr = "None"
		if PATTERN_HOSTNAME.search(str_line):
			name_tbr = PATTERN_HOSTNAME.searh(str_line).groups()[0]
		if PATTERN_ASN.search(str_line):
			asn_tbr = PATTERN_ASN.search(str_line).groups()[0]
		if PATTERN_IP.search(str_line):
			ip_tbr = PATTERN_IP.search(str_line).groups()[0]
		tbr = "{\"name\": \"" + name_tbr + "\", \"ip\": \"" + ip_tbr + "\", \"asn\": \"" + asn_tbr + "\"}"

		f.write(tbr)

		#IF END OF FILE
		if j == (len(lines) - 1):
			f.write("]]}");
		#IF NEXT LINE IS NEW TRACEROUTE CALL TO DIFF HOSTNAME
		elif lines[j+1].split()[0] == "HOSTNAME:":
			f.write("]], ")
		#IF NEXT LINE IS NEW HOP
		elif lines[j+1].split()[0].isdigit():
			f.write("], ");
		#IF NEXT LINE IS ANOTHER ROUTER
		else:
			f.write(", ");

if __name__ == "__main__":
	sites_a = ["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"]
	sites_b = ["tpr-route-server.saix.net", "route-server.ip-plus.net", "route-views.oregon-ix.net", "route-server.eastern.allstream.com"]
	# run_traceroute(sites_a, 5, "tr_part_a1.txt")
	# run_traceroute(sites_a, 5, "tr_part_a2.txt")
	# run_traceroute(sites_a, 5, "tr_part_a3.txt")
	# run_traceroute(sites_a, 5, "tr_part_a4.txt")
	# run_traceroute(sites_a, 5, "tr_part_a5.txt")
	# parse_traceroute("tr_part_a1.txt", "tr_part_a1.json")
	# parse_traceroute("tr_part_a2.txt", "tr_part_a2.json")
	# parse_traceroute("tr_part_a3.txt", "tr_part_a3.json")
	# parse_traceroute("tr_part_a4.txt", "tr_part_a4.json")
	# parse_traceroute("tr_part_a5.txt", "tr_part_a5.json")
	# parse_traceroute("tr_part_a.txt", "tr_part_a.json")

	# run_traceroute(sites_b, 5, "tr_part_b1.txt")
	# parse_traceroute("tr_part_b1.txt", "tr_part_b1.json")
	# parse_traceroute("tr_part_b2.txt", "tr_part_b2.json")

