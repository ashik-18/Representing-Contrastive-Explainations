import argparse
import re
import sys
import subprocess
from graphviz import Digraph


def install_requirements():
    subprocess.run(["python3", "-m", "venv", "venv"])
    activate_script = "./venv/bin/activate"
    subprocess.run(["source", activate_script], shell=True, executable="/bin/bash")
    subprocess.run(["pip", "install", "-r", "../../requirements.txt"], check=True)

def parse_mapping(line):
    d = {}
    for pair in line.split(','):
        if '->' not in pair:
            continue
        k, v = pair.split('->', 1)  # Split by '->' and strip whitespace
        d[k.strip()] = v.strip()
    return d

def apply_mapping(axioms, mapping):
    edges = []
    for stmt in axioms.split(','):
        parts = stmt.strip().split()
        if len(parts) == 3:
            subj, rel, obj = parts
            mapped_subj = mapping.get(subj, subj)
            mapped_obj = mapping.get(obj, obj)
            edges.append((mapped_subj, rel, mapped_obj))
    return edges

def update_flags(common_nodes, node, flag):
    if node not in common_nodes:
        common_nodes[s] = {flag: True}
    else:
        common_nodes[s].update({flag: True})

if __name__ == "__main__":
    install_requirements()

    parser = argparse.ArgumentParser("Graph Representation of Fact vs Foil")
    parser.add_argument(
        "--input-file",
        type=str,
        # Change this to your input file path when running without cmd line
        default="../logs/family-ontology.owl.log",
        help="Path to the input file containing the mappings and axioms."
        #todo need to make this required = true before pushing
    )
    try:
        args = parser.parse_args()
        file_path = args.input_file
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        sys.exit(1)

    with open(file_path, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = {
        "fact_mappings": [],
        "foil_mappings": [],
        "common_axioms": [],
        "different_axioms": [],
        "class_expression": []
    }

    expressions = []
    collecting = False
    current_expr = ""

    for line in lines:
        line = line.strip()

        if "CE: Common:" in line:
            common_axioms = line.split("CE: Common:")[1].strip()
            current_block["common_axioms"].append(common_axioms)
        elif "Different:" in line:
            different_axioms = line.split("Different:")[1].strip()
            current_block["different_axioms"].append(different_axioms)
        elif "Fact mapping:" in line:
            fact_mapping = re.search(r"Fact mapping:\s*([^\n]+)", line).group(1)
            fact_mapping = parse_mapping(fact_mapping)
            current_block["fact_mappings"].append(fact_mapping)
        elif "Foil mapping:" in line:
            foil_mapping = re.search(r"Foil mapping:\s*([^\n]+)", line).group(1)
            foil_mapping = parse_mapping(foil_mapping)
            current_block["foil_mappings"].append(foil_mapping)

        elif "CEP: ClassExpression:" in line:
            # Start collecting from after the keyword
            collecting = True
            part = line.split("CEP: ClassExpression:")[1].strip()
            current_expr += part + " "
        elif collecting:
            current_expr += line.strip() + " "

        if collecting and "," in current_expr:
            expr = current_expr.split(",", 1)[0].strip()
            current_expr = ""
            collecting = False
            current_block["class_expression"].append(expr)

        if current_block["fact_mappings"] and current_block["foil_mappings"] and current_block["common_axioms"] and \
                current_block["different_axioms"] and current_block["class_expression"]:
            blocks.append(current_block)
            current_block = {
                "fact_mappings": [],
                "foil_mappings": [],
                "common_axioms": [],
                "different_axioms": [],
                "class_expression": []
            }

    c = 1
    for block in blocks:

        # Build edges
        fact_edges = apply_mapping(block["common_axioms"][0], block["fact_mappings"][0]) + \
                     apply_mapping(block["different_axioms"][0], block["fact_mappings"][0])
        common_foil_edges = apply_mapping(block["common_axioms"][0], block["foil_mappings"][0])
        different_foil_edges = apply_mapping(block["different_axioms"][0], block["foil_mappings"][0])

        # Create main graph
        dot = Digraph(comment="Fact vs Foil in one image",
                      graph_attr={'rankdir': 'LR', 'splines': 'true', 'bgcolor': 'lightyellow', 'label': f"Query: {block['class_expression'][0]}",
                                  'fontsize': '20', 'fontcolor': 'black'})

        common_nodes = {}

        # FACT subgraph
        with dot.subgraph(name='cluster_fact') as f:
            f.attr(style='filled', color='lightyellow', label="", fontsize='20', fontcolor='black', labelloc='t')
            for s, r, o in fact_edges:
                f.edge(s, o, label=r)
                update_flags(common_nodes, s, "fact_flag")
                update_flags(common_nodes, o, "fact_flag")

        # FOIL common subgraph
        with dot.subgraph(name='cluster_foil') as f:
            f.attr(style='filled', color='lightyellow', label="", )
            for s, r, o in common_foil_edges:
                f.edge(s, o, label=r)
                update_flags(common_nodes, s, "foil_flag")
                update_flags(common_nodes, o, "foil_flag")

        # FOIL different subgraph
        with dot.subgraph(name='cluster_foil') as f:
            f.attr(style='filled', color='lightyellow', label="", )
            for s, r, o in different_foil_edges:
                f.edge(s, o, label=r, style='dashed', color='#ff0000', penwidth='2')
                update_flags(common_nodes, s, "foil_flag")
                update_flags(common_nodes, o, "foil_flag")

        with dot.subgraph(name='cluster_foil') as f:
            for node in common_nodes:
                if common_nodes[node].get("fact_flag"):
                    f.node(node, style='filled', fillcolor='#3399FF')
                if common_nodes[node].get("foil_flag"):
                    f.node(node, style='filled', fillcolor='#6AC780')
                if common_nodes[node].get("fact_flag") and common_nodes[node].get("foil_flag"):
                    f.node(node, style='filled', fillcolor='lightyellow')

        dot.node('legend', label="""<
                                <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
                                  <TR><TD COLSPAN="2"><B>Legend</B></TD></TR>
                                  <TR><TD BGCOLOR="#3399FF"></TD><TD>Fact Node</TD></TR>
                                  <TR><TD BGCOLOR="#6AC780"></TD><TD>Foil Node</TD></TR>
                                  <TR><TD><FONT COLOR="#ff0000"><I>--------</I></FONT></TD><TD>Missing edge</TD></TR>

                                </TABLE>
                                >""", shape='none', pos='0,0!', width='1', height='1', style='filled',
                 fillcolor='lightyellow')

        output_file = "../output/graphs/graph-" + str(c)

        c += 1
        dot.render(output_file, format="png", cleanup=True)

        print(f"Graph saved to: {output_file}.png")
