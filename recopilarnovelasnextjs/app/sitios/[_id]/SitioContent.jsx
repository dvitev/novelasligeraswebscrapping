"use client";

import { useState, useMemo, useCallback } from "react";
import NovelCard from "./NovelCard";

const NOVELS_PER_PAGE = 30;

export default function SitioContent({ novelas, generos }) {
  const [search, setSearch] = useState("");
  const [genero, setGenero] = useState("");
  const [pagina, setPagina] = useState(1);

  // Filtrar novelas por búsqueda y género
  const novelasFiltradas = useMemo(() => {
    let resultado = novelas;

    if (search.trim()) {
      const q = search.toLowerCase();
      resultado = resultado.filter((n) =>
        n.nombre.toLowerCase().includes(q)
      );
    }

    if (genero) {
      resultado = resultado.filter((n) =>
        n.genero?.includes(genero)
      );
    }

    return resultado;
  }, [novelas, search, genero]);

  const totalPaginas = Math.max(
    1,
    Math.ceil(novelasFiltradas.length / NOVELS_PER_PAGE)
  );

  // Resetear página al cambiar filtros
  const paginaActual = Math.min(pagina, totalPaginas);

  const novelasPagina = useMemo(() => {
    const inicio = (paginaActual - 1) * NOVELS_PER_PAGE;
    return novelasFiltradas.slice(inicio, inicio + NOVELS_PER_PAGE);
  }, [novelasFiltradas, paginaActual]);

  const handleSearchChange = useCallback((e) => {
    setSearch(e.target.value);
    setPagina(1);
  }, []);

  const handleGeneroChange = useCallback((e) => {
    setGenero(e.target.value);
    setPagina(1);
  }, []);

  const irPagina = useCallback(
    (p) => {
      const nueva = Math.max(1, Math.min(p, totalPaginas));
      setPagina(nueva);
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [totalPaginas]
  );

  return (
    <>
      {/* Toolbar: búsqueda + filtro género */}
      <div className="toolbar">
        <div className="search-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Buscar novela…"
            value={search}
            onChange={handleSearchChange}
          />
        </div>

        {generos.length > 0 && (
          <select
            className="filter-select"
            value={genero}
            onChange={handleGeneroChange}
          >
            <option value="">Todos los géneros</option>
            {generos.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Paginación superior */}
      {totalPaginas > 1 && (
        <Pagination
          pagina={paginaActual}
          total={totalPaginas}
          onPageChange={irPagina}
        />
      )}

      {/* Grid de novelas */}
      {novelasPagina.length > 0 ? (
        <div className="grid grid-novels">
          {novelasPagina.map((novela) => (
            <NovelCard key={novela._id} novela={novela} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <span style={{ fontSize: 40 }}>📭</span>
          <p>No se encontraron novelas con los filtros seleccionados.</p>
        </div>
      )}

      {/* Paginación inferior */}
      {totalPaginas > 1 && (
        <Pagination
          pagina={paginaActual}
          total={totalPaginas}
          onPageChange={irPagina}
        />
      )}
    </>
  );
}

// ── Componente de Paginación ──────────────────────────────
function Pagination({ pagina, total, onPageChange }) {
  const [gotoValue, setGotoValue] = useState("");

  const handleGotoChange = (e) => {
    const val = e.target.value;
    setGotoValue(val);
    const num = parseInt(val, 10);
    if (!isNaN(num) && num >= 1 && num <= total) {
      onPageChange(num);
    }
  };

  return (
    <div className="pagination">
      <button
        className="pagination-btn"
        disabled={pagina <= 1}
        onClick={() => onPageChange(pagina - 1)}
        title="Página anterior"
      >
        ‹
      </button>

      <div className="pagination-info">
        <span className="current">{pagina}</span>
        <span className="separator">/</span>
        <span className="total">{total}</span>
      </div>

      <button
        className="pagination-btn"
        disabled={pagina >= total}
        onClick={() => onPageChange(pagina + 1)}
        title="Página siguiente"
      >
        ›
      </button>

      <div className="pagination-goto">
        <label>Ir a:</label>
        <input
          type="number"
          min="1"
          max={total}
          value={gotoValue}
          onChange={handleGotoChange}
          placeholder={String(pagina)}
        />
      </div>
    </div>
  );
}
