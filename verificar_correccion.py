import random
from arbolbmas import ArbolBMas
from verificar_bug_guia import es_arbol_valido

random.seed(99)

t = 2
n = 40
codigos = [f"{i:03d}" for i in range(n)]
random.shuffle(codigos)

arbol = ArbolBMas(t=t)
for c in codigos:
    arbol.insertar(c, {'titulo': f'Obra {c}', 'autor': 'A'})

print(f"Arbol construido: {n} claves, t={t}, altura={arbol.altura()}")
ok, problemas = es_arbol_valido(arbol)
print(f"Valido tras insercion: {ok}\n")

orden_elim = codigos.copy()
random.shuffle(orden_elim)

fallos = []
for i, c in enumerate(orden_elim):
    arbol.eliminar(c)
    ok, problemas = es_arbol_valido(arbol)
    ok_lista, msg_lista = arbol.verificar_lista_enlazada()
    if not ok or not ok_lista:
        fallos.append((i, c, problemas, msg_lista))

print(f"Eliminaciones realizadas: {len(orden_elim)}")
print(f"Fallos de invariante B+ detectados: {len(fallos)}")
if fallos:
    for f in fallos[:5]:
        print(" ", f)
else:
    print("CORRECCION VERIFICADA: con la propagacion recursiva hacia arriba, "
          "el arbol se mantiene valido durante las 40 eliminaciones (mismo "
          "escenario que rompio el algoritmo original de la guia en la eliminacion #23).")

print(f"\nEstado final: {arbol.contar_claves() if hasattr(arbol, 'contar_claves') else len(arbol.recorrer_todo_el_catalogo())} libros restantes")
ok_lista, msg_lista = arbol.verificar_lista_enlazada()
print(f"Lista enlazada final: {msg_lista}")
