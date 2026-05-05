import { getSitios } from "@/lib/api";
import Link from "next/link";

export default async function HomePage() {
  const sitios = await getSitios();

  return (
    <>
      <div className="home-header">
        <h1>📖 Novelas Manager</h1>
        <p>Gestiona y descarga tus novelas favoritas</p>
        <div className="badge">
          🌐 {sitios.length} Sitios disponibles
        </div>
      </div>

      <p className="home-subtitle">📚 Selecciona un sitio para explorar</p>

      <div className="grid grid-sites">
        {sitios.map((sitio) => (
          <Link key={sitio._id} href={`/sitios/${sitio._id}`}>
            <div className="site-card">
              <div className="icon-circle">🌐</div>
              <span className="site-name">{sitio.nombre}</span>
              <span className="site-url">
                {sitio.url?.length > 30
                  ? sitio.url.slice(0, 30) + "…"
                  : sitio.url || "Sin URL"}
              </span>
            </div>
          </Link>
        ))}
      </div>

      {sitios.length === 0 && (
        <div className="empty-state">
          <span style={{ fontSize: 40 }}>📭</span>
          <p>No se encontraron sitios. Verifica la conexión con la API.</p>
        </div>
      )}
    </>
  );
}
