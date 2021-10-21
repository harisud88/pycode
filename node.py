#!/bin/python



## To be executed on all kubernetes cluster nodes as daemonset - Part of the kubernetes cluster health check 

##

## It needs configmap "master-config" to be available on censor-admin namespace - This configmap is created as part of master script execution 

##

## Update configmap "master-config" with below information

##

##             1 Node connectivity to Nexus 

##             2 Node connectivity to proxy

##             3 CPU load on node

##             4 Memory bottleneck on node

##             5 Node restarts in last 24 hours

##             6 Kubernetes filesystem usage on node

##             7 Kernel version of node

##             8 Systemd services related to kubernetes 

##



import sys

import platform

import telnetlib

import socket

import re

import subprocess

import requests

import os

import collections

import glob

from kubernetes import client, config

from kubernetes.client.rest import ApiException

from pprint import pprint



## Login kubernetes with service account token



filename='/run/secrets/kubernetes.io/serviceaccount/token'

s = open(filename, 'r').read()



b=s.split('\n')



token=b[0]



configuration = client.Configuration()

configuration.api_key["authorization"] = token

configuration.api_key_prefix['authorization'] = 'Bearer'

configuration.host = 'https://kubernetes.default.svc:443'

configuration.ssl_ca_cert = '/run/secrets/kubernetes.io/serviceaccount/ca.crt'

v1 = client.CoreV1Api(client.ApiClient(configuration))





sys.path.insert(0, '/tmp/master-config')



## Import proxy and Nexus port information from master-config configmap

from nexusports import ports

from proxy import proxy



## Get nodes' hostname

host = os.getenv('HOST_NAME')

 

## Write configmap



def patch_configmap_object(D):

    # Get File Content

    # Instantiate the configmap object

    configmap = client.V1ConfigMap(

        api_version="v1",

        kind="ConfigMap",

        data=D,

    )



    return configmap



def patch_configmap(v1, configmap):

    try:

        api_response = v1.patch_namespaced_config_map(

            namespace="censor-admin",

            body=configmap,

            name='master-config',

            pretty = 'pretty_example',

        )

        pprint(api_response)



    except ApiException as e:

        print("Exception when calling CoreV1Api->patch_namespaced_config_map: %s\n" % e)



## Step 1 , Check connectivity to nexus ports from cluster node



def check_nexus_connection():



    pass_test=''

    fail_test=''

    for i in ports:

        try:

            TNT = telnetlib.Telnet("regis.censor.com", i,2)

            response = 'Success'

        except IOError:

            response = 'Failure'

        if response is 'Success':

            pass_test="%s:%s " % (host,i)

        else:

            fail_test+="%s " % (i)

    fail_list=fail_test.split(" ")

    fail_list.pop()

    if fail_list:

        nexus_fail="nexusfail-host-and-port:%s:%s" % (host,fail_list)

        D={'nexus-fail-%s' % (host):'%s' % (nexus_fail)} 

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap) 

    else:

        D={'nexus-success-%s' % (host):'success'} 

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)



## Step 2 , Check connectivity to proxy from cluster node



def check_proxy_connection():

    fail_list=''

    proxy_host=proxy.split(":")[0]

    proxy_port=proxy.split(":")[1]

    try:

        TNT = telnetlib.Telnet(proxy_host,proxy_port,2)

        response = 'Success'

    except IOError:

        response = 'Failure'

    if response is 'Success':

        D={'proxy-success-%s' % (host):'success'} 

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)

    else:

        fail_list="proxyfailure on host %s:%s:%s" % (host,proxy_host,proxy_port)

        D={'proxy-fail-%s' % (host):'%s' % (fail_list)} 

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)



## Step 3 , Check if there any cpu bottleneck - High load if "load average value is greater than number of CPU"



def check_cpu():

    cpu_count=subprocess.check_output(['nproc'])

    cpu_count=cpu_count[:-1]

    load=subprocess.check_output(['cat', '/proc/loadavg'])

    load_avg=load.split(" ")[0]

    if int(float(load_avg)) > int(cpu_count):

        cpumsg="cpuload %s on %s " % (load_avg,host)

        D={'cpu-load-%s' % (host):'%s' % (cpumsg)}

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)

    else:

        D={'cpu-normal-%s' % (host):'success'}

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)



## Step 4 , Check for memory bottleneck , Alerts if available memory is lesser than 1 GB



def check_mem():

    mem_cmd='cat /proc/meminfo | grep -i MemAvailable | awk -F: \'{print$2}\' | awk -FkB \'{print$1}\' | sed \'s/ //g\''

    mem=subprocess.check_output(mem_cmd,shell=True) 

    mem=mem[:-1]

    mem_total_cmd='cat /proc/meminfo | grep -i MemTotal | awk -F: \'{print$2}\' | awk -FkB \'{print$1}\' | sed \'s/ //g\''

    mem_total=subprocess.check_output(mem_total_cmd,shell=True)

    mem_total=mem_total[:-1]

    mem_use=int(mem_total)-int(mem)

    file="/tmp/health/nodeh-%s" % host

    D={'availablememory-%s' % (host):'%s-%s' %(mem_use,mem_total)}

    configmap = patch_configmap_object(D)

    patch_configmap(v1, configmap)

    if len(mem) <= 6:

        memmsg="Highmemory Alert - Available memory is less than 1 GB on %s" % (host)

        D={'memory-load-%s' % (host):'%s' % (memmsg)}

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap) 

    else:

        D={'memory-normal-%s' % (host):'success'}

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)





## Step 5 , Write kernel versions of the nodes



def check_kernel():

    kernel=platform.release()

    msg="Kernel:%s:%s" % (host,kernel)

    D={'kernel-%s' % (host):'%s' % (msg)}

    configmap = patch_configmap_object(D)

    patch_configmap(v1, configmap)



## Step 6 , Checks if the node restarted in last 24 hours



def check_restart():

    cmd='uptime | awk \'{print$4}\' | cut -c 1-3'

    uptime=subprocess.check_output(cmd,shell=True)

    uptime=uptime.split("\n")[0]

    if uptime != 'day':

        msg="Uptime:%s" % (host)

        D={'node-restart-%s' % (host):'%s' % (msg)}

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)



## Step 7 , Check systemd services related to kubernetes on node



def check_systemd():

  services=['iptables.service','tuned.service','atomic-openshift-node.service','docker.service']

  fail_list=''

  fail_item=''

  for i in services:

    path='/tmp/sys/systemd/system.slice/%s' % i

    isfile=os.path.isdir(path)

    if not isfile:

      fail_item+="srvcfail:%s:%s " % (host,i)

  fail_list=fail_item.split(" ")

  fail_list.pop()

  if fail_list:

    D={'service-fail-%s' % (host):'%s' % (fail_list)}

    configmap = patch_configmap_object(D)

    patch_configmap(v1, configmap)



## Step 8 , Check if the kubernetes file-systems has reached 80% of capacity



def check_fs():

    threshold=int(80)

    fail_list=''

    fail_item=''

    fs=['/etc/etc','/var/lib/origin','/var/lib/docker']

    for i in fs:

        cmd = 'df -h %s | awk \'{print$5}\' | tail -1' % (i)

        out=subprocess.check_output(cmd,shell=True)

        out1=int(out[:-2])

        if out1 > threshold:

            fail_item+="fsusage %s:%s:%s " % (host,i,out1) 

    fail_list=fail_item.split(" ")   

    fail_list.pop()

    if fail_list:

        D={'fs-fail-%s' % (host):'%s' % (fail_list)}

        configmap = patch_configmap_object(D)

        patch_configmap(v1, configmap)







check_nexus_connection()

check_proxy_connection()

check_cpu()

check_mem()

check_kernel()

check_restart()

check_systemd()

check_fs()



## Below sleep command is to prevent the pods going to crashloop backoff state after script execution until the daemonset is removed by main script



cmd='sleep 360'

i=subprocess.check_output(cmd,shell=True)
