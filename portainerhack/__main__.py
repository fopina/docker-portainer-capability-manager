from . import patched_docker as docker
import logging
import argparse
from threading import Timer

logger = logging.getLogger(__name__)

LABEL_DELAY = 'io.portainerhack.delay'
LABEL_ADD = 'io.portainerhack.cap_add'
LABEL_DROP = 'io.portainerhack.cap_drop'


class ServiceMonitor:
    def __init__(self):
        self.client = docker.from_env()

    def update_service(self, service, service_repr, need_add, need_drop):
        logger.info('Service %s need update - cap_add %s and cap_drop %s', service_repr, need_add, need_drop)
        # FIXME: review possible replies
        r = service.update(cap_add=need_add, cap_drop=need_drop)
        logger.info('Service %s capabilities updated: %s', service_repr, r)
        return True

    def process_service(self, service_id):
        service = self.client.services.get(service_id)
        if service.name:
            service_repr = f'{service.name} ({service.id})'
        else:
            service_repr = service.id

        want_add = service.attrs.get('Spec', {}).get('Labels', {}).get(LABEL_ADD)
        want_drop = service.attrs.get('Spec', {}).get('Labels', {}).get(LABEL_DROP)
        if not want_add and not want_drop:
            logger.debug('service %s does not have any of the labels, ignored', service_repr)
            return False

        want_add = {f'CAP_{x}' for x in want_add.split(',')} if want_add else set()
        want_drop = {f'CAP_{x}' for x in want_drop.split(',')} if want_drop else set()
        has_add = set(service.attrs.get('Spec', {}).get('TaskTemplate', {}).get('ContainerSpec', {}).get('CapabilityAdd') or [])
        has_drop = set(service.attrs.get('Spec', {}).get('TaskTemplate', {}).get('ContainerSpec', {}).get('CapabilityDrop') or [])

        if want_add:
            logger.debug('Service %s requires cap_add of %s and has %s', service_repr, want_add, has_add)
        if want_drop:
            logger.debug('Service %s requires cap_drop of %s and has %s', service_repr, want_drop, has_drop)

        need_add = list(want_add - has_add)
        need_drop = list(want_drop - has_drop)

        if not need_add and not need_drop:
            logger.debug('Service %s does not need anything, ignored', service_repr)
            return False

        # Check if service needs delay
        want_delay = service.attrs.get('Spec', {}).get('Labels', {}).get(LABEL_DELAY)

        if want_delay:
            want_delay = int(want_delay)
            logger.info('Service %s delay initiated: %ss', service_repr, want_delay)
            Timer(int(want_delay), self.update_service, [service, service_repr, need_add, need_drop]).start()
        else:
            self.update_service(service, service_repr, need_add, need_drop)

    def review_existing_services(self):
        for service in self.client.services.list():
            self.process_service(service.id)

    def monitor_events(self):
        for event in self.client.events(decode=True, filters={'type': 'service', 'event': 'update'}):
            s_id = event['Actor']['ID']
            s_name = event['Actor'].get('Attributes', {}).get('name')
            logger.debug('Service %s (%s) update seen in events', s_id, s_name)
            self.process_service(s_id)


def main(args):
    if args.debug:
        logger.setLevel(logging.DEBUG)
    monitor = ServiceMonitor()
    logger.debug('reviewing existing services, before monitor mode')
    monitor.review_existing_services()
    logger.debug('review done, monitoring events now')
    monitor.monitor_events()


def build_parser(args=None):
    parser = argparse.ArgumentParser(description='Monitor for services that require cap_add on the side (portainer hack)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='debug output')

    return parser.parse_args(args)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(build_parser())
