I've been using this (swarm proxy service) for running containers with extra capabilities (or privileged) as docker swarm did not support those.
as this was finally added in docker 20.10 (insert feature link), but portainer doesn't support it yet (https://github.com/portainer/portainer/issues/4684), this service will try to complement it, by performing a service upgrade on the services created by portainer (as suggested in the same issue)

only needs to run one single replica but in a master node, as it only monitors `service` events.


https://docs.docker.com/engine/reference/commandline/events/#object-types

