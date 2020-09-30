# Resurrection of GPC preemtive instances

Automatically restart GPC preemtive instances once they are preemted.

We adapted the original version to work with GPC pub/sub:
Original version: https://github.com/itamaro/gcp-night-king

## Overview

The setup consits of several parts.
1) You need a startup script on your instance that resumes your data processing at the point it was interrupted before preemption
2) The preemt_signal.sh code needs to be added to your instance as instance metadata. 
3) You need to create a pub/sub topic to route the preemtion signal
4) You need to create a cloud function with the cloud_function.py code which will restart the instance

## 1 - your instance startup script

This is the only part we cannot provide you given that it totally depends on your data :-)

As a general rule the overall setup will only work when you have data processing of several small chunks that take a few seconds to minutes. When the processing of one junk need several hours chances are very high that the instance will be preemted before you can even process one chunk.

A few notes that might help:
- Make sure to mount any cloud disk you need via UUID - that spares you a lot of trouble

- Add a system.d service that executes your data processing script and make sure to set the correct permissions for the service file and your script
(example: https://linuxconfig.org/how-to-run-script-on-startup-on-ubuntu-20-04-focal-fossa-server-desktop)
For the example service in this repository you need to make sure to set your working dir correctly and keep all paths in there...

- Load your service:
$ sudo systemctl daemon-reload
$ sudo systemctl enable YOUR_SERVICE.service


## 2 - Process the preemtion signal via shutdown script

We assume you have a GPC preemtive instance ready to work with (not covering here how to get this up and running)

Adding the shutdown script is as easy as adding the code as metadata. (Either when creating the instance or click on "Edit" for the instance)

The KEY for the metadata entry is 'shutdown-script' and for the value just copy and paste the preemt_signal.sh code from this repository into the value field.

The script assumes that you will later name the pub/sub topic 'prere' - in case you want to change this you have to adapt the code in the TOPIC line.

Whenever a preemption signal is sent to the instance this script will send the information to the pubsub topic. 

#### You have to make sure that your instance has the permission to publish to the PUB/SUB service otherwise this will not work!

## 3 - Create a pub/sub topic that will trigger your restart script

Go to the PUB/SUB page in your console (https://console.cloud.google.com/cloudpubsub) and create a new topic called 'prere'

Thats it - nice and easy

## 4 - Create a restart script that is triggered by your pub/sub topic

Go to the Cloud Functions page in your console (https://console.cloud.google.com/functions) and create a new function:

a) The function needs to be in the same region as your other setup (preemtive instance etc.)
b) As a trigger choose your 'prere' PUB/SUB topic

c) In the code section copy and paste the code from 'cloud_function.py' in this repository into the main.py file of your function
d) In the code section copy and paste the code from 'cloud_function_requirements.txt' in this repository to the requirements.txt file of your function


## DONE 

You should now be able to startup your machine. It will start crunching your data. Whenever it is preemted it automatically restarts.

NOTE: When you manually shutdown the machine it will NOT restart - that is filtered out in the code.


