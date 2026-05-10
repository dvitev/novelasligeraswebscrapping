import { getSitio, getNovelasDelSitio, getGeneros } from "@/lib/api";
import SitioContent from "./SitioContent";
import Link from "next/link";

export async function generateMetadata({ params }) {
  const { _id } = params;
  const sitio = await getSitio(_id);

  if (!sitio) {
    return {
      title: "Sitio no encontrado - Recopilador de Novelas",
    };
  }

  return {
    title: `${sitio.nombre} - Recopilador de Novelas`,
    description: `Explora las novelas disponibles en ${sitio.nombre}. ${sitio.url || ""}`,
    openGraph: {
      title: `${sitio.nombre} - Recopilador de Novelas`,
      description: `Explora las novelas disponibles en ${sitio.nombre}.`,
      type: "website",
    },
  };
}

export default async function SitioPage({ params }) {
  const { _id } = params;

  const [sitio, novelas, generos] = await Promise.all([
    getSitio(_id),
    getNovelasDelSitio(_id),
    getGeneros(_id),
  ]);

  if (!sitio) {
    return (
      <div className="error-container">
        <span className="error-icon">⚠️</span>
        <h2>Sitio no encontrado</h2>
        <p>No se pudo cargar la información del sitio.</p>
        <Link href="/" className="btn btn-process" style={{ width: "auto" }}>
          ← Volver al inicio
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="appbar">
        <Link href="/" className="appbar-back">←</Link>
        <span className="appbar-title">
          <span className="icon">📚</span>
          {sitio.nombre}
        </span>
      </div>

      <div className="site-header">
        <div className="icon-circle">🌐</div>
        <div className="site-header-info">
          <h1>{sitio.nombre}</h1>
          <p className="url">{sitio.url || "N/A"}</p>
        </div>
        <div className="stat-badge">
          <span className="number">{novelas.length}</span>
          <span className="label">novelas</span>
        </div>
      </div>

      <SitioContent novelas={novelas} generos={generos} />
    </>
  );
}
