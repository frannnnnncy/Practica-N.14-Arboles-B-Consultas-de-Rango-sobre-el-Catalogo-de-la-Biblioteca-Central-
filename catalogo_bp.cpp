// ── catalogo_bp.cpp — Prueba del Arbol B+ (Actividad 6) ────────────────
#include "catalogo_bp.hpp"

int main() {
    ArbolBMasCpp arbol(4);

    std::vector<std::string> codigos = {
        "004.100", "004.250", "004.678", "004.900", "005.133",
        "003.050", "003.900", "006.010", "006.500", "004.300",
        "004.050", "002.100", "007.200", "004.999", "004.001"
    };

    std::cout << "=== Practica 14 - Actividad 6: insercion y busqueda B+ en C++17 ===\n";
    for (auto& c : codigos) arbol.insertar(c, LibroBP{"Titulo " + c, "Autor"});
    std::cout << "Altura tras insertar " << codigos.size() << " codigos (t=4): " << arbol.altura() << "\n";

    auto* lib = arbol.buscar("004.678");
    std::cout << "Buscar 004.678: " << (lib ? "encontrado (" + lib->titulo + ")" : "no encontrado") << "\n";
    auto* lib2 = arbol.buscar("999.999");
    std::cout << "Buscar 999.999: " << (lib2 ? "encontrado" : "no encontrado") << "\n";

    std::cout << "\n=== Consulta de rango [004.000, 004.999] ===\n";
    auto resultados = arbol.rango("004.000", "004.999");
    std::cout << "Resultados encontrados: " << resultados.size() << "\n";
    for (auto& r : resultados) std::cout << "  " << r.titulo << "\n";

    std::cout << "\n=== Practica 14 - Extension: eliminacion B+ en C++17 ===\n";
    arbol.eliminar("004.678");
    auto* lib3 = arbol.buscar("004.678");
    std::cout << "Tras eliminar 004.678 -> buscar: " << (lib3 ? "encontrado (ERROR)" : "no encontrado (correcto)") << "\n";

    arbol.eliminar("003.050");
    arbol.eliminar("006.010");
    std::cout << "Altura tras 3 eliminaciones: " << arbol.altura() << "\n";
    std::cout << "Lista enlazada consistente: " << (arbol.verificarListaEnlazada() ? "SI" : "NO") << "\n";

    auto resultados2 = arbol.rango("004.000", "004.999");
    std::cout << "Rango [004.000, 004.999] tras eliminaciones: " << resultados2.size() << " resultados\n";

    int total = arbol.recorrerTodoElCatalogo().size();
    std::cout << "Total en catalogo (recorrerTodoElCatalogo): " << total
              << " (esperado: " << (codigos.size() - 3) << ")\n";

    return 0;
}
