# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import itertools
from collections import OrderedDict, defaultdict
from typing import List, Tuple, Hashable, Dict

import numpy as np
import networkx as nx

DIRECTIONS = ["north", "south", "east", "west"]

directions = OrderedDict([((0, 1), 'north'),
                          ((-1, 0), 'west'),
                          ((0, -1), 'south'),
                          ((1, 0), 'east')])

RELATIVE_POSITIONS = {
    'north': np.array((0, 1)),
    'south': np.array((0, -1)),
    'east': np.array((1, 0)),
    'west': np.array((-1, 0)),
}

OPPOSITE_RELATIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}

def reverse_direction(direction):
    index = DIRECTIONS.index(direction)
    if index % 2 == 0:
        return DIRECTIONS[index + 1]

    return DIRECTIONS[index -1]


def xy_diff(x, y):
    return tuple(np.array(y) - np.array(x))


def direction(x, y):
    return directions[xy_diff(x, y)]


def gen_layout(rng, n_nodes=5, h=10, w=10):
    '''
    Generate a map with n_nodes rooms by
    picking a subgraph from a h,w grid.
    '''
    G = nx.grid_2d_graph(h, w, create_using=nx.OrderedGraph())
    new_G = nx.OrderedGraph()
    pos = (rng.randint(0, h - 1),
           rng.randint(0, w - 1))
    visited = set()
    visited.add(pos)
    new_G.add_node(pos, name="r_{}".format(len(new_G)))
    while len(visited) < n_nodes:
        pos_ = pos
        neighbors = G[pos]
        neighbors = list(neighbors.keys())
        pos = neighbors[rng.randint(0, len(neighbors))]
        visited.add(pos)
        if pos not in new_G.nodes:
            new_G.add_node(pos, name="r_{}".format(len(new_G)))

        new_G.add_edge(pos_, pos,
                       has_door=False,
                       door_state=None,
                       door_name=None)
    return new_G


def mark_doors(G, rng, possible_door_states=["open", "closed", "locked"]):
    """Put doors between neighbouring articulation points."""
    components = list(nx.articulation_points(G))
    combos = list(itertools.combinations(components, 2))

    door_id = 0
    for i, j in combos:
        if G.has_edge(i, j):
            door_name = 'd_{}'.format(door_id)
            G[i][j]['has_door'] = True
            G[j][i]['has_door'] = True
            door_state = rng.choice(possible_door_states)
            G[j][i]['door_state'] = door_state
            G[i][j]['door_state'] = door_state
            G[i][j]['door_name'] = door_name
            G[j][i]['door_name'] = door_name
            door_id += 1
            if door_state == "locked":
                G[i][j]["weight"] = 999
                G[j][i]["weight"] = 999
            else:
                G[i][j]["weight"] = 0.1
                G[j][i]["weight"] = 0.1

    return G


def extremes(G):
    '''Find left most and bottom nodes in the cartesian sense.'''
    left_most = sorted(G.nodes(), key=lambda x: x[0])[0]
    bottom = sorted(G.nodes(), key=lambda x: x[1])[0]
    return left_most, bottom


def relabel(G):
    """
    Relabel G so that its origin is (0, 0)
    """
    left_most, bottom = extremes(G)
    x = left_most[0]
    y = bottom[1]
    mapping = lambda n: (n[0]-x, n[1]-y)
    G = nx.relabel_nodes(G, mapping=mapping)
    return G


def get_path(G, room1, room2):
    sp = nx.shortest_path(G, source=room1, target=room2)
    return list(zip(sp, sp[1:]))


def plot_graph(g, show=True):
    """Plot cartesian graph on a grid."""
    import matplotlib.pyplot as plt
    pos = dict((n, n) for n in g.nodes())
    labels = dict(((i, j), i * 10 + j) for i, j in g.nodes())
    labels = {n: d["name"] for n, d in g.nodes.items()}
    nx.draw_networkx(g, pos=pos, labels=labels, with_labels=True)
    plt.axis('off')
    if show:
        plt.show()


def create_map(rng, n_nodes, h, w, possible_door_states=["open", "closed", "locked"]):
    G = gen_layout(rng, n_nodes=n_nodes, h=h, w=w)
    if possible_door_states is not None:
        G = mark_doors(G, rng, possible_door_states)

    return G


def create_small_map(rng, n_rooms, possible_door_states=["open", "closed", "locked"]):
    G = nx.grid_2d_graph(3, 3)

    G = nx.OrderedGraph()
    room0 = (0, 0)
    G.add_node(room0, name="r_0")

    D = list(directions.keys())
    for i in range(n_rooms-1):
        rng.shuffle(D)
        new_room = D.pop()
        G.add_node(new_room, name="r_{}".format(len(G)))
        has_door = rng.rand() < 0.5
        door_state = rng.choice(possible_door_states)

        G.add_edge(room0, new_room,
                   has_door=has_door,
                   door_state=door_state if has_door else None,
                   door_name="d_{}".format(i))
        G.add_edge(new_room, room0,
                   has_door=has_door,
                   door_state=door_state if has_door else None,
                   door_name="d_{}".format(i))

    return G


def shortest_path(G, source, target):
    """
    Return shortest path in terms of directions.
    """
    d = []
    path = nx.algorithms.shortest_path(G, source, target)
    for i in range(len(path) - 1):
            d.append(direction(path[i], path[i+1]))
    return d


class InvalidConstraint(NameError):
    pass


def relative_2d_constraint_layout(G: nx.Graph, constraints: List[Tuple[Hashable, str, Hashable]]) -> Dict[Hashable, Tuple[int, int]]:
    """ Position nodes respecting provided relative 2D contraints.

    Arguments:
        G: Graph containing the nodes to position nodes.
        constraints: List of relative positioning contraints. Each constraint
                     has the following format: (node1, relation, node2) where
                     relation is either 'north', 'south', 'east' or 'west'.
                     For instance, ('A', 'north', 'B') would mean node 'A'
                     should be aligned above (north of) node 'B'.

    Returns:
        pos: Node positions.
    """
    constraints_ = defaultdict(list)

    def _check_existing_constraint(src, relation, dest):
        existing_constraints = [c for c in constraints_[src] if c[1] == relation]
        for constraint in existing_constraints:
            if (src, relation, dest) != constraint:
                msg = "Find multiple constraints with the same relation for node {}: {} and {}."
                msg = msg.format(src, (src, relation, dest), constraint)
                raise InvalidConstraint(msg)

    for src, relation, dest in constraints:
        opposite_relation = OPPOSITE_RELATIONS[relation]
        _check_existing_constraint(src, relation, dest)
        _check_existing_constraint(dest, opposite_relation, src)
        constraints_[src].append((src, relation, dest))
        constraints_[dest].append((dest, opposite_relation, src))

    edges = []
    nodes = list(G.nodes())
    node = nodes[0]
    pos = {node: (0, 0)}

    def _used_pos():
        pos_along_edges = []
        for e in edges:
            A, B = pos[e[0]], pos[e[1]]
            if A[0] == B[0]:  # Y-axis edge.
                for i in range(A[1], B[1], np.sign(B[1] - A[1])):
                    pos_along_edges.append((A[0], i))
            else:  # X-axis edge.
                for i in range(A[0], B[0], np.sign(B[0] - A[0])):
                    pos_along_edges.append((i, A[1]))

        return list(pos.values()) + pos_along_edges

    def _move_subgraph(pos, offset, pivot):
        for n, p in pos.items():
            if np.any(offset * (offset + p - pivot) > 0):
                pos[n] = tuple(p + offset)

    openset = [node]
    closedset = set()

    while len(openset) > 0:
        node = openset.pop(0)
        closedset.add(node)

        for constraint in constraints_[node]:
            condition = constraint[1]
            target = constraint[-1]

            if target in openset or target in closedset:
                edges.append((node, target))
                continue

            openset.append(target)

            src_pos = np.array(pos[node])
            offset = RELATIVE_POSITIONS[condition]
            target_pos = tuple(src_pos - offset)

            if target_pos in _used_pos():
                _move_subgraph(pos, offset, src_pos)

            pos[target] = tuple(pos[node] - offset)
            edges.append((node, target))

    pos = {k: tuple(np.array(v).tolist()) for k, v in pos.items()}
    return pos
