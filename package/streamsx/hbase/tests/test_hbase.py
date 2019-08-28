# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import streamsx.hbase as hbase

from streamsx.topology.topology import streamsx, Topology
from streamsx.topology.tester import Tester
from streamsx.topology.schema import StreamSchema
import streamsx.spl.toolkit as tk

import unittest
import os
from datetime import time

##
## Test assumptions
## Before you start with test make sure that:
##
## - IBM Streams instance running
## - HBASE server running 
## - The hostname and the port of HBASE server is referenced by HADOOP_HOST_PORT environment variable.
## - Or the "core-site.xml" is referenced by HBASE_SITE_XML environment variable.
## - HBASE toolkit location is given by STREAMS_HBASE_TOOLKIT environment variable.
## - A table 'streamsSample_lotr' is exsit on your HBASE database.
##    echo "create 'streamsSample_lotr','appearance','location'" | hbase shell
##

def toolkit_env_var():
    result = True
    try:
        os.environ['STREAMS_HBASE_TOOLKIT']
    except KeyError: 
        result = False
    return result

def streams_install_env_var():
    result = True
    try:
        os.environ['STREAMS_INSTALL']
    except KeyError: 
        result = False
    return result

def site_xml_env_var():
    result = True
    try:
        os.environ['HBASE_SITE_XML']
    except KeyError: 
        result = False
    return result

def hadoop_host_port_env_var():
    result = True
    try:
        os.environ['HADOOP_HOST_PORT']
    except KeyError: 
        result = False
#        print ("Missing HADOOP_HOST_PORT environment variable.")
    return result

def cloud_creds_env_var():
    result = True
    try:
        os.environ['ANALYTICS_ENGINE']
    except KeyError: 
        result = False
    return result

def _create_stream_for_get(topo):
    s = topo.source([1,2,3,4,5,6])
    schema=StreamSchema('tuple<int32 id, rstring who, rstring infoType, rstring requestedDetail>').as_tuple()
    return s.map(lambda x : (x,'Gandalf', 'location','beginTwoTowers'), schema=schema)


def _create_stream_for_put(topo):
    s = topo.source([1,2,3,4,5,6])
    schema=StreamSchema('tuple<int32 id, rstring character, rstring colF, rstring colQ, rstring value>').as_tuple()
    return s.map(lambda x : (x,'Gandalf', 'location','beginTwoTowers', 'travelling'), schema=schema)

def _get_table_name():
    tableName = 'streamsSample_lotr'
    return tableName


class StringData(object):
    def __init__(self, who, count, delay=True):
        self.who = who
        self.count = count
        self.delay = delay
    def __call__(self):
        if self.delay:
            time.sleep(10)
        for i in range(self.count):
            yield self.who



class TestParams(unittest.TestCase):

    def test_hadoop_host_port(self):
        topo = Topology()
        hbase.scan(topo, table_name=_get_table_name(), max_versions=3)
        s = _create_stream_for_get(topo) 
        hbase.get(s, table_name=_get_table_name(), row_attr_name='who')



class TestDistributed(unittest.TestCase):
    """ Test in local Streams instance with local toolkit from STREAMS_HBASE_TOOLKIT environment variable """

    @classmethod
    def setUpClass(self):
        print (str(self))

    def setUp(self):
        Tester.setup_distributed(self)
        self.hbase_toolkit_location = os.environ['STREAMS_HBASE_TOOLKIT']

    # -----------------------------------------------------------
    def test_hbase_put(self):
        topo = Topology('test_hbase_put')

        if self.hbase_toolkit_location is not None:
            tk.add_toolkit(topo, self.hbase_toolkit_location)

        s = _create_stream_for_put(topo) 
        tester = Tester(topo)
        # hbase.put creates site.xml file with the use of environment variable HADOOP_HOST_PORT / HBASE_SITE_XML
        get_rows = hbase.put(s, table_name=_get_table_name())
        get_rows.print()

        tester.tuple_count(get_rows, 2, exact=False)
        # tester.run_for(60)

        cfg = {}
        job_config = streamsx.topology.context.JobConfig(tracing='info')
        job_config.add(cfg)
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False     
        # Run the test
        tester.test(self.test_ctxtype, cfg, always_collect_logs=True)

 
    # -----------------------------------------------------------
    def test_hbase_get(self):
        topo = Topology('test_hbase_get')

        if self.hbase_toolkit_location is not None:
            tk.add_toolkit(topo, self.hbase_toolkit_location)

        s = _create_stream_for_get(topo) 
        tester = Tester(topo)
        # hbase.get creates site.xml file with the use of environment variable HADOOP_HOST_PORT / HBASE_SITE_XML
        get_rows = hbase.get(s, table_name=_get_table_name(), row_attr_name='who')
        get_rows.print()

        tester.tuple_count(get_rows, 2, exact=False)
        # tester.run_for(60)

        cfg = {}
        job_config = streamsx.topology.context.JobConfig(tracing='info')
        job_config.add(cfg)
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False     
        # Run the test
        tester.test(self.test_ctxtype, cfg, always_collect_logs=True)


    # --------------------------------------------------------
    def test_hbase_scan(self):
        topo = Topology('test_hbase_scan')

        if self.hbase_toolkit_location is not None:
            tk.add_toolkit(topo, self.hbase_toolkit_location)
 
        tester = Tester(topo)
        # hbase.scan creates site.xml file with the use of environment variable HADOOP_HOST_PORT / HBASE_SITE_XML
        scanned_rows = hbase.scan(topo, table_name=_get_table_name(), max_versions=1 , init_delay=2)
        scanned_rows.print()
        tester.tuple_count(scanned_rows, 2, exact=False)

        cfg = {}
        job_config = streamsx.topology.context.JobConfig(tracing='info')
        job_config.add(cfg)
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False     

        # Run the test
        tester.test(self.test_ctxtype, cfg, always_collect_logs=True)

    # --------------------------------------------------------
    @unittest.skipIf(((site_xml_env_var()))== False, "Missing HBASE_SITE_XML")
    def test_hbase_scan_connection_param_file(self):
        topo = Topology('test_hbase_scan_connection_param_file')

        if self.hbase_toolkit_location is not None:
            tk.add_toolkit(topo, self.hbase_toolkit_location)
 
        tester = Tester(topo)
        # set HBASE_SITE_XML file as connection parameter
        scanned_rows = hbase.scan(topo, table_name=_get_table_name(), max_versions=1 , init_delay=2, connection=os.environ['HBASE_SITE_XML'])
        scanned_rows.print()
        tester.tuple_count(scanned_rows, 2, exact=False)

        cfg = {}
        job_config = streamsx.topology.context.JobConfig(tracing='info')
        job_config.add(cfg)
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False     

        # Run the test
        tester.test(self.test_ctxtype, cfg, always_collect_logs=True)


    # --------------------------------------------------------
    @unittest.skipIf(((hadoop_host_port_env_var()))== False, "Missing HADOOP_HOST_PORT")
    def test_hbase_scan_connection_param_string(self):
        topo = Topology('test_hbase_scan_connection_param_string')

        if self.hbase_toolkit_location is not None:
            tk.add_toolkit(topo, self.hbase_toolkit_location)
 
        tester = Tester(topo)
        # set HADOOP_HOST_PORT string as connection parameter
        scanned_rows = hbase.scan(topo, table_name=_get_table_name(), max_versions=1 , init_delay=2, connection=os.environ['HADOOP_HOST_PORT'])
        scanned_rows.print()
        tester.tuple_count(scanned_rows, 2, exact=False)

        cfg = {}
        job_config = streamsx.topology.context.JobConfig(tracing='info')
        job_config.add(cfg)
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False     

        # Run the test
        tester.test(self.test_ctxtype, cfg, always_collect_logs=True)

    # --------------------------------------------------------
    @unittest.skipIf(((hadoop_host_port_env_var()))== False, "Missing HADOOP_HOST_PORT")
    def test_hbase_scan_connection_param_dict(self):
        topo = Topology('test_hbase_scan_connection_param_dict')

        if self.hbase_toolkit_location is not None:
            tk.add_toolkit(topo, self.hbase_toolkit_location)
 
        tester = Tester(topo)
        # set dict as connection parameter with values from HADOOP_HOST_PORT
        hp = os.environ['HADOOP_HOST_PORT'].split(":", 1)
        ext_connection = {}
        ext_connection['host'] = hp[0]
        ext_connection['port'] = hp[1]
        scanned_rows = hbase.scan(topo, table_name=_get_table_name(), max_versions=1 , init_delay=2, connection=ext_connection)
        scanned_rows.print()
        tester.tuple_count(scanned_rows, 2, exact=False)

        cfg = {}
        job_config = streamsx.topology.context.JobConfig(tracing='info')
        job_config.add(cfg)
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False     

        # Run the test
        tester.test(self.test_ctxtype, cfg, always_collect_logs=True)


class TestICPRemote(TestDistributed):
    def setUp(self):
        Tester.setup_distributed(self)
        self.hbase_toolkit_location = None

