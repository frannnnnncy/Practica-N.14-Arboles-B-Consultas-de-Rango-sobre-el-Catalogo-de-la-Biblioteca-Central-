// ── catalogo_bp.hpp — Arbol B+ en C++17 (insercion + rango + eliminacion) ──
#pragma once
#include <vector>
#include <memory>
#include <string>
#include <iostream>
#include <stdexcept>
#include <functional>
#include <algorithm>

struct LibroBP {
    std::string titulo, autor;
};

struct NodoBP {
    bool esHoja;
    std::vector<std::string> claves;

    // Datos usados solo si esHoja == true
    std::vector<LibroBP> libros;
    NodoBP* siguiente = nullptr;  // puntero crudo, lista enlazada de hojas

    // Hijos usados solo si esHoja == false (propiedad exclusiva -> unique_ptr)
    std::vector<std::unique_ptr<NodoBP>> hijos;

    explicit NodoBP(bool hoja) : esHoja(hoja) {}
};

class ArbolBMasCpp {
    int t;
    std::unique_ptr<NodoBP> raiz;
    NodoBP* primeraHoja;  // ancla para recorrer todo el catalogo (no posee memoria)

    struct ResultadoSplit {
        bool huboSplit = false;
        std::string claveSubida;
        std::unique_ptr<NodoBP> nuevoHermano;
    };

    ResultadoSplit insertarRec(NodoBP* nodo, const std::string& codigo, LibroBP libro) {
        if (nodo->esHoja) {
            size_t i = 0;
            while (i < nodo->claves.size() && codigo > nodo->claves[i]) i++;
            nodo->claves.insert(nodo->claves.begin() + i, codigo);
            nodo->libros.insert(nodo->libros.begin() + i, std::move(libro));
            if ((int)nodo->claves.size() <= 2 * t - 1) return {};
            return splitHoja(nodo);
        } else {
            size_t i = 0;
            while (i < nodo->claves.size() && codigo >= nodo->claves[i]) i++;
            ResultadoSplit r = insertarRec(nodo->hijos[i].get(), codigo, std::move(libro));
            if (!r.huboSplit) return {};
            nodo->claves.insert(nodo->claves.begin() + i, r.claveSubida);
            nodo->hijos.insert(nodo->hijos.begin() + i + 1, std::move(r.nuevoHermano));
            if ((int)nodo->claves.size() <= 2 * t - 1) return {};
            return splitInterno(nodo);
        }
    }

    ResultadoSplit splitHoja(NodoBP* hoja) {
        size_t mitad = hoja->claves.size() / 2;
        auto nueva = std::make_unique<NodoBP>(true);
        nueva->claves.assign(hoja->claves.begin() + mitad, hoja->claves.end());
        nueva->libros.assign(hoja->libros.begin() + mitad, hoja->libros.end());
        hoja->claves.resize(mitad);
        hoja->libros.resize(mitad);

        nueva->siguiente = hoja->siguiente;  // CRITICO: mantener la lista enlazada
        NodoBP* nuevaPtr = nueva.get();
        hoja->siguiente = nuevaPtr;

        ResultadoSplit r;
        r.huboSplit = true;
        r.claveSubida = nueva->claves[0];
        r.nuevoHermano = std::move(nueva);
        return r;
    }

    ResultadoSplit splitInterno(NodoBP* nodo) {
        size_t mitad = nodo->claves.size() / 2;
        std::string claveMedia = nodo->claves[mitad];
        auto nuevo = std::make_unique<NodoBP>(false);
        nuevo->claves.assign(nodo->claves.begin() + mitad + 1, nodo->claves.end());
        for (size_t k = mitad + 1; k < nodo->hijos.size(); k++)
            nuevo->hijos.push_back(std::move(nodo->hijos[k]));
        nodo->claves.resize(mitad);
        nodo->hijos.resize(mitad + 1);

        ResultadoSplit r;
        r.huboSplit = true;
        r.claveSubida = claveMedia;
        r.nuevoHermano = std::move(nuevo);
        return r;
    }

    NodoBP* bajarAHoja(const std::string& codigo) const {
        NodoBP* nodo = raiz.get();
        while (!nodo->esHoja) {
            size_t i = 0;
            while (i < nodo->claves.size() && codigo >= nodo->claves[i]) i++;
            nodo = nodo->hijos[i].get();
        }
        return nodo;
    }

    // ---------------------------------------------------------------
    // Eliminacion, con propagacion recursiva de subpoblamiento hacia
    // arriba (extension frente a la guia original, ver informe).
    // ---------------------------------------------------------------
    struct Contexto {
        NodoBP* padre = nullptr;
        int idx = -1;
        NodoBP* hermanoIzq = nullptr;
        NodoBP* hermanoDer = nullptr;
    };

    Contexto localizarContexto(NodoBP* objetivo, const std::string& codigoRef) {
        std::vector<std::pair<NodoBP*, int>> camino;
        NodoBP* nodo = raiz.get();
        while (!nodo->esHoja) {
            size_t i = 0;
            while (i < nodo->claves.size() && codigoRef >= nodo->claves[i]) i++;
            camino.push_back({nodo, (int)i});
            nodo = nodo->hijos[i].get();
        }
        if (camino.empty()) return {};
        auto [padre, idx] = camino.back();
        Contexto ctx;
        ctx.padre = padre;
        ctx.idx = idx;
        ctx.hermanoIzq = (idx > 0) ? padre->hijos[idx - 1].get() : nullptr;
        ctx.hermanoDer = (idx < (int)padre->hijos.size() - 1) ? padre->hijos[idx + 1].get() : nullptr;
        return ctx;
    }

    Contexto localizarContextoInterno(NodoBP* objetivo) {
        if (objetivo == raiz.get()) return {};
        std::vector<std::pair<NodoBP*, int>> camino;
        std::function<bool(NodoBP*)> buscar = [&](NodoBP* actual) -> bool {
            if (actual == objetivo) return true;
            if (actual->esHoja) return false;
            for (size_t i = 0; i < actual->hijos.size(); i++) {
                camino.push_back({actual, (int)i});
                if (actual->hijos[i].get() == objetivo || buscar(actual->hijos[i].get())) return true;
                camino.pop_back();
            }
            return false;
        };
        buscar(raiz.get());
        if (camino.empty()) return {};
        auto [padre, idx] = camino.back();
        Contexto ctx;
        ctx.padre = padre;
        ctx.idx = idx;
        ctx.hermanoIzq = (idx > 0) ? padre->hijos[idx - 1].get() : nullptr;
        ctx.hermanoDer = (idx < (int)padre->hijos.size() - 1) ? padre->hijos[idx + 1].get() : nullptr;
        return ctx;
    }

    void repararInternoSubpoblado(NodoBP* nodo) {
        if (nodo == raiz.get()) {
            if (!nodo->esHoja && nodo->claves.empty() && nodo->hijos.size() == 1) {
                raiz = std::move(nodo->hijos[0]);
            }
            return;
        }
        if ((int)nodo->claves.size() >= t - 1) return;

        Contexto ctx = localizarContextoInterno(nodo);
        if (!ctx.padre) return;
        NodoBP* padre = ctx.padre;
        int idx = ctx.idx;

        if (ctx.hermanoDer && (int)ctx.hermanoDer->claves.size() > t - 1) {
            nodo->claves.push_back(padre->claves[idx]);
            nodo->hijos.push_back(std::move(ctx.hermanoDer->hijos.front()));
            ctx.hermanoDer->hijos.erase(ctx.hermanoDer->hijos.begin());
            padre->claves[idx] = ctx.hermanoDer->claves.front();
            ctx.hermanoDer->claves.erase(ctx.hermanoDer->claves.begin());
            return;
        }
        if (ctx.hermanoIzq && (int)ctx.hermanoIzq->claves.size() > t - 1) {
            nodo->claves.insert(nodo->claves.begin(), padre->claves[idx - 1]);
            nodo->hijos.insert(nodo->hijos.begin(), std::move(ctx.hermanoIzq->hijos.back()));
            ctx.hermanoIzq->hijos.pop_back();
            padre->claves[idx - 1] = ctx.hermanoIzq->claves.back();
            ctx.hermanoIzq->claves.pop_back();
            return;
        }
        if (ctx.hermanoDer) {
            nodo->claves.push_back(padre->claves[idx]);
            for (auto& c : ctx.hermanoDer->claves) nodo->claves.push_back(c);
            for (auto& h : ctx.hermanoDer->hijos) nodo->hijos.push_back(std::move(h));
            padre->claves.erase(padre->claves.begin() + idx);
            padre->hijos.erase(padre->hijos.begin() + idx + 1);
        } else if (ctx.hermanoIzq) {
            ctx.hermanoIzq->claves.push_back(padre->claves[idx - 1]);
            for (auto& c : nodo->claves) ctx.hermanoIzq->claves.push_back(c);
            for (auto& h : nodo->hijos) ctx.hermanoIzq->hijos.push_back(std::move(h));
            padre->claves.erase(padre->claves.begin() + idx - 1);
            padre->hijos.erase(padre->hijos.begin() + idx);
        }
        repararInternoSubpoblado(padre);
    }

    void repararHojaSubpoblada(NodoBP* hoja, const std::string& codigoRef) {
        Contexto ctx = localizarContexto(hoja, codigoRef);
        if (!ctx.padre) return;
        NodoBP* padre = ctx.padre;
        int idx = ctx.idx;

        if (ctx.hermanoDer && (int)ctx.hermanoDer->claves.size() > t - 1) {
            hoja->claves.push_back(ctx.hermanoDer->claves.front());
            hoja->libros.push_back(ctx.hermanoDer->libros.front());
            ctx.hermanoDer->claves.erase(ctx.hermanoDer->claves.begin());
            ctx.hermanoDer->libros.erase(ctx.hermanoDer->libros.begin());
            padre->claves[idx] = ctx.hermanoDer->claves[0];
            return;
        }
        if (ctx.hermanoIzq && (int)ctx.hermanoIzq->claves.size() > t - 1) {
            hoja->claves.insert(hoja->claves.begin(), ctx.hermanoIzq->claves.back());
            hoja->libros.insert(hoja->libros.begin(), ctx.hermanoIzq->libros.back());
            ctx.hermanoIzq->claves.pop_back();
            ctx.hermanoIzq->libros.pop_back();
            padre->claves[idx - 1] = hoja->claves[0];
            return;
        }
        if (ctx.hermanoDer) {
            for (auto& c : ctx.hermanoDer->claves) hoja->claves.push_back(c);
            for (auto& l : ctx.hermanoDer->libros) hoja->libros.push_back(l);
            hoja->siguiente = ctx.hermanoDer->siguiente;
            padre->claves.erase(padre->claves.begin() + idx);
            padre->hijos.erase(padre->hijos.begin() + idx + 1);
        } else if (ctx.hermanoIzq) {
            for (auto& c : hoja->claves) ctx.hermanoIzq->claves.push_back(c);
            for (auto& l : hoja->libros) ctx.hermanoIzq->libros.push_back(l);
            ctx.hermanoIzq->siguiente = hoja->siguiente;
            padre->claves.erase(padre->claves.begin() + idx - 1);
            padre->hijos.erase(padre->hijos.begin() + idx);
        }
        repararInternoSubpoblado(padre);
    }

public:
    explicit ArbolBMasCpp(int orden = 4) : t(orden) {
        raiz = std::make_unique<NodoBP>(true);
        primeraHoja = raiz.get();
    }

    void insertar(const std::string& codigo, LibroBP libro) {
        ResultadoSplit r = insertarRec(raiz.get(), codigo, std::move(libro));
        if (r.huboSplit) {
            auto nuevaRaiz = std::make_unique<NodoBP>(false);
            nuevaRaiz->claves.push_back(r.claveSubida);
            nuevaRaiz->hijos.push_back(std::move(raiz));
            nuevaRaiz->hijos.push_back(std::move(r.nuevoHermano));
            raiz = std::move(nuevaRaiz);
        }
    }

    const LibroBP* buscar(const std::string& codigo) const {
        NodoBP* hoja = bajarAHoja(codigo);
        for (size_t i = 0; i < hoja->claves.size(); i++)
            if (hoja->claves[i] == codigo) return &hoja->libros[i];
        return nullptr;
    }

    std::vector<LibroBP> rango(const std::string& codMin, const std::string& codMax) const {
        std::vector<LibroBP> resultados;
        NodoBP* hoja = bajarAHoja(codMin);
        while (hoja) {
            for (size_t i = 0; i < hoja->claves.size(); i++) {
                if (hoja->claves[i] > codMax) return resultados;
                if (hoja->claves[i] >= codMin) resultados.push_back(hoja->libros[i]);
            }
            hoja = hoja->siguiente;
        }
        return resultados;
    }

    void eliminar(const std::string& codigo) {
        NodoBP* hoja = bajarAHoja(codigo);
        auto it = std::find(hoja->claves.begin(), hoja->claves.end(), codigo);
        if (it == hoja->claves.end()) throw std::runtime_error("Codigo no encontrado: " + codigo);
        size_t idx = it - hoja->claves.begin();
        hoja->claves.erase(hoja->claves.begin() + idx);
        hoja->libros.erase(hoja->libros.begin() + idx);
        if ((int)hoja->claves.size() >= t - 1 || hoja == raiz.get()) return;
        repararHojaSubpoblada(hoja, codigo);
    }

    int altura() const {
        int h = 0;
        NodoBP* n = raiz.get();
        while (!n->esHoja) { h++; n = n->hijos[0].get(); }
        return h;
    }

    std::vector<LibroBP> recorrerTodoElCatalogo() const {
        std::vector<LibroBP> resultados;
        NodoBP* hoja = primeraHoja;
        while (hoja) {
            for (auto& l : hoja->libros) resultados.push_back(l);
            hoja = hoja->siguiente;
        }
        return resultados;
    }

    bool verificarListaEnlazada() const {
        NodoBP* hoja = primeraHoja;
        std::string anterior;
        bool primera = true;
        long visitas = 0;
        while (hoja) {
            for (auto& c : hoja->claves) {
                if (!primera && c < anterior) return false;
                anterior = c;
                primera = false;
            }
            hoja = hoja->siguiente;
            if (++visitas > 10000000L) return false;
        }
        return true;
    }
};
