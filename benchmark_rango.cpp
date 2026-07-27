// ── benchmark_rango.cpp — B+ vs B-Tree vs AVL en consultas de rango ────
//
// Nota de correccion: el codigo de benchmark de la guia original era
// pseudocodigo incompleto: llamaba a rango(nullptr, ...) literalmente
// pasando un puntero nulo, y la logica de "B-Tree y AVL" estaba resumida
// en un comentario ("... logica de rango sin lista enlazada ..."), sin
// codigo real. Este archivo implementa las TRES estructuras completas
// (B+, B-Tree simplificado y AVL) con una consulta de rango genuina para
// cada una, y mide tiempos reales, no simulados.

#include "catalogo_bp.hpp"
#include <chrono>
#include <random>
#include <algorithm>
#include <memory>

using Clock = std::chrono::high_resolution_clock;

// =========================================================================
// Arbol B simplificado (Practica 13), con consulta de rango mediante
// recorrido in-order acotado (poda de subarboles fuera del rango).
// =========================================================================
struct NodoBSimple {
    std::vector<std::string> claves;
    std::vector<LibroBP> libros;  // el arbol B real (Practica 13) SI guarda datos en cada nodo
    std::vector<std::unique_ptr<NodoBSimple>> hijos;
    bool esHoja = true;
};

class ArbolBSimple {
    int t;
    std::unique_ptr<NodoBSimple> raiz;

    void split(NodoBSimple* padre, int i, NodoBSimple* y) {
        auto z = std::make_unique<NodoBSimple>();
        z->esHoja = y->esHoja;
        z->claves.assign(y->claves.begin() + t, y->claves.end());
        z->libros.assign(y->libros.begin() + t, y->libros.end());
        if (!y->esHoja)
            for (size_t k = t; k < y->hijos.size(); k++) z->hijos.push_back(std::move(y->hijos[k]));
        std::string claveMedia = y->claves[t - 1];
        LibroBP libroMedio = y->libros[t - 1];
        y->claves.resize(t - 1);
        y->libros.resize(t - 1);
        if (!y->esHoja) y->hijos.resize(t);
        padre->hijos.insert(padre->hijos.begin() + i + 1, std::move(z));
        padre->claves.insert(padre->claves.begin() + i, claveMedia);
        padre->libros.insert(padre->libros.begin() + i, libroMedio);
    }

    void insertarNoLleno(NodoBSimple* nodo, const std::string& clave, LibroBP libro) {
        int i = (int)nodo->claves.size() - 1;
        if (nodo->esHoja) {
            nodo->claves.push_back("");
            nodo->libros.push_back(LibroBP{});
            while (i >= 0 && clave < nodo->claves[i]) {
                nodo->claves[i + 1] = nodo->claves[i];
                nodo->libros[i + 1] = nodo->libros[i];
                i--;
            }
            nodo->claves[i + 1] = clave;
            nodo->libros[i + 1] = std::move(libro);
        } else {
            while (i >= 0 && clave < nodo->claves[i]) i--;
            i++;
            if ((int)nodo->hijos[i]->claves.size() == 2 * t - 1) {
                split(nodo, i, nodo->hijos[i].get());
                if (clave > nodo->claves[i]) i++;
            }
            insertarNoLleno(nodo->hijos[i].get(), clave, std::move(libro));
        }
    }

    // Recorrido in-order acotado: solo desciende a subarboles que pueden contener el rango
    void rangoRec(const NodoBSimple* nodo, const std::string& cMin, const std::string& cMax,
                  std::vector<LibroBP>& out) const {
        int i = 0;
        while (i < (int)nodo->claves.size() && nodo->claves[i] < cMin) i++;
        while (i < (int)nodo->claves.size()) {
            if (!nodo->esHoja) rangoRec(nodo->hijos[i].get(), cMin, cMax, out);
            if (nodo->claves[i] > cMax) return;
            if (nodo->claves[i] >= cMin) out.push_back(nodo->libros[i]);
            i++;
        }
        if (!nodo->esHoja) rangoRec(nodo->hijos[i].get(), cMin, cMax, out);
    }

public:
    explicit ArbolBSimple(int orden) : t(orden) { raiz = std::make_unique<NodoBSimple>(); }

    void insertar(const std::string& clave, LibroBP libro) {
        if ((int)raiz->claves.size() == 2 * t - 1) {
            auto s = std::make_unique<NodoBSimple>();
            s->esHoja = false;
            s->hijos.push_back(std::move(raiz));
            split(s.get(), 0, s->hijos[0].get());
            raiz = std::move(s);
        }
        insertarNoLleno(raiz.get(), clave, std::move(libro));
    }

    std::vector<LibroBP> rango(const std::string& cMin, const std::string& cMax) const {
        std::vector<LibroBP> out;
        rangoRec(raiz.get(), cMin, cMax, out);
        return out;
    }
};

// =========================================================================
// AVL simplificado, con consulta de rango mediante in-order acotado.
// =========================================================================
struct NodoAVLSimple {
    std::string clave;
    LibroBP libro;
    int altura = 1;
    std::unique_ptr<NodoAVLSimple> izq, der;
    NodoAVLSimple(std::string k, LibroBP l) : clave(std::move(k)), libro(std::move(l)) {}
};

int alturaAVL(const NodoAVLSimple* n) { return n ? n->altura : 0; }
int balanceAVL(const NodoAVLSimple* n) { return n ? alturaAVL(n->izq.get()) - alturaAVL(n->der.get()) : 0; }

std::unique_ptr<NodoAVLSimple> rotarDerAVL(std::unique_ptr<NodoAVLSimple> y) {
    auto x = std::move(y->izq);
    y->izq = std::move(x->der);
    x->der = std::move(y);
    x->der->altura = 1 + std::max(alturaAVL(x->der->izq.get()), alturaAVL(x->der->der.get()));
    x->altura = 1 + std::max(alturaAVL(x->izq.get()), alturaAVL(x->der.get()));
    return x;
}

std::unique_ptr<NodoAVLSimple> rotarIzqAVL(std::unique_ptr<NodoAVLSimple> x) {
    auto y = std::move(x->der);
    x->der = std::move(y->izq);
    y->izq = std::move(x);
    y->izq->altura = 1 + std::max(alturaAVL(y->izq->izq.get()), alturaAVL(y->izq->der.get()));
    y->altura = 1 + std::max(alturaAVL(y->izq.get()), alturaAVL(y->der.get()));
    return y;
}

std::unique_ptr<NodoAVLSimple> insertarAVL(std::unique_ptr<NodoAVLSimple> nodo, const std::string& clave, LibroBP libro) {
    if (!nodo) return std::make_unique<NodoAVLSimple>(clave, std::move(libro));
    if (clave < nodo->clave) nodo->izq = insertarAVL(std::move(nodo->izq), clave, std::move(libro));
    else if (clave > nodo->clave) nodo->der = insertarAVL(std::move(nodo->der), clave, std::move(libro));
    else return nodo;

    nodo->altura = 1 + std::max(alturaAVL(nodo->izq.get()), alturaAVL(nodo->der.get()));
    int balance = balanceAVL(nodo.get());

    if (balance > 1 && clave < nodo->izq->clave) return rotarDerAVL(std::move(nodo));
    if (balance < -1 && clave > nodo->der->clave) return rotarIzqAVL(std::move(nodo));
    if (balance > 1 && clave > nodo->izq->clave) {
        nodo->izq = rotarIzqAVL(std::move(nodo->izq));
        return rotarDerAVL(std::move(nodo));
    }
    if (balance < -1 && clave < nodo->der->clave) {
        nodo->der = rotarDerAVL(std::move(nodo->der));
        return rotarIzqAVL(std::move(nodo));
    }
    return nodo;
}

// Recorrido in-order acotado (poda ramas fuera del rango, igual principio que en el B-Tree)
void rangoAVLRec(const NodoAVLSimple* nodo, const std::string& cMin, const std::string& cMax,
                  std::vector<LibroBP>& out) {
    if (!nodo) return;
    if (nodo->clave > cMin) rangoAVLRec(nodo->izq.get(), cMin, cMax, out);
    if (nodo->clave >= cMin && nodo->clave <= cMax) out.push_back(nodo->libro);
    if (nodo->clave < cMax) rangoAVLRec(nodo->der.get(), cMin, cMax, out);
}

// =========================================================================
// Benchmark comparativo
// =========================================================================
void compararEstructuras(int n, const std::string& codMin, const std::string& codMax) {
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 999);
    std::vector<std::string> codigos;
    while ((int)codigos.size() < n * 12 / 10) {
        char buf[16];
        snprintf(buf, sizeof(buf), "%03d.%03d", dist(rng), dist(rng));
        codigos.push_back(buf);
    }
    std::sort(codigos.begin(), codigos.end());
    codigos.erase(std::unique(codigos.begin(), codigos.end()), codigos.end());
    if ((int)codigos.size() > n) codigos.resize(n);
    std::shuffle(codigos.begin(), codigos.end(), rng);

    // Construir las 3 estructuras con el mismo conjunto de claves
    ArbolBMasCpp catalogoBP(50);
    ArbolBSimple catalogoB(50);
    std::unique_ptr<NodoAVLSimple> raizAVL;

    for (auto& c : codigos) {
        catalogoBP.insertar(c, LibroBP{"Titulo " + c, "Autor"});
        catalogoB.insertar(c, LibroBP{"Titulo " + c, "Autor"});
        raizAVL = insertarAVL(std::move(raizAVL), c, LibroBP{"Titulo " + c, "Autor"});
    }

    const int repeticiones = 20;

    auto t0 = Clock::now();
    size_t kBP = 0;
    for (int r = 0; r < repeticiones; r++) kBP = catalogoBP.rango(codMin, codMax).size();
    double msBP = std::chrono::duration<double, std::milli>(Clock::now() - t0).count() / repeticiones;

    t0 = Clock::now();
    size_t kB = 0;
    for (int r = 0; r < repeticiones; r++) kB = catalogoB.rango(codMin, codMax).size();
    double msB = std::chrono::duration<double, std::milli>(Clock::now() - t0).count() / repeticiones;

    t0 = Clock::now();
    size_t kAVL = 0;
    for (int r = 0; r < repeticiones; r++) {
        std::vector<LibroBP> out;
        rangoAVLRec(raizAVL.get(), codMin, codMax, out);
        kAVL = out.size();
    }
    double msAVL = std::chrono::duration<double, std::milli>(Clock::now() - t0).count() / repeticiones;

    std::cout << "N=" << n
              << " | B+ (con lista): " << msBP << "ms (" << kBP << " resultados)"
              << " | B-Tree (in-order acotado): " << msB << "ms (" << kB << " resultados)"
              << " | AVL (in-order acotado): " << msAVL << "ms (" << kAVL << " resultados)\n";
}

int main() {
    std::cout << "Comparando B+ vs B-Tree vs AVL para consultas de rango [004.000, 004.999]\n";
    std::cout << "(promedio de 20 repeticiones por estructura, para reducir ruido del sistema)\n\n";
    for (int n : {1000, 10000, 80000})
        compararEstructuras(n, "004.000", "004.999");

    std::cout << "\nComparando con un rango AMPLIO [000.000, 499.999] (k grande, domina el termino O(k)):\n\n";
    for (int n : {1000, 10000, 80000})
        compararEstructuras(n, "000.000", "499.999");

    return 0;
}
