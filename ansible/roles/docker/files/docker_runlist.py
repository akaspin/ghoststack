#!/usr/bin/env python
# coding=utf-8

import argparse
from itertools import chain

import docker


class Container(object):
    def __init__(self, raw):
        self.name = raw['Name'][1:]
        links = [l.split(':')[0][1:] for l
                 in (raw['HostConfig']['Links'] or [])]
        volumes_from = [v for v in
                        (raw['HostConfig']['VolumesFrom'] or [])]
        self._deps_names = list(set(links + volumes_from))
        self.dependencies = []
        super(Container, self).__init__()

    def run_list(self, raw):
        res = self._deps_names + [self.name]
        pre = chain.from_iterable(dep.run_list(raw) for dep in raw
                                  if dep.name in self._deps_names)
        return list(pre) + res

    def __repr__(self):
        return '%s %s' % (self.name, self.dependencies)


class RunList(object):

    def __init__(self, client):
        self.client = client
        self.containers = [Container(c) for c in
                           [client.inspect_container(c['Id']) for c
                            in client.containers(all=True)]]
        super(RunList, self).__init__()

    @property
    def run_list(self):
        feed = list(chain.from_iterable(c.run_list(self.containers)
                    for c in self.containers))
        return reduce(lambda x, y: x if y in x else x + [y], feed, [])


def main():
    parser = argparse.ArgumentParser(description='Docker run list.')
    parser.add_argument('--reverse', help="Reverse containers",
                        action='store_true')
    args = parser.parse_args()
    res = RunList(docker.Client()).run_list
    if args.reverse:
        res.reverse()
    print ' '.join(res)


if __name__ == '__main__':
    main()
