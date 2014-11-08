#!/bin/bash

readonly SCRIPTPATH="$(dirname "$0")"

readonly PREFIX="vstart-$(hostname)"
readonly MON_ASOKS=(mon.a.asok
		    mon.b.asok
		    mon.c.asok)
readonly OSD_ASOKS=(osd.0.asok
		    osd.1.asok
		    osd.2.asok)

for asok in ${MON_ASOKS[@]}; do
    $SCRIPTPATH/perf-graphite.py "${PREFIX}.${asok%*.asok}" <(ceph --admin-daemon "$asok" perfcounters_dump)
done
for asok in ${OSD_ASOKS[@]}; do
    $SCRIPTPATH/perf-graphite.py "${PREFIX}.${asok%*.asok}" <(ceph --admin-daemon "$asok" perf dump)
done
