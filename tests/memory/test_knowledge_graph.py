"""``KnowledgeGraph``: lo que el arquitecto sabe del proyecto, con relaciones.

Está **conectado** —``MemoryEngine`` lo construye y ``refresh()`` lo llena—
y estaba al 62 % de cobertura.

Es también el motivo por el que se podó ``knowledge/`` entero: aquel paquete
tenía cuatro constructores de grafos (``file_graph``, ``dependency_graph``,
``architecture_graph``, ``project_graph``) que recorrían el árbol con
``rglob`` pelado —mirando dentro del ``.venv``— y cuyo ``DependencyGraph``
**reventaba con un solo archivo que no compilara**. Esto, más
``analyzer/dependency_analyzer.py``, cubre lo mismo sin esos dos problemas.
"""

from __future__ import annotations

import pytest

from ai_architect.memory.knowledge_graph import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
)


def nodo(identificador: str, categoria: str = "modulo") -> KnowledgeNode:
    return KnowledgeNode(
        id=identificador,
        category=categoria,
        label=identificador,
    )


@pytest.fixture
def grafo() -> KnowledgeGraph:
    return KnowledgeGraph()


@pytest.fixture
def con_dos(grafo: KnowledgeGraph) -> KnowledgeGraph:
    grafo.add_node(nodo("a"))
    grafo.add_node(nodo("b"))
    return grafo


# --- Nodos ------------------------------------------------------------------


def test_empieza_vacio(grafo: KnowledgeGraph) -> None:
    assert grafo.node_count() == 0
    assert grafo.edge_count() == 0


def test_anadir_un_nodo(grafo: KnowledgeGraph) -> None:
    grafo.add_node(nodo("a"))

    assert grafo.node_count() == 1
    assert grafo.has_node("a") is True


def test_un_nodo_repetido_no_duplica(grafo: KnowledgeGraph) -> None:
    grafo.add_node(nodo("a", categoria="vieja"))
    grafo.add_node(nodo("a", categoria="nueva"))

    assert grafo.node_count() == 1
    assert grafo.node("a").category == "nueva"


def test_pedir_un_nodo_que_no_existe(grafo: KnowledgeGraph) -> None:
    assert grafo.node("inventado") is None
    assert grafo.has_node("inventado") is False


# --- Aristas ----------------------------------------------------------------


def test_unir_dos_nodos(con_dos: KnowledgeGraph) -> None:
    con_dos.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))

    assert con_dos.edge_count() == 1


def test_no_se_puede_unir_desde_un_nodo_que_no_existe(grafo: KnowledgeGraph) -> None:
    """Una arista colgando no es un grafo, es un error silencioso."""
    grafo.add_node(nodo("b"))

    with pytest.raises(ValueError, match="Unknown node: a"):
        grafo.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))


def test_no_se_puede_unir_hacia_un_nodo_que_no_existe(grafo: KnowledgeGraph) -> None:
    grafo.add_node(nodo("a"))

    with pytest.raises(ValueError, match="Unknown node: b"):
        grafo.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))


def test_un_nodo_puede_apuntar_a_varios(con_dos: KnowledgeGraph) -> None:
    con_dos.add_node(nodo("c"))
    con_dos.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))
    con_dos.add_edge(KnowledgeEdge(source="a", target="c", relation="importa"))

    assert con_dos.edge_count() == 2


# --- Recorrer ---------------------------------------------------------------


def test_los_vecinos_son_a_los_que_apunta(con_dos: KnowledgeGraph) -> None:
    con_dos.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))

    assert [n.id for n in con_dos.neighbors("a")] == ["b"]


def test_los_vecinos_van_en_un_solo_sentido(con_dos: KnowledgeGraph) -> None:
    """Es un grafo dirigido: que a importe a b no significa lo contrario."""
    con_dos.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))

    assert con_dos.neighbors("b") == []


def test_un_nodo_sin_aristas_no_tiene_vecinos(con_dos: KnowledgeGraph) -> None:
    assert con_dos.neighbors("a") == []


def test_las_relaciones_van_en_los_dos_sentidos(con_dos: KnowledgeGraph) -> None:
    """Para saber quién depende de un módulo hace falta mirar las dos puntas."""
    con_dos.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))

    assert len(con_dos.relations("b")) == 1
    assert con_dos.relations("b")[0].source == "a"


def test_las_relaciones_de_un_nodo_suelto(con_dos: KnowledgeGraph) -> None:
    assert con_dos.relations("a") == []


# --- Vaciar -----------------------------------------------------------------


def test_vaciarlo_se_lleva_nodos_y_aristas(con_dos: KnowledgeGraph) -> None:
    con_dos.add_edge(KnowledgeEdge(source="a", target="b", relation="importa"))

    con_dos.clear()

    assert con_dos.node_count() == 0
    assert con_dos.edge_count() == 0
