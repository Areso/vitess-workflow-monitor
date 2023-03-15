# Vitess-workflow-monitor  
![demo.png](demo.png)
Small application to track workflow status Linux/GNOME/GTK  
Green icon shows replication in Copying/Running  
Red icon shows replication in Error state  
Also, by click, you could see TPS (transaction per second) rate of applying binlogs  
Show stats in `shard: TPS` format.  
## Install requirements
`sudo pip3 install -r requirements.txt`  
## To start:  
`python3 moveworkflowmon.py`  
or  
`python3 moveworkflowmon.py --workflow testdb.move2vitess`,  
where `testdb` is a keyspace name and `move2vitess` is workflow name