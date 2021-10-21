FROM regis.censor.com:7994/eve-rhel7:v1.0.4

USER root

RUN mkdir -p /go/src/app

WORKDIR /go/src/app

COPY . /go/src/app

EXPOSE 10000 

CMD ["./app"]



#!/bin/python



##  Last step of kubernetes health check - To be executed as kubernetes job on a App node

##

##  This script updates the html file on /tmp/stathc with the informtion from configmap master-config and then sends the file as Email to CHS



import subprocess

import glob

from email.mime.text import MIMEText

import smtplib

from os import path



html_file='/tmp/stathc'



url_cmd='cat /tmp/master-config/master-url'

url_name=subprocess.check_output(url_cmd,shell=True)

url_name=url_name.strip('\n')



## Copy stathc html file to /tmp

cmd='cp /app/stathc /tmp/'

a=subprocess.check_output(cmd,shell=True)



## Function to update html template



def find_replace(string,replace):

    with open(html_file, 'r') as file :

      filedata = file.read()



    # Replace the target string

    filedata = filedata.replace(string,replace)



    # Write the file out again

    with open(html_file, 'w') as file:

      file.write(filedata)







def version():



    cmd='cat /tmp/master-config/master-version'

    a=subprocess.check_output(cmd,shell=True)

    a=a.strip('\n')

    find_replace('vershc',replace=a)



def url():

    cmd='cat /tmp/master-config/master-url'

    cluster_name=subprocess.check_output(cmd,shell=True)

    cluster_name=cluster_name.strip('\n')

    find_replace('clushc',replace=cluster_name)



def etcd():

    if path.exists("/tmp/master-config/master-etcd-success"):

        find_replace('etchc','&#9989')

    else:

        find_replace('etchc','&#10060')

   

def cpu():

    if glob.glob('/tmp/master-config/cpu-load*'):

        find_replace('cpuhc','&#10060')

        cmd1='echo "<h3><b>Nodes with high CPU usage</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/cpu-load* >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('cpuhc','&#9989')



def memory():

    if glob.glob('/tmp/master-config/memory-load*'):

        find_replace('memhc','&#10060')

        cmd1='echo "<h3><b>Nodes with high memory usage</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/memory-load* >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('memhc','&#9989')





def check_pending_csr():

   if path.exists("/tmp/master-config/master-pendingcsr-fail"):

       find_replace('csrhc','&#10060')

   else:

       find_replace('csrhc','&#9989')





def proxy_check():

    if glob.glob('/tmp/master-config/proxy-fail*'):

        find_replace('proxyhc','&#10060')

        cmd1='echo "<h3><b>Nodes with proxy connect fail</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='grep proxyfail /tmp/master-config/* | awk -F: \'{print$2":"$3":"$4}\' | while read line; do echo "<br>$line";done  >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('proxyhc','&#9989')





def nexus_check():

    if glob.glob('/tmp/master-config/nexus-fail*'):

        find_replace('nexushc','&#10060')

        cmd1='echo "<h3><b>Nodes with Nexus connect fail</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='grep nexusfail /tmp/master-config/* | awk -F: \'{print$2":"$3":"$4}\' | while read line; do echo "<br>$line";done  >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('nexushc','&#9989')



def check_fs():

    if glob.glob('/tmp/master-config/fs-fail*'):

        find_replace('fshc','&#10060')

        cmd1='echo "<h3><b>Nodes with ocp file-system breach threshold</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/fs-fail* >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('fshc','&#9989') 



def platform_pods():

    if glob.glob('/tmp/master-config/master-platformpod-fail'):

        find_replace('ppodhc','&#10060')

        cmd1='echo "<h3><b>Below Platform Pods are in error state</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/master-platformpod-fail | tr "," "\n" >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('ppodhc','&#9989') 

      

def app_pods():

    if glob.glob('/tmp/master-config/master-apppod-fail'):

        find_replace('apodhc','&#10060')

        cmd1='echo "<h3><b>Below Application Pods are in error state</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd2='for i in `cat /tmp/master-config/master-apppod-fail | tr "," "\n"` ; do echo "<br>$i";done >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd2,shell=True)

    else:

        find_replace('apodhc','&#9989')



def platform_routes():

    if glob.glob('/tmp/master-config/master-platform-routes-fail'):

        find_replace('routehc','&#10060')

        cmd1='echo "<h3><b>Received incorrect HTTP response from below platform routes</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/master-platformpod-fail | tr "," "\n" >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('routehc','&#9989')

    

def node_status():

    if glob.glob('/tmp/master-config/master-node-fail'):

        find_replace('nodehc','&#10060')

        cmd1='echo "<h3><b>Below Nodes are not on ready status</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/master-node-fail >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('nodehc','&#9989')



def systemd():

    if glob.glob('/tmp/master-config/service-fail*'):

        find_replace('systemdhc','&#10060')

        cmd1='echo "<h3><b>Below systemd services are not running</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/service-fail* >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('systemdhc','&#9989')

    

    

def kernel():

    cmd='grep Kernel /tmp/master-config/* | awk -F: \'{print$4}\' | uniq | wc -l'

    a=subprocess.check_output(cmd,shell=True)

    a=a.strip("\n") 

    if int(a) != 1:

        find_replace('kernelhc','&#10060')

        cmd1='echo "<h3><b>Please investigate - some of the cluster nodes are running on different kernel version</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd2='grep Kernel /tmp/master-config/* | awk -F: \'{print$3":"$4}\' >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd2,shell=True)

    else:   

        find_replace('kernelhc','&#9989')

            

def node_restart():

    if glob.glob('/tmp/master-config/node-restart*'):

        find_replace('uptimehc','&#10060')

        cmd1='echo "<h3><b>FYI - Below nodes restarted within last 24 hours</b></h3>" >>/tmp/stathc'

        subprocess.check_output(cmd1,shell=True)

        cmd='cat /tmp/master-config/node-restart* >>/tmp/stathc ; echo -en \'\n\'  >>/tmp/stathc'

        subprocess.check_output(cmd,shell=True)

    else:

        find_replace('uptimehc','&#9989')







def node_capacity1():

    cmd = 'cat /tmp/master-config/master-Nodememcap'

    out=subprocess.check_output(cmd,shell=True)

    memusage = out.split(':')

    a=memusage[0]

    a=a.strip('\n')

    if float(a) > 100:  

        find_replace('memreq','Yes')

    else:

        find_replace('memreq','No')

    if float(a) > 90:

        find_replace('mem1req','Yes')

    else:

        find_replace('mem1req','No')



def node_capacity2():

    cmd = 'cat /tmp/master-config/master-Nodecpucap'

    out=subprocess.check_output(cmd,shell=True)

    cpuusage = out.split(':')

    a=cpuusage[0]

    a=a.strip('\n')

    if float(a) > 100:

        find_replace('cpureq','Yes')

    else:

        find_replace('cpureq','No')

    if float(a) > 90:

        find_replace('cpu1req','Yes')

    else:

        find_replace('cpu1req','No')



def send_email():

    fromaddr = "CaaS@censor.com"

    toaddr = "containerengineeringdel@censor.com"

    file="/tmp/stathc"

    html = open("/tmp/stathc")

    msg = MIMEText(html.read(), 'html')

    msg['From'] = fromaddr

    msg['To'] = toaddr

    msg['Subject'] = 'Cluster Health Check - %s' % url_name

    s = smtplib.SMTP('svexgwa01.corp.censor.com:25')

    s.sendmail('caas@censor.com', ['containerengineeringdel@censor.com'], msg.as_string())

    



    



version()

url()

etcd()

platform_pods()

app_pods()

cpu()

memory()

check_pending_csr()

proxy_check()

nexus_check()

check_fs()

platform_routes()

node_status()

systemd()

kernel()

node_restart()

node_capacity1()

node_capacity2()

send_email()

