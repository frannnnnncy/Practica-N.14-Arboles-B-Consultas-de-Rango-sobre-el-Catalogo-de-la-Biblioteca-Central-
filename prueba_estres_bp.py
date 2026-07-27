"""
Trabajo de Investigacion (punto 2): prueba de estres sobre el arbol B+ de
la Actividad 5: 5,000 eliminaciones aleatorias seguidas de consultas de
rango repetidas, verificando que la lista enlazada de hojas permanece
consistente (sin ciclos, sin huecos) usando recorrer_todo_el_catalogo().
"""
import random
import time
from arbolbmas import ArbolBMas

# Reconstruir el mismo catalogo de 80,000 codigos de la Actividad 5
random.seed(42)
codigos = sorted(set(f'{random.randint(0,999):03d}.{random.randint(0,999):03d}'
                      for _ in range(85_000)))[:80_000]
random.shuffle(codigos)

catalogo_bp = ArbolBMas(t=50)
for i, cod in enumerate(codigos):
    catalogo_bp.insertar(cod, {'titulo': f'Obra {i}', 'autor': f'Autor {i%500}'})

print(f'Catalogo base reconstruido: {len(catalogo_bp.recorrer_todo_el_catalogo())} libros, '
      f'altura={catalogo_bp.altura()}')

# --- Prueba de estres: 5,000 eliminaciones aleatorias ---
random.seed(123)
a_eliminar = random.sample(codigos, 5_000)

for cod in a_eliminar:
    catalogo_bp.eliminar(cod)

restantes = catalogo_bp.recorrer_todo_el_catalogo()
print(f'5,000 eliminaciones completadas. Libros restantes: {len(restantes)} '
      f'(esperado: {80_000 - 5_000})')

# --- Consultas de rango repetidas tras las eliminaciones ---
rangos_prueba = [('004.000', '004.999'), ('000.000', '099.999'),
                  ('500.000', '599.999'), ('900.000', '999.999')]

print('\nConsultas de rango repetidas tras las 5,000 eliminaciones:')
codigos_restantes = set(codigos) - set(a_eliminar)
for cmin, cmax in rangos_prueba:
    t0 = time.perf_counter()
    resultado = catalogo_bp.rango(cmin, cmax)
    ms = (time.perf_counter() - t0) * 1000
    esperado = sorted(c for c in codigos_restantes if cmin <= c <= cmax)
    coincide = len(resultado) == len(esperado)
    print(f'  [{cmin}, {cmax}]: {len(resultado)} resultados en {ms:.3f}ms '
          f'(esperado: {len(esperado)}, coincide: {coincide})')

# --- Verificacion critica: lista enlazada sin ciclos, sin huecos ---
ok, msg = catalogo_bp.verificar_lista_enlazada()
print(f'\nVerificacion de la lista enlazada de hojas: {msg}')

# Verificacion cruzada final con recorrer_todo_el_catalogo()
todos = catalogo_bp.recorrer_todo_el_catalogo()
print(f'recorrer_todo_el_catalogo(): {len(todos)} libros (esperado: {len(codigos_restantes)})')

exito = ok and len(todos) == len(codigos_restantes) and len(restantes) == 80_000 - 5_000
print(f'\nPRUEBA DE ESTRES: {"EXITOSA - lista enlazada consistente tras 5,000 eliminaciones" if exito else "FALLIDA"}')
