"""
As docker-py does not support updating services with capabilities, this is a patched version based on https://github.com/docker/docker-py/pull/2809/
"""
import docker

docker.constants.DEFAULT_DOCKER_API_VERSION = '1.41'
docker.models.services.CONTAINER_SPEC_KWARGS.extend(['cap_add', 'cap_drop'])


class ContainerSpec(docker.types.services.ContainerSpec):
    def __init__(self, *args, **kwargs):
        cap_add = kwargs.pop('cap_add', None)
        cap_drop = kwargs.pop('cap_drop', None)

        super().__init__(*args, **kwargs)

        if cap_add is not None:
            if not isinstance(cap_add, list):
               raise TypeError('cap_add must be a list')

            self['CapabilityAdd'] = cap_add

        if cap_drop is not None:
            if not isinstance(cap_drop, list):
                raise TypeError('cap_drop must be a list')

            self['CapabilityDrop'] = cap_drop


class DockerClient(docker.DockerClient):
    pass


# monkey patch the import in models, not the original
docker.models.services.ContainerSpec = ContainerSpec
from_env = DockerClient.from_env
