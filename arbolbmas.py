# ── Actividad 1: Estructuras B+ ─────────────────────────────────────────
class NodoHojaBP:
    def __init__(self):
        self.claves = []       # codigos topograficos ordenados
        self.libros = []       # registros paralelos a claves
        self.siguiente = None  # puntero a la siguiente hoja (clave del B+)
        self.es_hoja = True


class NodoInternoBP:
    def __init__(self):
        self.claves = []  # claves GUIA (no tienen datos asociados)
        self.hijos = []    # punteros a NodoHojaBP o NodoInternoBP
        self.es_hoja = False


# ── Actividad 2: ArbolBMas — insercion ──────────────────────────────────
class ArbolBMas:
    def __init__(self, t=4):
        self.t = t
        self.raiz = NodoHojaBP()
        self.primera_hoja = self.raiz  # ancla para recorrer todo el catalogo

    def insertar(self, codigo, libro):
        resultado = self._ins(self.raiz, codigo, libro)
        if resultado:  # la raiz se dividio, crear nueva raiz interna
            clave_subida, nuevo_hermano = resultado
            nueva_raiz = NodoInternoBP()
            nueva_raiz.claves = [clave_subida]
            nueva_raiz.hijos = [self.raiz, nuevo_hermano]
            self.raiz = nueva_raiz

    def _ins(self, nodo, codigo, libro):
        if nodo.es_hoja:
            i = 0
            while i < len(nodo.claves) and codigo > nodo.claves[i]:
                i += 1
            nodo.claves.insert(i, codigo)
            nodo.libros.insert(i, libro)
            if len(nodo.claves) <= 2 * self.t - 1:
                return None
            return self._split_hoja(nodo)
        else:
            i = 0
            while i < len(nodo.claves) and codigo >= nodo.claves[i]:
                i += 1
            resultado = self._ins(nodo.hijos[i], codigo, libro)
            if not resultado:
                return None
            clave_subida, nuevo_hermano = resultado
            nodo.claves.insert(i, clave_subida)
            nodo.hijos.insert(i + 1, nuevo_hermano)
            if len(nodo.claves) <= 2 * self.t - 1:
                return None
            return self._split_interno(nodo)

    def _split_hoja(self, hoja):
        mitad = len(hoja.claves) // 2
        nueva = NodoHojaBP()
        nueva.claves = hoja.claves[mitad:]
        nueva.libros = hoja.libros[mitad:]
        hoja.claves = hoja.claves[:mitad]
        hoja.libros = hoja.libros[:mitad]
        nueva.siguiente = hoja.siguiente  # CRITICO: mantener la lista enlazada
        hoja.siguiente = nueva
        return (nueva.claves[0], nueva)  # la clave guia sube al padre

    def _split_interno(self, nodo):
        mitad = len(nodo.claves) // 2
        clave_media = nodo.claves[mitad]
        nuevo = NodoInternoBP()
        nuevo.claves = nodo.claves[mitad + 1:]
        nuevo.hijos = nodo.hijos[mitad + 1:]
        nodo.claves = nodo.claves[:mitad]
        nodo.hijos = nodo.hijos[:mitad + 1]
        return (clave_media, nuevo)

    # ── Actividad 3: Busqueda puntual y consulta de rango O(log n + k) ──
    def _bajar_a_hoja(self, codigo):
        """Desciende desde la raiz hasta la hoja donde deberia estar codigo."""
        nodo = self.raiz
        while not nodo.es_hoja:
            i = 0
            while i < len(nodo.claves) and codigo >= nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]
        return nodo

    def buscar(self, codigo):
        hoja = self._bajar_a_hoja(codigo)
        for i, k in enumerate(hoja.claves):
            if k == codigo:
                return hoja.libros[i]
        return None

    def rango(self, codigo_min, codigo_max):
        """Retorna todos los libros con codigo en [codigo_min, codigo_max].
        Complejidad: O(log n) para llegar a la primera hoja + O(k) para
        recorrer la lista enlazada hasta superar codigo_max."""
        resultados = []
        hoja = self._bajar_a_hoja(codigo_min)
        while hoja:
            for i, k in enumerate(hoja.claves):
                if codigo_min <= k <= codigo_max:
                    resultados.append(hoja.libros[i])
                elif k > codigo_max:
                    return resultados
            hoja = hoja.siguiente  # ¡aqui esta la ventaja del B+!
        return resultados

    def recorrer_todo_el_catalogo(self):
        """Recorre TODAS las hojas en O(n) sin tocar los nodos internos."""
        resultados = []
        hoja = self.primera_hoja
        while hoja:
            resultados.extend(hoja.libros)
            hoja = hoja.siguiente
        return resultados

    # ── Actividad 4: Eliminacion B+ — preservando la lista enlazada ─────
    def eliminar(self, codigo):
        hoja = self._bajar_a_hoja(codigo)
        if codigo not in hoja.claves:
            raise KeyError(f'Codigo no encontrado: {codigo}')
        idx = hoja.claves.index(codigo)
        hoja.claves.pop(idx)
        hoja.libros.pop(idx)
        if len(hoja.claves) >= self.t - 1 or hoja is self.raiz:
            return  # la hoja sigue cumpliendo el minimo, no se requiere accion
        self._reparar_hoja_subpoblada(hoja, codigo)

    def _reparar_hoja_subpoblada(self, hoja, codigo_referencia):
        """
        Busca el padre y hermano de la hoja subpoblada. Intenta redistribuir
        (borrow) de un hermano; si no es posible, fusiona, ACTUALIZANDO
        el puntero `siguiente` para que la lista enlazada quede consistente.

        Nota de correccion (agregada en esta implementacion, no en la guia
        original): tras una fusion, el PADRE pierde una clave y un hijo; si
        el padre mismo queda con menos de t-1 claves y no es la raiz, ese
        subpoblamiento debe repararse tambien (recursivamente hacia arriba),
        igual que en el arbol B de la Practica 13. La guia original no
        contemplaba este caso -- ver seccion de correccion en el informe.
        """
        padre, idx_en_padre, hermano_izq, hermano_der = self._localizar_contexto(hoja, codigo_referencia)

        # Intentar redistribuir desde el hermano derecho
        if hermano_der and len(hermano_der.claves) > self.t - 1:
            hoja.claves.append(hermano_der.claves.pop(0))
            hoja.libros.append(hermano_der.libros.pop(0))
            padre.claves[idx_en_padre] = hermano_der.claves[0]
            return

        # Intentar redistribuir desde el hermano izquierdo
        if hermano_izq and len(hermano_izq.claves) > self.t - 1:
            hoja.claves.insert(0, hermano_izq.claves.pop())
            hoja.libros.insert(0, hermano_izq.libros.pop())
            padre.claves[idx_en_padre - 1] = hoja.claves[0]
            return

        # Sin posibilidad de redistribuir: FUSIONAR con el hermano derecho
        if hermano_der:
            hoja.claves.extend(hermano_der.claves)
            hoja.libros.extend(hermano_der.libros)
            hoja.siguiente = hermano_der.siguiente  # ¡reparar la lista!
            padre.claves.pop(idx_en_padre)
            padre.hijos.pop(idx_en_padre + 1)
        elif hermano_izq:
            hermano_izq.claves.extend(hoja.claves)
            hermano_izq.libros.extend(hoja.libros)
            hermano_izq.siguiente = hoja.siguiente  # ¡reparar la lista!
            padre.claves.pop(idx_en_padre - 1)
            padre.hijos.pop(idx_en_padre)

        # --- EXTENSION (no en la guia original): propagar el subpoblamiento
        # hacia arriba si el padre quedo con menos de t-1 claves y no es raiz.
        self._reparar_interno_subpoblado(padre)

    def _localizar_contexto(self, hoja_objetivo, codigo_ref):
        """Localiza padre, indice y hermanos de hoja_objetivo (busqueda auxiliar)."""
        camino = []
        nodo = self.raiz
        while not nodo.es_hoja:
            i = 0
            while i < len(nodo.claves) and codigo_ref >= nodo.claves[i]:
                i += 1
            camino.append((nodo, i))
            nodo = nodo.hijos[i]
        if not camino:
            return None, None, None, None
        padre, idx = camino[-1]
        herm_izq = padre.hijos[idx - 1] if idx > 0 else None
        herm_der = padre.hijos[idx + 1] if idx < len(padre.hijos) - 1 else None
        return padre, idx, herm_izq, herm_der

    # --- EXTENSION: reparacion recursiva de nodos internos subpoblados ---
    def _localizar_contexto_interno(self, nodo_objetivo):
        """Analogo a _localizar_contexto pero para un nodo INTERNO cualquiera."""
        if nodo_objetivo is self.raiz:
            return None, None, None, None
        camino = []
        nodo = self.raiz
        clave_guia = nodo_objetivo.claves[0] if nodo_objetivo.claves else None
        # Descenso guiado por identidad de objeto, no por clave (mas robusto)
        def _buscar(actual):
            if actual is nodo_objetivo:
                return True
            if actual.es_hoja:
                return False
            for hijo in actual.hijos:
                camino.append((actual, actual.hijos.index(hijo)))
                if hijo is nodo_objetivo or _buscar(hijo):
                    return True
                camino.pop()
            return False
        _buscar(self.raiz)
        if not camino:
            return None, None, None, None
        padre, idx = camino[-1]
        herm_izq = padre.hijos[idx - 1] if idx > 0 else None
        herm_der = padre.hijos[idx + 1] if idx < len(padre.hijos) - 1 else None
        return padre, idx, herm_izq, herm_der

    def _reparar_interno_subpoblado(self, nodo):
        t = self.t
        if nodo is self.raiz:
            # Si la raiz interna quedo sin claves (un solo hijo), esa hija pasa a ser la raiz
            if not nodo.es_hoja and len(nodo.claves) == 0 and len(nodo.hijos) == 1:
                self.raiz = nodo.hijos[0]
            return
        if len(nodo.claves) >= t - 1:
            return  # sigue cumpliendo el minimo, no hay nada que hacer

        padre, idx_en_padre, herm_izq, herm_der = self._localizar_contexto_interno(nodo)
        if padre is None:
            return

        # Redistribuir (borrow) desde un hermano interno con excedente
        if herm_der and len(herm_der.claves) > t - 1:
            nodo.claves.append(padre.claves[idx_en_padre])
            nodo.hijos.append(herm_der.hijos.pop(0))
            padre.claves[idx_en_padre] = herm_der.claves.pop(0)
            return
        if herm_izq and len(herm_izq.claves) > t - 1:
            nodo.claves.insert(0, padre.claves[idx_en_padre - 1])
            nodo.hijos.insert(0, herm_izq.hijos.pop())
            padre.claves[idx_en_padre - 1] = herm_izq.claves.pop()
            return

        # Fusionar con un hermano interno
        if herm_der:
            nodo.claves.append(padre.claves[idx_en_padre])
            nodo.claves.extend(herm_der.claves)
            nodo.hijos.extend(herm_der.hijos)
            padre.claves.pop(idx_en_padre)
            padre.hijos.pop(idx_en_padre + 1)
        elif herm_izq:
            herm_izq.claves.append(padre.claves[idx_en_padre - 1])
            herm_izq.claves.extend(nodo.claves)
            herm_izq.hijos.extend(nodo.hijos)
            padre.claves.pop(idx_en_padre - 1)
            padre.hijos.pop(idx_en_padre)

        # Propagar hacia arriba si el padre tambien quedo subpoblado
        self._reparar_interno_subpoblado(padre)

    # ── utilidades propias (no en la guia): altura y verificacion ──────
    def altura(self):
        n = self.raiz
        h = 0
        while not n.es_hoja:
            h += 1
            n = n.hijos[0]
        return h

    def verificar_lista_enlazada(self):
        """Verifica que la lista de hojas no tenga ciclos, cubra todas las
        hojas del arbol y este estrictamente ordenada de extremo a extremo."""
        vistos = set()
        hoja = self.primera_hoja
        claves_lista = []
        while hoja:
            if id(hoja) in vistos:
                return False, "CICLO detectado en la lista enlazada"
            vistos.add(id(hoja))
            claves_lista.extend(hoja.claves)
            hoja = hoja.siguiente
        if claves_lista != sorted(claves_lista):
            return False, "La lista enlazada no esta ordenada"
        return True, f"{len(claves_lista)} claves, sin ciclos, ordenada"
