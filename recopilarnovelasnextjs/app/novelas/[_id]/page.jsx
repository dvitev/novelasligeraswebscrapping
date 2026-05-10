import {
  getNovela,
  getCapitulosNovela,
  getConteoCapitulos,
  getContenidosCapitulos,
} from "@/lib/api";
import NovelDetail from "./NovelDetail";
import Link from "next/link";

export async function generateMetadata({ params }) {
  const { _id } = params;
  const novelaResult = await getNovela(_id);
  const novela = novelaResult.data;

  if (!novela) {
    return {
      title: "Novela no encontrada - Recopilador de Novelas",
    };
  }

  const generos = novela.generos?.join(", ") || "Novela";

  return {
    title: `${novela.titulo} - Recopilador de Novelas`,
    description: `Lee ${novela.titulo}. ${generos}. ${novela.sinopsis?.substring(0, 150) || ""}`,
    openGraph: {
      title: `${novela.titulo} - Recopilador de Novelas`,
      description: novela.sinopsis?.substring(0, 150) || `Lee ${novela.titulo}`,
      type: "article",
      authors: novela.autor ? [novela.autor] : undefined,
    },
  };
}

export default async function NovelaPage({ params }) {
  const { _id } = params;

  const [novelaResult, capitulosResult, conteoResult, contenidosResult] = await Promise.all([
    getNovela(_id),
    getCapitulosNovela(_id),
    getConteoCapitulos(_id),
    getContenidosCapitulos(_id),
  ]);

  const novela = novelaResult.data;
  
  if (!novela) {
    return (
      <div className="error-container">
        <span className="error-icon">⚠️</span>
        <h2>Novela no encontrada</h2>
        <p>No se pudo cargar la información de la novela.</p>
        <Link href="/" className="btn btn-process" style={{ width: "auto" }}>
          ← Volver al inicio
        </Link>
      </div>
    );
  }

  const contenidos = contenidosResult.data || [];
  const capituloIdsConContenido = new Set(
    contenidos.map(c => {
      if (typeof c.capitulo_id === 'object' && c.capitulo_id !== null) {
        return c.capitulo_id._id || c.capitulo_id.$oid || c.capitulo_id.toString();
      }
      return String(c.capitulo_id);
    })
  );

  return (
    <NovelDetail
      novela={novela}
      capitulos={capitulosResult.data || []}
      conteo={conteoResult.data || { cantidad_capitulos: 0, cantidad_contenido_capitulos: 0 }}
      capituloIdsConContenido={capituloIdsConContenido}
    />
  );
}
