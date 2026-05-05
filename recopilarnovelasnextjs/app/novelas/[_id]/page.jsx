import {
  getNovela,
  getCapitulosNovela,
  getConteoCapitulos,
} from "@/lib/api";
import NovelDetail from "./NovelDetail";
import Link from "next/link";

export default async function NovelaPage({ params }) {
  const { _id } = params;

  const [novela, capitulos, conteo] = await Promise.all([
    getNovela(_id),
    getCapitulosNovela(_id),
    getConteoCapitulos(_id),
  ]);

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

  return (
    <NovelDetail
      novela={novela}
      capitulos={capitulos}
      conteo={conteo}
    />
  );
}
