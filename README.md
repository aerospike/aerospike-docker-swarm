# aerospike-docker-swarm

Aerospike cluster template to use with Docker Swarm Mode (Docker v1.12+). This is not the same as Standalone Swarm (old Swarm).

# Requirements

* Docker Engine 1.13+ (due to Compose v3.2)


# Usage

```bash
docker stack deploy -c <compose yaml> <deployment name>  
eg:  
docker stack deploy -c aerospike.yml aerospike  
```

# Starting from scratch

## I don't have any docker hosts:
1. Install docker-machine via [Docker Toolbox](https://www.docker.com/products/docker-toolbox)
1. Create your VMs:  
    `$ docker-machine create --driver virtualbox node1`  
    `$ docker-machine create --driver virtualbox node2`
1. To ssh into each machine:
    `$ docker-machine ssh <machine name>`
	eg: `docker-machine ssh node1`
1. Continue below

## I already have my docker hosts running Docker 1.13+

1. Configure a docker node as Swarm Manager:  
    `docker@node1 docker swarm init --advertise-addr <swarm_advertise_ip>`  
    There should be a 192.168.99.0/24 subnet created just for inter-VM networking by docker-machine. Use this address for your `<swarm_advertise_ip>` 
1. Join other docker nodes as Swarm Workers:
    The previous command will output a command and token for every other docker node to use to join as Swarm Workers:
    ```
    Swarm initialized: current node (bvz81updecsj6wjz393c09vti) is now a manager.
    To add a worker to this swarm, run the following command:
    docker swarm join  --token <token> <swarm_advertise_ip>
    ```  
	Copy and paste the command into your other Docker nodes. Note that the following example is ran on node2, while all other commands are on node1. Do not copy the command from this document, copy it from your Swarm Manager's output.  
    `docker@node2 docker swarm join  --token <token> <swarm_advertise_ip>`
1. Verify your Swarm:  
    `docker@node1 docker node ls`
1. Clone this repo onto your manager node and deploy:  
    `docker@node1 docker stack deploy -c aerospike.yml aerospike`

## Other actions
1. Verify your deployment:
    `docker stack ls`
1. Verify your services:
    `docker service ls`
1. Take a look at your containers:
    `docker ps`
1. Scale your Aerospike cluster:
    `docker service scale <deployment>_<servicename>=#`  
    eg:  
    `docker service scale aerospike_aerospikedb=3`

## Confirm your aerospike cluster:

1. Run asadm:
    `docker exec -it <aerospikedb container> asadm -e info`  
    or  
    `docker exec -it <meshworker container> asadm -h aerospikedb -e info`

1. Run aerospike tools commands:
    `docker exec -it <meshworker container> "<command>"`

## Cleanup
If you used docker-machine to create VMs for docker hosts, just remove the VirtualBox VMs.

To remove the docker swarm stack:
`docker stack rm aerospike`

# Aerospike.conf changes

Due to Docker containers deploying with multiple NICS, you'd need to lock down the interface used for Aerospike networking.

This is done by specifying `address eth0` for each of the following within the network stanza:

* service
* heartbeat
* fabric


# Details

**AerospikeDB service**

endpoint_mode: dnsrr    - By default, service discovery is via Virtual IP (VIP). This is akin to a loadbalancer and does not work well with aerospike discovery mechanism. Therefore DNS Round Robin (dnsrr) is used. **This is a Compose v3.2 feature.**

command - Use our custom conf file located at /run/secrets.
secrets - Utilize the `conffile` secret.

**Meshworker service**

entrypoint - Overwrite default container entrypoint to run our discovery script instead.
secrets - Utilize the `discovery` secret.

## discovery.py

```
usage: discovery.py [-h] [--fqdn SERVICENAME] [-p PORT] [-i INTERVAL] [-v]

optional arguments:
  -h, --help            show this help message and exit
  --fqdn SERVICENAME, --servicename SERVICENAME
                        The FQDN to resolve
  -p PORT, --port PORT  The asinfo port
  -i INTERVAL, --interval INTERVAL
                        The DNS polling interval in s. Defaults to 60
  -v, --verbose         Print status changes
``` 

