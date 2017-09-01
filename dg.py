#!/usr/bin/env python3

import argparse
import pprint
import glob
import sys

import dirtygrapher.data
import dirtygrapher.log
import dirtygrapher.graph
import dirtygrapher.misc

import yaml
import json
import csv
from os import getcwd
from os.path import join

if __name__ == '__main__':
    # Do some command line parsing
    parser = argparse.ArgumentParser(description='not sure')

    parser.add_argument('-c','--config-file', metavar='CONFIG', type=str, nargs=1, default=['config.yaml'],
                        help='config to use to generate graph(s)')
    parser.add_argument('-n', '--no-graph', action='store_true',
                        help='do not generate graphs - very good when creating a data dump')
    parser.add_argument('-r', '--read-dump', action='store_true',
                        help='read dump file instead of graphing data')
    parser.add_argument('-d', '--dump-file', metavar='DUMPF', type=str, nargs=1, default=['dump.yaml'],
                        help='file to dump to or read from depending on state')
    parser.add_argument('--csv', action='store_true',
                        help='create CSV output - implies --no-graph')
    parser.add_argument('--json', action='store_true',
                        help='create JSON output - implies --no-graph')
    parser.add_argument('filespec', metavar='FILESPEC', type=str, nargs='*',
                        help='base name of input files - each one is treated as a seperate line within the dataset')

    args = parser.parse_args()

    # parse config
    config = None
    with open(args.config_file[0],'r') as configf:
        # there should only be ONE config document
        config = next(yaml.load_all(configf, Loader=yaml.CSafeLoader))

    if args.read_dump:
        with open(args.dump_file[0], 'r') as dumpf:
            tmp = yaml.load_all(dumpf, Loader=yaml.CLoader)
            X = next(tmp)
            reduced_data = next(tmp)
    else:
        if args.filespec is None:
            eprint('No filespecs given! Exiting...')
            parser.print_help()
            sys.exit()
        else:
            data = []
            for idx, filename in enumerate(args.filespec):
                data.append([])
                for i in glob.iglob(join(getcwd(), filename, '*.log')):
                    with open(i, 'r') as outfile:
                        tmp = yaml.load_all(outfile, Loader=yaml.CLoader)
                        for doc in tmp:
                            if 'config' in config and 'lformat' in config['config']: # we change the name of the data set to make it more visible
                                doc['test']['name'] = '{:s}-{:s}'.format(filename.split(config['config']['lformat']['splitchar'])[config['config']['lformat']['tokennum']], doc['test']['name'])
                            data[idx].append(doc)

            if len(data) != len(args.filespec):
                eprint('Data did not correctly populate, wrong lengths!')
                sys.exit()

            #pprint.pprint(data)
            #sys.exit()

            # get size of data in bytes
            #print(sys.getsizeof(data))

            # get x values
            if 'config' in config and 'xrange' in config['config'] and config['config']['xrange']:
                X = config['config']['xrange']
            else:
                Xs = set()
                for i in data:
                    for j in i:
                        Xs.add(j['test']['size'][0])

                X = list(Xs)
                X.sort()

            reduced_data = dirtygrapher.data.collect_data(data, **config['data'])
            #collect_data_from_set_update(data, reduced_data, 'sync-test', hkernel=('host','Kernel',0))
            dirtygrapher.data.compute_median(reduced_data, *config['data'].keys())

            # here we can dump the data so that we don't need to recompute it each time
            if 'config' in config and 'dump' in config['config'] and config['config']['dump']:
                with open(args.dump_file[0],'w') as dumpf:
                    yaml.dump_all([X, reduced_data], dumpf, explicit_start=True, allow_unicode=False, Dumper=yaml.CDumper)

            if args.json:
                compute_fold(reduced_data, drop_x_data, (X)) # FIXME do we need to this each time?
                #compute_fold(reduced_data, drop_not_listed, (graph['plots']))
                sys.stdout.write(json.dumps([X, reduced_data], sort_keys=True, indent=2))
            elif args.csv:
                compute_fold(reduced_data, drop_x_data, (X)) # FIXME do we need to this each time?
                create_csv_table(reduced_data, ['x'] + reduced_data.keys(), X)

    if not args.no_graph and not (args.json or args.csv):
        for graph in config['graph']:
            dirtygrapher.graph.create_graph(graph['title'], graph['xlabel'], graph['ylabel'], X, reduced_data, graph['plots'], graph.get('options'))
    else:
        eprint('Nothing graphed... did you generate a dump?')
