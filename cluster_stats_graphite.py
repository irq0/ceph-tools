#!/usr/bin/env python

"""
Print Ceph cluster stats in graphite format
"""

import os
import time
import json
import re
import rados

from ceph_argparse import json_command

def ceph_get_pg_stats(rados_handle):
    """
    Wrapper for Ceph 'pg stat' json command
    """
    ret, j, _ = json_command(rados_handle, prefix="pg stat",
                           argdict={'format':'json'})

    if ret == 0:
        return json.loads(j)

def pg_stats(rados_handle):
    """
    Return cluster pg stats
    """

    # see PGMap.cc/PGMonitor.cc
    interesting_stats_keys = (
        # standard stats
        "read_bytes_sec",
        "write_bytes_sec",
        "io_sec",
        "raw_bytes",
        "raw_bytes_avail",
        "raw_bytes_used",
        "num_bytes",
        "num_pgs",
        # recovery rate summary
        "recovering_objects_per_sec",
        "recovering_bytes_per_sec",
        "recovering_keys_per_sec",
        "num_objects_recovered",
        "num_bytes_recovered",
        "num_keys_recovered",
        # recovery_summary
        "unfound_objects",
        "unfound_total",
        "unfound_ratio",
        "misplaced_objects",
        "misplaced_total",
        "misplaced_ratio",
        "degraded_objects",
        "degraded_total",
        "degraded_ratio",
    )

    data = ceph_get_pg_stats(rados_handle)

    if data:
        metrics = [("pgstat.{}".format(k), data.get(k, 0))
                   for k in interesting_stats_keys]

        pg_by_state = [("pg_by_state.{}".format(x["name"]), x["num"])
                       for x in data["num_pg_by_state"]]
        metrics.extend(pg_by_state)

        return metrics

def sanitize_name(name):
    """
    Remove chars that don't work well in Graphite metric names
    """
    return re.sub(r"[^\w]", "_", name)

def rados_stat(rados_handle):
    """
    Return stats from RADOS API (pool and cluster)
    """
    pools = rados_handle.list_pools()

    cluster_stats = rados_handle.get_cluster_stats()

    metrics = [("cluster.{}".format(sanitize_name(k)), v)
               for k, v in cluster_stats.iteritems()]

    for pool in pools:
        io_ctx = rados_handle.open_ioctx(pool)
        pool_stat = [("pool.{}.{}".format(sanitize_name(pool),
                                          sanitize_name(k)), v)
                     for k, v in io_ctx.get_stats().iteritems()]

        metrics.extend(pool_stat)
        io_ctx.close()

    return metrics

def print_graphite(data, now, prefix):
    """
    Print data in sequence in graphite format
    """
    for key, val in data:
        print "{}.{}".format(prefix, key), val, now

def setup():
    conf = os.environ.get("CEPH_CONF", "/etc/ceph/ceph.conf")
    name = os.environ.get("CEPH_NAME", "client.admin")

    rados_handle = rados.Rados(conffile=conf,
                               name=name)
    rados_handle.connect()
    return rados_handle

def main():
    rados_handle = setup()

    print_graphite(pg_stats(rados_handle), int(time.time()), "ceph.cluster")
    print_graphite(rados_stat(rados_handle), int(time.time()), "ceph.cluster")

if __name__ == "__main__":
    main()
