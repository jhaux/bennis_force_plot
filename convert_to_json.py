'''Converts Bennis files to a json file, similar to that found at
<https://bl.ocks.org/mbostock/4062045>. This allows to use them for plotting.
'''

__author__ = 'jhaux'
__mail__ = 'jo.mobile.2007@gmail.com'

import argparse
import json
import os
import re


def read_graph_file(path_to_graph):
    '''Takes the <network.dot> file and converts it to a python dict.

    Arguments:
        path_to_graph: path to the .dot file
    '''

    assert os.path.isfile(path_to_graph)

    with open(path_to_graph) as graph_file:
        data = graph_file.read()
        lines = data.split('\n')

        raw_graphs = find_graphs(lines)

        graphs = {}
        for name, description in raw_graphs.iteritems():
            nodes = []
            links = []
            for descriptor in description:
                is_node, value = get_node_or_link(descriptor)
                if is_node:
                    nodes.append(value)
                else:
                    links.append(value)
            graphs[name] = {'nodes': nodes, 'links': links}
            get_all_neighbours(graphs[name])

        return graphs


def find_graphs(lines):
    '''Finds all graphs in a array of lines from a graph file and returns
    the contents of the graphs.'''

    opening_brackets = re.compile('\D{')
    closing_brackets = re.compile('}')

    graph_beginings = []
    graph_ends = []
    for i, line in enumerate(lines):
        matches = opening_brackets.findall(line)
        if len(matches) == 1:
            graph_beginings.append(i)

        matches = closing_brackets.findall(line)
        if len(matches) == 1:
            graph_ends.append(i)

    graphs = {}
    for start, stop in zip(graph_beginings, graph_ends):
        name_line = lines[start]
        name = name_line.split(' ')[1]

        graphs[name] = lines[start+1:stop]

    return graphs


def get_node_or_link(descriptor):
    '''The following assumptions are made:
        - ids are followed directly by a ';'
        - links always contain a '--'
        - links are followed by a ' ' and a ';'
    '''

    if '--' not in descriptor:
        is_node = True
        node_id = descriptor[:-1]
        value = {'id': int(node_id), 'group': 0, 'selected': False}
    else:
        is_node = False
        s, t = descriptor[:-2].split('--')
        value = {'source': int(s), 'target': int(t), 'value': 1}

    return is_node, value


def get_all_neighbours(graph, depth=2):
    '''Find all neighbours of all nodes in a graph up to depth <depth>.'''

    for node in graph['nodes']:
        neighbours = get_neighbours(node, graph, depth)
        node['neighbours'] = neighbours


def get_neighbours(node, graph, depth=2):
    '''Given a node returns all its neighbours up to depth <depth>.'''

    node_id = node['id']

    def get_neighbours_one_node(node_id):
        n = []
        for link in graph['links']:
            s, t = link['source'], link['target']

            if s == node_id:
                n.append(t)
            elif t == node_id:
                n.append(s)
        return n

    neighbours = {'n0': get_neighbours_one_node(node_id)}

    for i in range(1, depth):
        all_n = []
        for n_id in neighbours['n{}'.format(i-1)]:
            all_n += get_neighbours_one_node(n_id)
        neighbours['n{}'.format(i)] = all_n

    # Remove unwanted recursion
    for i in range(1, depth)[::-1]:
        current = neighbours['n{}'.format(i)]
        all_above = [node_id]
        for j in range(0, i):
            all_above += neighbours['n{}'.format(j)]
        clean = [n for n in current if n not in all_above]
        neighbours['n{}'.format(i)] = clean

    return neighbours


def read_costs_or_payoffs_file(path_to_file):
    '''Read costs or payoffs file and return the costs or payoffs over time.

    Arguments:
        path_to_file: path where the file lives
    Returns:
        values: dict of form {node_id: [val_t=0, val_t=1, ...]}
    '''

    assert os.path.isfile(path_to_file)

    with open(path_to_file, 'r') as data_file:
        data = data_file.read()
        timesteps = data.split('\n')

        num_nodes = len(timesteps[0].split(',')) - 1
        num_ts = len(timesteps) - 1

        # range(num_ts) is used here to allow the assing at index code
        # in the inner loop. This of course bears the danger to assign values
        # that are not in the dataset!
        values = {node_id: range(num_ts) for node_id in range(num_nodes)}
        for i, ts in enumerate(timesteps):
            vals_at_ts = ts.split(',')
            for j, val in enumerate(vals_at_ts[:-1]):
                values[j][i] = float(val)

        return values


def write_json_file(graph, costs, payoffs):
    '''Reads all files and joins them together in one json file.

    This script assumes, there is only one graph descriped in <graph>!

    Arguments:
        graph: path to graph file
        costs: path to costs file
        payoffs: path to payoffs file
    '''

    graphs = read_graph_file(graph)
    assert len(graphs.keys()) == 1
    name = graphs.keys()[0]
    graph = graphs[name]

    costs = read_costs_or_payoffs_file(costs)
    payoffs = read_costs_or_payoffs_file(payoffs)

    for node in graph['nodes']:
        node['costs'] = costs[node['id']]
        node['payoffs'] = payoffs[node['id']]

    with open('graph_{}.json'.format(name), 'w+') as f:
        f.write(json.dumps(graph, indent=4, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g',
                        type=str,
                        metavar='<graph.dot>',
                        help='path to graph definition file',
                        required=True)
    parser.add_argument('-c',
                        type=str,
                        metavar='<costs.txt>',
                        help='path to costs',
                        required=True)
    parser.add_argument('-p',
                        type=str,
                        metavar='<payoffs.txt>',
                        help='path to payoffs',
                        required=True)

    args = parser.parse_args()

    write_json_file(args.g, args.c, args.p)
