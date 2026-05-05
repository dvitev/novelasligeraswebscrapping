"use client";

import { useState, useMemo, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import { getEpubUrl, getPdfUrl } from "@/lib/api";

const imageLoader = ({ src, width }) => `${src}?w=${width}`;
const CAPS_PER_PAGE = 50;

export default function NovelDetail({ novela, capitulos, conteo }) {
  const [paginaCaps, setPaginaCaps] = useState(1);

  // ── Progreso ──────────────────────────────────────────
  const totalCaps = conteo.cantidad_capitulos || capitulos.length;
  const descargados = conteo.cantidad_contenido_capitulos || 0;
  const porcentaje = totalCaps > 0 ? (descargados / totalCaps) * 100 : 0;
  const allDownloaded = totalCaps > 0 && descargados >= totalCaps;

  // ── Status ────────────────────────────────────────────
  const statusLower = (novela.status || "").toLowerCase();
  const statusColor = statusLower.includes("complet")
    ? "status-completed"
    : statusLower.includes("ongoing") || statusLower.includes("emision")
    ? "status-ongoing"
    : "status-unknown";
  const statusIcon = statusLower.includes("complet") ? "✅" : "⏳";

  // ── Géneros ───────────────────────────────────────────
  const genres = useMemo(
    () =>
      novela.genero
        ? novela.genero.split(",").map((g) => g.trim()).filter(Boolean)
        : [],
    [novela.genero]
  );

  // ── Paginación de capítulos ───────────────────────────
  const totalPaginasCaps = Math.max(
    1,
    Math.ceil(capitulos.length / CAPS_PER_PAGE)
  );
  const paginaActual = Math.min(paginaCaps, totalPaginasCaps);

  const capitulosPagina = useMemo(() => {
    const inicio = (paginaActual - 1) * CAPS_PER_PAGE;
    return capitulos.slice(inicio, inicio + CAPS_PER_PAGE);
  }, [capitulos, paginaActual]);

  const offsetInicial = (paginaActual - 1) * CAPS_PER_PAGE;

  const irPaginaCaps = useCallback(
    (p) => setPaginaCaps(Math.max(1, Math.min(p, totalPaginasCaps))),
    [totalPaginasCaps]
  );

  // ── Goto page handler ────────────────────────────────
  const [gotoValue, setGotoValue] = useState("");
  const handleGotoChange = (e) => {
    const val = e.target.value;
    setGotoValue(val);
    const num = parseInt(val, 10);
    if (!isNaN(num) && num >= 1 && num <= totalPaginasCaps) {
      irPaginaCaps(num);
    }
  };

  return (
    <>
      {/* AppBar */}
      <div className="appbar">
        {novela.sitio_id ? (
          <Link href={`/sitios/${novela.sitio_id}`} className="appbar-back">
            ←
          </Link>
        ) : (
          <Link href="/" className="appbar-back">←</Link>
        )}
        <span className="appbar-title">
          <span className="icon">📖</span>
          {novela.nombre?.length > 40
            ? novela.nombre.slice(0, 40) + "…"
            : novela.nombre}
        </span>
      </div>

      <div className="novel-detail">
        {/* ── Top: Cover + Info ───────────────────────── */}
        <div className="novel-detail-top">
          {/* Cover */}
          <div className="novel-cover-container">
            <div className="novel-cover">
              <Image
                loader={imageLoader}
                src={novela.imagen_url}
                alt={`Portada de ${novela.nombre}`}
                width={180}
                height={250}
                priority
              />
            </div>
            <span className={`novel-status-badge ${statusColor}`}>
              {statusIcon} {novela.status || "N/A"}
            </span>
          </div>

          {/* Info */}
          <div className="novel-info">
            <h1>{novela.nombre}</h1>

            <div className="info-cards">
              <InfoCard
                icon="👤"
                label="Autor"
                value={(novela.autor || "Desconocido").slice(0, 25)}
                color="var(--secondary)"
              />
              <InfoCard
                icon="🏷️"
                label="Género"
                value={
                  genres.length > 0
                    ? genres.slice(0, 2).join(", ").slice(0, 20)
                    : "N/A"
                }
                color="var(--accent-pink)"
              />
              <InfoCard
                icon="📖"
                label="Capítulos"
                value={String(capitulos.length)}
                color="var(--accent-orange)"
              />
            </div>

            {/* Sinopsis */}
            <div className="synopsis-box">
              <h3>📝 Sinopsis</h3>
              <p>
                {novela.sinopsis
                  ? novela.sinopsis.length > 500
                    ? novela.sinopsis.slice(0, 500) + "…"
                    : novela.sinopsis
                  : "Sin sinopsis disponible."}
              </p>
            </div>

            {/* Géneros */}
            {genres.length > 0 && (
              <div className="genre-tags">
                {genres.map((g, i) => (
                  <span key={i} className="genre-tag">{g}</span>
                ))}
              </div>
            )}

            {/* URL original */}
            {novela.url && (
              <div style={{ marginTop: 10 }}>
                <a
                  href={novela.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontSize: 11,
                    color: "var(--primary-light)",
                    textDecoration: "underline",
                  }}
                >
                  🔗 Ver en sitio original
                </a>
              </div>
            )}
          </div>
        </div>

        <div className="divider" />

        {/* ── Bottom: Progress + Chapters ──────────────── */}
        <div className="novel-detail-bottom">
          {/* Progress Panel */}
          <div className="progress-panel">
            <h3>📊 Progreso</h3>

            <div className="progress-numbers">
              <span className="downloaded">{descargados}</span>
              <span className="total">/ {totalCaps}</span>
            </div>

            <div className="progress-bar-container">
              <div
                className={`progress-bar-fill ${
                  porcentaje >= 100 ? "complete" : "partial"
                }`}
                style={{ width: `${Math.min(porcentaje, 100)}%` }}
              />
            </div>

            <span className="progress-percent">
              {porcentaje.toFixed(1)}%
            </span>

            {/* Action Buttons */}
            <div className="action-buttons">
              <a
                href={allDownloaded ? getEpubUrl(novela._id) : undefined}
                target="_blank"
                rel="noopener noreferrer"
                className={`btn btn-epub ${!allDownloaded ? "disabled-link" : ""}`}
                style={!allDownloaded ? { pointerEvents: "none", opacity: 0.4 } : {}}
              >
                📖 EPUB
              </a>
              <a
                href={allDownloaded ? getPdfUrl(novela._id) : undefined}
                target="_blank"
                rel="noopener noreferrer"
                className={`btn btn-pdf ${!allDownloaded ? "disabled-link" : ""}`}
                style={!allDownloaded ? { pointerEvents: "none", opacity: 0.4 } : {}}
              >
                📄 PDF
              </a>
            </div>

            {!allDownloaded && (
              <p
                style={{
                  fontSize: 10,
                  color: "var(--text-muted)",
                  textAlign: "center",
                  marginTop: 4,
                }}
              >
                ⚠️ Faltan {totalCaps - descargados} capítulos por descargar para
                habilitar la exportación.
              </p>
            )}
          </div>

          {/* Chapters List */}
          <div className="chapters-panel">
            <div className="chapters-header">
              <h3>📋 Capítulos</h3>
              <span className="count-badge">
                {descargados}/{totalCaps}
              </span>
            </div>

            {/* Chapters Pagination */}
            {totalPaginasCaps > 1 && (
              <div className="pagination">
                <button
                  className="pagination-btn"
                  disabled={paginaActual <= 1}
                  onClick={() => irPaginaCaps(paginaActual - 1)}
                >
                  ‹
                </button>
                <div className="pagination-info">
                  <span className="current">{paginaActual}</span>
                  <span className="separator">/</span>
                  <span className="total">{totalPaginasCaps}</span>
                </div>
                <button
                  className="pagination-btn"
                  disabled={paginaActual >= totalPaginasCaps}
                  onClick={() => irPaginaCaps(paginaActual + 1)}
                >
                  ›
                </button>
                <div className="pagination-goto">
                  <label>Ir a:</label>
                  <input
                    type="number"
                    min="1"
                    max={totalPaginasCaps}
                    value={gotoValue}
                    onChange={handleGotoChange}
                    placeholder={String(paginaActual)}
                  />
                </div>
              </div>
            )}

            {/* Chapter items */}
            <div className="chapter-list">
              {capitulosPagina.map((cap, idx) => {
                const globalIdx = offsetInicial + idx + 1;
                return (
                  <div key={cap._id} className="chapter-item">
                    <div className="chapter-index">{globalIdx}</div>
                    <div className="chapter-info">
                      <p className="chapter-name">
                        {cap.nombre?.length > 60
                          ? cap.nombre.slice(0, 60) + "…"
                          : cap.nombre}
                      </p>
                      <p className="chapter-date">
                        {cap.created_at
                          ? new Date(cap.created_at).toLocaleDateString("es-ES")
                          : "Sin fecha"}
                      </p>
                    </div>
                    <span className="chapter-status-icon">○</span>
                  </div>
                );
              })}
            </div>

            {capitulos.length === 0 && (
              <div className="empty-state">
                <p>No hay capítulos registrados para esta novela.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

// ── Info Card Component ───────────────────────────────────
function InfoCard({ icon, label, value, color }) {
  return (
    <div className="info-card">
      <span className="info-icon" style={{ color }}>
        {icon}
      </span>
      <span className="info-label">{label}</span>
      <span className="info-value">{value}</span>
    </div>
  );
}
