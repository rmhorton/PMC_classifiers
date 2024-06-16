#!/home/rmhorton/anaconda3/envs/nlp/bin/python

import sys
import re
import argparse
import pandas as pd

parser = argparse.ArgumentParser(
    description='Repair CSV files that have linefeeds in the text field.',
    epilog='''
    Example: 
	# find /data/pmc_tables/PMC003xxxxxx/ -name '*.csv' | xargs tail -q -n +2 | ./repair_csv.py --mode test
	find /data/pmc_tables/PMC003xxxxxx/ -name '*.csv' | xargs -I{} ./repair_csv.py {} --mode test

	echo '/data/pmc_tables/PMC003xxxxxx/PMC003xxxxxx_PMC3018417.csv' | xargs -I{} ./repair_csv.py {} --mode test
'''
)
parser.add_argument("input_file")
parser.add_argument("--mode", help="test or repair", choices=['test', 'repair'], default='test')
args = parser.parse_args()

if args.mode == 'test':
	try:
		df=pd.read_csv(args.input_file)
	except:
		print(f"Could not read file '{args.input_file}'")
else:
	print("repair mode not implemented.")

# sys.exit(f"Thank you for submitting '{args.input_file}'")

# with open(args.input_file, 'rt', encoding='utf8') as in_fh:
#	prev_line = ''
#	i = 0
#	for line in in_fh.readlines():  # sys.stdin:
#		if i == 0: # skip the first line (header)
#			i = 1
#			continue
#		line = line.rstrip()
#		if re.match(r"^\d{7}", line):
#			if args.mode=='repair': 
#				print(prev_line)
#			prev_line = line
#		else:
#			if args.mode != 'repair':
#				print("MALFORMED LINE:", line)
#
#			prev_line = prev_line + '<br/>' + line
#
#	if args.mode=='repair': 
#		print(prev_line)


