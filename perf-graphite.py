#!/usr/bin/env python

import sys
import argparse
import json
import time

from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('path_prefix', type=str)
parser.add_argument('dump_file', type=argparse.FileType('r'))
args = parser.parse_args()

dump = json.load(args.dump_file)
ts = int(time.time())

out_format = "ceph.{}.{{}} {{}} {}".format(args.path_prefix, ts)

def mt(x):
    if isinstance(x, dict):
        return x.iteritems()
    else:
        return (("count", x),)

data = ( (".".join((group, metric_name, metric_type)), metric_value)
         for group, metrics in dump.iteritems()
         for metric_name, metric in metrics.iteritems()
         for metric_type, metric_value in mt(metric)
)

print "\n".join((out_format.format(path, value) for path, value in data))
