import json
import os
import argparse
from collections import namedtuple
import re

Node = namedtuple('Node', 'node_name sig_name idx wave value edge')
Edge = namedtuple('Edge', 'type_ n1 n2 delay')

mapping = {"1" : "$rise" , "0": "$fell" , ".": "$stable"}
edge_mapping = {"-~>": "curve", "->": "hor", "-|>" : "vert"}

def find_node(nodes, name):
    for n in nodes:
        if name == n.node_name:
            return n
    return None

def get_last_value(wave):
    v = None
    for i in reversed(wave):
        if i != ".":
            v = i
            break
    return v

def main():
    # args
    parser = argparse.ArgumentParser()
    parser.add_argument('wave_file', help='Path to Wave')
    args = parser.parse_args()

    # load wavedrom
    fh = open(args.wave_file)
    wd = json.load(fh)

    # Parse signals
    nodes = [] 
    for sig in wd["signal"]:
        sig_name = sig["name"]
        wave = sig["wave"]
        node = sig["node"]

        for i, n in enumerate(node):
            # Parse labels
            if n != ".":
                edge = mapping[wave[i]]

                assert (edge in mapping.values())

                """
                in case of 1 or 0, that is the correct value
                in case of ".", i need to get the last non-"." value
                """
                value = None
                if wave[i] != ".":
                    value = wave[i]
                else:
                    value = get_last_value(wave[0:i])
                assert(value is not None)

                nn = Node(n, sig_name, i , wave[i], value, edge)
                nodes.append(nn)

    # Parse edges for assertions
    edges = []
    for e in wd["edge"]:
        ed = None

        # a-~>b DELAY
        # a |-> ##[DELAY] b
        result = re.match("([a-zA-Z])-~>([a-zA-Z]) (.*)", e)
        if result:
            tokens = result.groups()
            ed = Edge("timed", *tokens)

        # a-|>b
        # a |-> b
        result = re.match("([a-zA-Z])-\|>([a-zA-Z])", e)
        if result:
            tokens = result.groups()
            ed = Edge("zero-delay", *tokens, None)

        edges.append(ed)
        
        
    """
    TODO
    $rose(b) |-> ##[3:5] $past(a)
    """

    """
    Generation
    """
    for ed in edges:
        if ed.type_ == "timed":
            x1 = find_node(nodes, ed.n1)
            x2 = find_node(nodes, ed.n2)
            print(f"{x1.edge}({x1.sig_name}) |-> ##[{ed.delay}] {x2.edge}({x2.sig_name}); ")

        if ed.type_ == "zero-delay":
            x1 = find_node(nodes, ed.n1)
            x2 = find_node(nodes, ed.n2)
            print(f"{x1.edge}({x1.sig_name}) |-> ({x2.edge}({x2.sig_name}); && {x2.sig_name} == {x2.value}  ")

if __name__ == "__main__":
    main()
