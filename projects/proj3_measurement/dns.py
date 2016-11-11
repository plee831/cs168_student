# -*- coding: utf-8 -*-
import subprocess
import json
import matplotlib.pyplot as plot
import re


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
    PATTERN_TIME = re.compile("Query time (\d+) msec")
    PATTERN_STATUS = re.compile("status: NOERROR")
    PATTERN_ANSWER_SECTION = re.compile("ANSWER SECTION:")
    PATTERN_ADD_SECTION = re.compile("ADDITIONAL SECTION:")

    f = open(output_filename, 'w+')

    host_file = open(hostname_filename, 'r')
    hostnames = host_file.readlines()

    f.write("[")
    if dns_query_server != None:
        final = ""
        for i in range(0, len(hostnames)):
            for j in range(0, 5):
                tr = subprocess.Popen(
                    ["dig", hostnames[i].split("\n")[0], "@"+dns_query_server],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                out, error = tr.communicate()
                tbr = ""

                queries = out.split(";; Got answer:");
                for q in range(1, len(queries)):
                    success = "false"  # WILL CHANGE WHEN WE PARSE
                    time_tbr = 0

                    query_tbr = ""  # WILL BE WRITTENT O FILE
                    query = queries[q]

                    blocks = out.split("\n\n")
                    for b in range(0, len(blocks)):
                        block = blocks[b]
                        body = ""
                        block_split = block.split("\n")

                        for k in range(0, len(block_split)):
                            line = block_split[k]
                            line_split = line.split()

                            if b == 0 or b == (len(blocks) - 1):  # FIRST BLOCK or LAST BLOCK
                                if PATTERN_TIME.search(line):
                                    time_tbr = PATTERN_TIME.search(line).groups()[0]
                                if PATTERN_STATUS.search(line):
                                    success = "true"

                            elif PATTERN_ANSWER_SECTION.search(block_split[0]) or PATTERN_ADD_SECTION.search(
                                    block_split[0]):
                                if len(line_split) == 0 or line_split[0] == ";;":
                                    continue

                                queried_name = line_split[0]
                                ttl_ = line_split[1]
                                type_ = line_split[3]
                                data_ = line_split[4]
                                tbw = "{" + QUERIED_NAME_KEY + "\"" + queried_name + "\", " \
                                      + ANSWER_DATA_KEY + "\"" + data_ + "\", " + TYPE_KEY \
                                      + "\"" + type_ + "\", " + TTL_KEY + ttl_ + "},"
                                body += tbw
                                # body = body + "\n\t\t" + tbw
                                # if len(blocks) < 4:
                                #     if block_split[k]:
                            else:
                                pass
                        query_tbr = query_tbr + body

                        # subheader = "\n\t" + "{" + TIME_KEY + str(time_tbr) + ", " + ANSWERS_KEY + "["
                    subheader = "{" + TIME_KEY + str(time_tbr) + ", " + ANSWERS_KEY + "["
                    query_tbr = subheader + query_tbr[:len(query_tbr) - 1] + "]},"
                    tbr += query_tbr
                # header = "\n" + "{" + NAME_KEY + "\"" + hostnames[i].split("\n")[0] + "\", " + SUCCESS_KEY \
                header = "{" + NAME_KEY + "\"" + hostnames[i].split("\n")[0] + "\", " + SUCCESS_KEY \
                         + success + ", " + QUERIES_KEY + "["
                tbr = header + tbr[:len(tbr) - 1] + "]},"
                final += tbr
        f.write(final[:len(final) - 1] + "]")

    else:
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
    # printed results - [587, 86]
    return [sum_total_time / len(parsed_json), sum_final_time / num_of_finals]


"""
This function should accept json_filename, the name of a json file with output as specified above as input.
It should generate a graph with a CDF of the distribution of each of the values described in the previous
function (the total time to resolve a site and the time to resolve just the final request) and save it to
output_filename. It should not return anything.
"""


def generate_time_cdfs(json_filename, output_filename):
    f = open(json_filename, 'r')
    parsed_json = json.loads(f.read())
    total_times = []
    final_times = []
    num_of_finals = 0
    for name_index in range(0, len(parsed_json)):
        queries = parsed_json[name_index]['Queries']
        sum_total_time = 0
        sum_final_time = 0
        for query_index in range(0, len(queries)):
            time = queries[query_index]['Time in millis']
            answers = queries[query_index]['Answers']
            for answer_index in range(0, len(answers)):
                type = answers[answer_index]['Type']
                if type == 'CNAME' or type == 'A':
                    sum_final_time += time
                    num_of_finals += 1
            sum_total_time += time
        total_times.append(sum_total_time)
        final_times.append(sum_final_time)
    sorted_total_times = sorted(total_times)
    sorted_final_times = sorted(final_times)
    total_y_values = []
    final_y_values = []
    for x_value in sorted_total_times:
        temp = float(sorted_total_times.index(x_value) + 1) / float(len(sorted_total_times))
        total_y_values.append(temp)
    plot.plot(sorted_total_times, total_y_values, label="Total Times")
    for x_value in sorted_final_times:
        temp = float(sorted_final_times.index(x_value) + 1) / float(len(sorted_final_times))
        final_y_values.append(temp)
    plot.plot(sorted_final_times, final_y_values, label="Final Times")
    plot.legend(loc=4)  # This shows the legend on the plot.
    plot.grid()  # Show grid lines, which makes the plot easier to read.
    plot.xlabel("Seconds")  # Label the x-axis.
    plot.ylabel("Cumulative Fraction")  # Label the y-axis.
    plot.xscale('log')
    plot.title("Alexa Top 100 Times CDF")
    plot.savefig(output_filename)


"""
This function should take the name of two files that
each contain json dig output. The idea of this function is to count the number of changes that occur between
the terminating entries (A or CNAME records for the hostname) in the two sets of dig runs in the two different
filenames. The function should return a list of two values.
"""


def count_different_dns_responses(filename1, filename2):
    f1 = open(filename1, 'r')
    f2 = open(filename2, 'r')
    f1_parsed_json = json.loads(f1.read())
    f2_parsed_json = json.loads(f2.read())
    response = count_differences_helper(f1_parsed_json, {})
    name_to_diff = response[0]
    f1_query_differences = response[1]
    name_to_set1 = response[2]
    response2 = count_differences_helper(f2_parsed_json, name_to_set1)
    name_to_diff2 = response2[0]
    f2_query_differences = response2[1]
    for name in name_to_diff2.keys():
        if name in name_to_diff:
            if name_to_diff[name] == 1 and name_to_diff2[name] == 1:
                f2_query_differences -= 1
    return [f1_query_differences, f1_query_differences + f2_query_differences]


def count_differences_helper(f_parsed_json, past_diff):
    f_query_differences = 0
    s1 = set()
    other_set = set()
    name_to_diff = {}
    curr_name = ""
    first_pass = True
    name_to_set = {}
    seen_diff = False
    for name_index in range(0, len(f_parsed_json)):
        name = f_parsed_json[name_index]['Name']
        if not curr_name == name:
            if curr_name != "" and not seen_diff:
                name_to_set[curr_name] = s1
            s1 = set()
            curr_name = name
            first_pass = True
            seen_diff = False
        if seen_diff:
            continue
        other_set = set()
        queries = f_parsed_json[name_index]['Queries']
        for query_index in range(0, len(queries)):
            answers = queries[query_index]['Answers']
            for answer_index in range(0, len(answers)):
                type = answers[answer_index]['Type']
                if type == 'CNAME' or type == 'A':
                    data = answers[answer_index]['Data']
                    if first_pass:
                        s1.add(data)
                    else:
                        other_set.add(data)
        if first_pass:
            first_pass = False
        else:
            if s1 != other_set:
                name_to_diff[curr_name] = 1
                f_query_differences += 1
                seen_diff = True
            elif curr_name in past_diff:
                if past_diff[curr_name] != s1:
                    name_to_diff[curr_name] = 1
                    f_query_differences += 1
                    seen_diff = True
    return [name_to_diff, f_query_differences, name_to_set]


if __name__ == "__main__":
    # run_dig("alexa_top_100", "dns_output_2.json")
    # print count_different_dns_responses("dns_output_1.json", "dns_output_2.json")
    # print count_different_dns_responses("dns_output_other_server.json", "dns_output_1.json")
    # get_average_ttls("test_result.json")
    # print get_average_times("test_result.json")
    # run_dig("alexa_top_100", "dns_output_other_server.json", "A ")
    # generate_time_cdfs("dns_output_1.json", "alexa_top_100_times.pdf")
    # run_dig("alexa_top_3", "etest.json", "201.93.174.242")
    pass
