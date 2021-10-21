from kubernetes import client

from pint import UnitRegistry

import sys

import re

import subprocess

import requests

import os

import collections

import glob

from kubernetes import client, config

from kubernetes.client.rest import ApiException

from pprint import pprint

 

##  Kubernetes login using service account token



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

node_state = v1.list_node(watch=False)

pod_state = v1.list_pod_for_all_namespaces(watch=False)



## Cleanup master-config configmap

cmap = client.V1ConfigMap()

cmap.metadata = client.V1ObjectMeta(name="master-config")

try:

    v1.delete_namespaced_config_map(name="master-config", namespace="censor-admin",body=cmap)

except:

    pass



## Create master-config configmap on censor-admin namespace

v1.create_namespaced_config_map(namespace="censor-admin",body=cmap)





## Patch configmap - The below functions patch_configmap_object & patch_configmaps will be called to update configmaps on each health-check step



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



## Step 1 , Check cluster node status and write the nodes that are not in "schedulable" status.



def node_state():

  node_state = v1.list_node(watch=False)

  c=[]

  e=[]



  for i in node_state.items:

      a="%s" % (i.spec.unschedulable)

      if a == 'True' :

          b="%s" % (i.metadata.name)

          e.append(b)

      else:

          d="%s" % (i.metadata.name)

          c.append(d)



  failed_nodes=len(e)

  if failed_nodes == 0 :

      D={'master-node-status':'success'} 

      configmap = patch_configmap_object(D)

      patch_configmap(v1, configmap)

  else :

      D={'master-node-fail':'%s' % (e)}

      configmap = patch_configmap_object(D)

      patch_configmap(v1, configmap)





## Step 2, Check status of platform pods and write the pods that are NOT in either 'completed' or 'Running' status



def platform_pod():

  pod_state = v1.list_pod_for_all_namespaces(watch=False)

  platform_ns=['default','kube-system','openshift-console','openshift-infra','openshift-logging','openshift-metrics-server','openshift-monitoring','openshift-node','openshift-sdn','openshift-web-console','splunk-connect-001','ccw-dev-001']

  failure_pods=[]

  success_pods=[]

  for i in pod_state.items:

    ns="%s" % (i.metadata.namespace)

    pod_state="%s" % (i.status.phase)

    pod_name="%s" % (i.metadata.name)

    if ((ns in platform_ns) and (pod_state!='Running') and (pod_state!='Succeeded')):

      pod_ns='Namespace-'+ns+':'+'Podname-'+pod_name

      failure_pods.append(pod_ns)

    else:

      success_pods.append(pod_name)

  failed_pods=len(failure_pods)   

  if failed_pods == 0 :

    D={'master-platformpod-status':'success'}

    configmap = patch_configmap_object(D)

    patch_configmap(v1, configmap)

  else :

    D={'master-platformpod-fail':'%s' % (failure_pods)}

    configmap = patch_configmap_object(D)

    patch_configmap(v1, configmap)


def platform_routes():

  routes=['console','docker-registry-default','registry-console-default','hawkular-metrics','kibana','alertmanager-main-openshift-monitoring','grafana-openshift-monitoring','grafana-custom-openshift-monitoring','prometheus-k8s-openshift-monitoring']

  cmd='cat /etc/etc/origin/master/master-config.yaml  | grep subdomain | awk -F: \'{print$2}\' | awk \'{$1=$1;print}\''

  wildcard=subprocess.check_output(cmd,shell=True)



  b=wildcard.split('\n')



  b=filter(None,b)



  mystring=b[0]



  mystring='.'+mystring

  failed_routes=''

  pass_routes=''



  new_array=[s + mystring for s in routes]

  for i in new_array:

    try: 

      response= requests.get("https://%s" % (i),verify=False)

      status= response.status_code

      if status == 200 or status == 403:

          pass_routes="%s : %s" % (i,status)

      else:

          failed_routes+="%s:%s " % (i,status)  

    except:

      pass

  fail_list=failed_routes.split(" ")

  fail_list.pop()

  if fail_list:

      D={'master-platform-routes-fail':'%s' % (fail_list)} 

      configmap = patch_configmap_object(D)

      patch_configmap(v1, configmap)

  else:

      D={'master-platform-routes':'success'}

      configmap = patch_configmap_object(D)

      patch_configmap(v1, configmap)

