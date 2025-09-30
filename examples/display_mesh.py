import sys
import os
import numpy as np
import pyvista as pv
from vtk import VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_HEXAHEDRON, VTK_WEDGE

sys.path.append('.')
from dynakw import DynaKeywordReader, KeywordType

# Add project root to path to allow importing dynakw
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def create_unstructured_grid(dyna_file: DynaKeywordReader) -> pv.UnstructuredGrid:
    """
    Create a PyVista UnstructuredGrid from a DynaKeywordReader object.
    """
    # Extract nodes
    node_keywords = dyna_file.find_keywords(KeywordType.NODE)
    if not node_keywords:
        raise ValueError("File does not contain *NODE keyword.")

    node_ids_list = []
    points_list = []
    for node_keyword in node_keywords:
        node_ids_list.append(node_keyword.cards['Card 1']['NID'])
        points_list.append(np.vstack((
            node_keyword.cards['Card 1']['X'],
            node_keyword.cards['Card 1']['Y'],
            node_keyword.cards['Card 1']['Z']
        )).T)

    node_ids = np.concatenate(node_ids_list)
    points = np.concatenate(points_list)

    node_id_to_point_index = {node_id: i for i, node_id in enumerate(node_ids)}

    cells_list = []
    cell_types_list = []

    # Shell elements (triangles and quads)
    shell_keywords = dyna_file.find_keywords(KeywordType.ELEMENT_SHELL)
    if shell_keywords:
        for shell_keyword in shell_keywords:
            card1 = shell_keyword.cards['Card 1']
            n1, n2, n3 = card1['N1'], card1['N2'], card1['N3']
            # N4 is optional for triangles
            n4 = card1.get('N4', np.zeros_like(n1))

            for i in range(len(n1)):
                # Check for Quad (4 nodes) vs Triangle (3 nodes)
                # A triangle can have N4=0 or N4=N3
                if n4[i] > 0 and n4[i] != n3[i]:
                    points_indices = [
                        node_id_to_point_index[n1[i]
                                               ], node_id_to_point_index[n2[i]],
                        node_id_to_point_index[n3[i]
                                               ], node_id_to_point_index[n4[i]]
                    ]
                    cells_list.extend([4] + points_indices)
                    cell_types_list.append(VTK_QUAD)
                else:
                    points_indices = [
                        node_id_to_point_index[n1[i]
                                               ], node_id_to_point_index[n2[i]],
                        node_id_to_point_index[n3[i]]
                    ]
                    cells_list.extend([3] + points_indices)
                    cell_types_list.append(VTK_TRIANGLE)

    # Solid elements (tets, hexas, wedges)
    solid_keywords = dyna_file.find_keywords(KeywordType.ELEMENT_SOLID)
    if solid_keywords:
        for solid_keyword in solid_keywords:
            card1 = solid_keyword.cards['Card 1']
            num_elements = len(card1['N1'])

            def get_node_col(name):
                return card1.get(name, np.zeros(num_elements, dtype=int))

            n1, n2, n3, n4 = card1['N1'], card1['N2'], card1['N3'], card1['N4']
            n5, n6, n7, n8 = get_node_col('N5'), get_node_col(
                'N6'), get_node_col('N7'), get_node_col('N8')

            for i in range(num_elements):
                # Check for Hexahedron (8 nodes)
                if n8[i] > 0:
                    points_indices = [node_id_to_point_index[nid] for nid in [
                        n1[i], n2[i], n3[i], n4[i], n5[i], n6[i], n7[i], n8[i]]]
                    cells_list.extend([8] + points_indices)
                    cell_types_list.append(VTK_HEXAHEDRON)
                # Check for Wedge (6 nodes)
                elif n6[i] > 0:
                    points_indices = [node_id_to_point_index[nid] for nid in [
                        n1[i], n2[i], n3[i], n4[i], n5[i], n6[i]]]
                    cells_list.extend([6] + points_indices)
                    cell_types_list.append(VTK_WEDGE)
                # Check for Tetrahedron (4 nodes)
                else:
                    points_indices = [node_id_to_point_index[nid]
                                      for nid in [n1[i], n2[i], n3[i], n4[i]]]
                    cells_list.extend([4] + points_indices)
                    cell_types_list.append(VTK_TETRA)

    if not cells_list:
        raise ValueError(
            "No supported element types (*ELEMENT_SHELL, *ELEMENT_SOLID) found or parsed in the file.")

    cells = np.array(cells_list)
    cell_types = np.array(cell_types_list, np.uint8)

    grid = pv.UnstructuredGrid(cells, cell_types, points)
    return grid


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <filepath.k>")
        sys.exit(1)

    kw_fname = sys.argv[1]

    try:
        with DynaKeywordReader(kw_fname) as dyna_file:
            mesh = create_unstructured_grid(dyna_file)
        mesh.plot(color="w", smooth_shading=True, show_edges=True)
    except FileNotFoundError:
        print(f"Error: File not found at {kw_fname}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
