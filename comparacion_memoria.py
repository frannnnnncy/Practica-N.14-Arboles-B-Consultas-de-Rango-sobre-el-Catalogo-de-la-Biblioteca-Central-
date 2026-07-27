"""
Trabajo de Investigacion (punto 3): comparar cuantitativamente (con datos
propios, midiendo con sys.getsizeof de forma recursiva) el espacio en
memoria estimado entre indexar 80,000 libros con arbol B (Practica 13,
datos duplicados en nodos internos) vs arbol B+ (esta practica, datos
solo en hojas).
"""
import sys
import random
from arbolbmas import ArbolBMas

# ---------------------------------------------------------------------
# Modelo simplificado del arbol B de la Practica 13 (misma estructura de
# datos: NodoB con claves+libros paralelos en CADA nodo, incluyendo
# internos), reconstruido aqui solo para medir memoria de forma
# comparable, sin repetir toda la logica de insercion/eliminacion.
# ---------------------------------------------------------------------
class NodoB_Simulado:
    __slots__ = ('claves', 'libros', 'hijos', 'es_hoja')

    def __init__(self, es_hoja=True):
        self.claves = []
        self.libros = []  # en el arbol B, TODOS los nodos (incluyendo internos) guardan datos
        self.hijos = []
        self.es_hoja = es_hoja


def tamano_recursivo(obj_inicial):
    """Calcula el tamano total en bytes de una estructura de nodos enlazados,
    sumando sys.getsizeof de cada objeto visitado (evitando doble conteo).
    Implementado de forma ITERATIVA (pila explicita) para evitar el limite
    de recursion de Python al recorrer la lista enlazada de miles de hojas."""
    visitados = set()
    pila = [obj_inicial]
    total = 0
    while pila:
        obj = pila.pop()
        if id(obj) in visitados:
            continue
        visitados.add(id(obj))
        total += sys.getsizeof(obj)
        if isinstance(obj, dict):
            for k, v in obj.items():
                pila.append(k)
                pila.append(v)
        elif isinstance(obj, (list, tuple, set)):
            pila.extend(obj)
        elif hasattr(obj, '__slots__'):
            for slot in obj.__slots__:
                if hasattr(obj, slot):
                    pila.append(getattr(obj, slot))
        elif hasattr(obj, '__dict__'):
            pila.extend(obj.__dict__.values())
    return total


def construir_libro(i):
    # Registro representativo de un libro real (similar al usado en Practica 13/14)
    return {'titulo': f'Obra de prueba numero {i} de la coleccion UNA-PUNO',
            'autor': f'Autor Apellido {i % 500}',
            'disponible': True}


def construir_arbol_b_simulado(t, codigos):
    """Construye un arbol B (Practica 13) simplificado, insertando los
    datos DUPLICADOS en nodos internos cuando una clave asciende en un
    split, tal como ocurre en el algoritmo real de la Practica 13."""
    raiz = NodoB_Simulado(es_hoja=True)

    def split(padre, i, y):
        z = NodoB_Simulado(es_hoja=y.es_hoja)
        z.claves = y.claves[t:]
        z.libros = y.libros[t:]
        if not y.es_hoja:
            z.hijos = y.hijos[t:]
        clave_media = y.claves[t - 1]
        libro_medio = y.libros[t - 1]
        y.claves = y.claves[:t - 1]
        y.libros = y.libros[:t - 1]
        if not y.es_hoja:
            y.hijos = y.hijos[:t]
        padre.hijos.insert(i + 1, z)
        padre.claves.insert(i, clave_media)
        padre.libros.insert(i, libro_medio)

    def insertar_no_lleno(nodo, codigo, libro):
        i = len(nodo.claves) - 1
        if nodo.es_hoja:
            nodo.claves.append(None)
            nodo.libros.append(None)
            while i >= 0 and codigo < nodo.claves[i]:
                nodo.claves[i + 1] = nodo.claves[i]
                nodo.libros[i + 1] = nodo.libros[i]
                i -= 1
            nodo.claves[i + 1] = codigo
            nodo.libros[i + 1] = libro
        else:
            while i >= 0 and codigo < nodo.claves[i]:
                i -= 1
            i += 1
            if len(nodo.hijos[i].claves) == 2 * t - 1:
                split(nodo, i, nodo.hijos[i])
                if codigo > nodo.claves[i]:
                    i += 1
            insertar_no_lleno(nodo.hijos[i], codigo, libro)

    arbol = {'raiz': raiz}

    def insertar(codigo, libro):
        r = arbol['raiz']
        if len(r.claves) == 2 * t - 1:
            s = NodoB_Simulado(es_hoja=False)
            s.hijos.append(r)
            split(s, 0, r)
            arbol['raiz'] = s
        insertar_no_lleno(arbol['raiz'], codigo, libro)

    for i, cod in enumerate(codigos):
        insertar(cod, construir_libro(i))

    return arbol['raiz']


if __name__ == "__main__":
    random.seed(42)
    N = 80_000
    codigos = sorted(set(f'{random.randint(0,999):03d}.{random.randint(0,999):03d} '
                          f'{chr(65+random.randint(0,25))}{random.randint(1,99)}'
                          for _ in range(int(N * 1.06))))[:N]
    random.shuffle(codigos)

    print(f'Comparando memoria real para {len(codigos)} libros indexados...\n')

    print('Construyendo arbol B (Practica 13, t=50, datos duplicados en internos)...')
    raiz_b = construir_arbol_b_simulado(t=50, codigos=codigos)
    mem_b = tamano_recursivo(raiz_b)

    print('Construyendo arbol B+ (esta practica, t=50, datos solo en hojas)...')
    arbol_bp = ArbolBMas(t=50)
    for i, cod in enumerate(codigos):
        arbol_bp.insertar(cod, construir_libro(i))
    mem_bp = tamano_recursivo(arbol_bp.raiz)

    print(f'\nMemoria real medida (sys.getsizeof recursivo, incluye overhead de objetos Python):')
    print(f'  Arbol B  (Practica 13): {mem_b:,} bytes ({mem_b/1_048_576:.2f} MB)')
    print(f'  Arbol B+ (esta practica): {mem_bp:,} bytes ({mem_bp/1_048_576:.2f} MB)')
    print(f'  Diferencia: {mem_b - mem_bp:,} bytes ({(mem_b-mem_bp)/1_048_576:.2f} MB), '
          f'B+ usa {(1 - mem_bp/mem_b)*100:.1f}% menos memoria')

    # Contar cuantas copias de "libro" completo existen en cada estructura
    def contar_libros_en_nodos(nodo, es_hoja_attr='es_hoja'):
        total = len(nodo.libros)
        if not nodo.es_hoja:
            for h in nodo.hijos:
                total += contar_libros_en_nodos(h)
        return total

    copias_b = contar_libros_en_nodos(raiz_b)

    def contar_libros_bp(nodo):
        if nodo.es_hoja:
            return len(nodo.libros)
        return sum(contar_libros_bp(h) for h in nodo.hijos)

    copias_bp = contar_libros_bp(arbol_bp.raiz)

    print(f'\nCopias totales de registros de libro almacenadas:')
    print(f'  Arbol B:  {copias_b:,} copias para {len(codigos):,} libros unicos '
          f'({copias_b - len(codigos):,} copias duplicadas en nodos internos por splits)')
    print(f'  Arbol B+: {copias_bp:,} copias para {len(codigos):,} libros unicos '
          f'(0 duplicados: los internos solo tienen claves guia)')

    # --- Repetir la comparacion con un orden pequeno (t=5) para mostrar
    # como el ahorro de memoria escala con la proporcion de nodos internos ---
    print(f'\n=== Repitiendo la comparacion con t=5 (arbol mas "alto", mas nodos internos) ===')
    raiz_b5 = construir_arbol_b_simulado(t=5, codigos=codigos)
    mem_b5 = tamano_recursivo(raiz_b5)

    arbol_bp5 = ArbolBMas(t=5)
    for i, cod in enumerate(codigos):
        arbol_bp5.insertar(cod, construir_libro(i))
    mem_bp5 = tamano_recursivo(arbol_bp5.raiz)

    print(f'  Arbol B  (t=5): {mem_b5:,} bytes ({mem_b5/1_048_576:.2f} MB)')
    print(f'  Arbol B+ (t=5): {mem_bp5:,} bytes ({mem_bp5/1_048_576:.2f} MB)')
    print(f'  Diferencia: {mem_b5 - mem_bp5:,} bytes, B+ usa '
          f'{(1 - mem_bp5/mem_b5)*100:.1f}% menos memoria con t=5 '
          f'(frente a {(1 - mem_bp/mem_b)*100:.1f}% con t=50)')
