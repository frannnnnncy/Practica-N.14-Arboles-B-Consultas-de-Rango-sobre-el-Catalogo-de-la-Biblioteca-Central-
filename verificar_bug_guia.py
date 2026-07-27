"""
Prueba de verificacion: se ejecuta la logica de eliminacion TAL COMO aparece
en la guia (_reparar_hoja_subpoblada SIN la llamada final a
_reparar_interno_subpoblado) para comprobar si en efecto se rompe con un
arbol de orden pequeno y varios niveles, tal como se sospecho.
"""
import copy
from arbolbmas import ArbolBMas, NodoHojaBP, NodoInternoBP


class ArbolBMasOriginalGuia(ArbolBMas):
    """Reproduce _reparar_hoja_subpoblada exactamente como aparece en la guia,
    es decir, SIN propagar el subpoblamiento del padre hacia arriba."""

    def _reparar_hoja_subpoblada(self, hoja, codigo_referencia):
        padre, idx_en_padre, hermano_izq, hermano_der = self._localizar_contexto(hoja, codigo_referencia)

        if hermano_der and len(hermano_der.claves) > self.t - 1:
            hoja.claves.append(hermano_der.claves.pop(0))
            hoja.libros.append(hermano_der.libros.pop(0))
            padre.claves[idx_en_padre] = hermano_der.claves[0]
            return

        if hermano_izq and len(hermano_izq.claves) > self.t - 1:
            hoja.claves.insert(0, hermano_izq.claves.pop())
            hoja.libros.insert(0, hermano_izq.libros.pop())
            padre.claves[idx_en_padre - 1] = hoja.claves[0]
            return

        if hermano_der:
            hoja.claves.extend(hermano_der.claves)
            hoja.libros.extend(hermano_der.libros)
            hoja.siguiente = hermano_der.siguiente
            padre.claves.pop(idx_en_padre)
            padre.hijos.pop(idx_en_padre + 1)
        elif hermano_izq:
            hermano_izq.claves.extend(hoja.claves)
            hermano_izq.libros.extend(hoja.libros)
            hermano_izq.siguiente = hoja.siguiente
            padre.claves.pop(idx_en_padre - 1)
            padre.hijos.pop(idx_en_padre)
        # (sin propagacion hacia arriba: asi termina la funcion en la guia)


def es_arbol_valido(arbol):
    """Verifica invariantes minimas de B+: cada nodo interno no-raiz con
    >= t-1 claves, y cada hoja no-raiz con >= t-1 claves."""
    problemas = []

    def _rec(nodo, es_raiz):
        if nodo.es_hoja:
            if not es_raiz and len(nodo.claves) < arbol.t - 1:
                problemas.append(f"Hoja subpoblada: {len(nodo.claves)} claves (< t-1={arbol.t-1})")
            return
        if not es_raiz and len(nodo.claves) < arbol.t - 1:
            problemas.append(f"Nodo interno subpoblado: {len(nodo.claves)} claves (< t-1={arbol.t-1})")
        if len(nodo.hijos) != len(nodo.claves) + 1:
            problemas.append(f"Nodo interno con {len(nodo.claves)} claves pero {len(nodo.hijos)} hijos (deberia ser {len(nodo.claves)+1})")
        for h in nodo.hijos:
            _rec(h, False)

    _rec(arbol.raiz, True)
    return len(problemas) == 0, problemas


if __name__ == "__main__":
    import random
    random.seed(99)

    print("=== Verificando el algoritmo de eliminacion TAL COMO aparece en la guia ===\n")
    t = 2
    n = 40
    codigos = [f"{i:03d}" for i in range(n)]
    random.shuffle(codigos)

    arbol = ArbolBMasOriginalGuia(t=t)
    for c in codigos:
        arbol.insertar(c, {'titulo': f'Obra {c}', 'autor': 'A'})

    print(f"Arbol construido: {n} claves, t={t}, altura={arbol.altura()}")
    ok, problemas = es_arbol_valido(arbol)
    print(f"Valido tras insercion: {ok}\n")

    orden_elim = codigos.copy()
    random.shuffle(orden_elim)

    primer_fallo = None
    for i, c in enumerate(orden_elim):
        arbol.eliminar(c)
        ok, problemas = es_arbol_valido(arbol)
        if not ok and primer_fallo is None:
            primer_fallo = (i, c, problemas)

    if primer_fallo:
        i, c, problemas = primer_fallo
        print(f"CONFIRMADO: el algoritmo de la guia (sin propagacion hacia arriba) "
              f"rompe la invariante B+ en la eliminacion #{i+1} (codigo '{c}'):")
        for p in problemas:
            print(f"  - {p}")
    else:
        print("No se detectaron violaciones en esta corrida (probar con mas datos/ordenes distintos).")
