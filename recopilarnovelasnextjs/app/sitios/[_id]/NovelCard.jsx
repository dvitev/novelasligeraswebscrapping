"use client";

import Image from "next/image";
import Link from "next/link";

const imageLoader = ({ src, width }) => `${src}?w=${width}`;

function getStatusInfo(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("complet"))
    return { className: "status-completed", label: status || "Completo" };
  if (s.includes("ongoing") || s.includes("emision"))
    return { className: "status-ongoing", label: status || "En emisión" };
  return { className: "status-unknown", label: status || "Desconocido" };
}

const NO_COVER = "/imagenes/no-cover.svg";

export default function NovelCard({ novela }) {
  const { className: statusClass, label: statusLabel } = getStatusInfo(
    novela.status
  );
  const coverSrc = novela.imagen_url || NO_COVER;

  return (
    <Link href={`/novelas/${novela._id}`}>
      <div className="novel-card">
        <Image
          loader={imageLoader}
          src={coverSrc}
          alt={`Portada de ${novela.nombre}`}
          width={170}
          height={245}
          style={{ objectFit: "cover" }}
        />
        <div className="overlay" />
        <div className="card-content">
          <span className={`status-badge ${statusClass}`}>
            {statusLabel.slice(0, 15)}
          </span>
          <div className="card-bottom">
            <p className="novel-name">{novela.nombre}</p>
            <p className="novel-author">
              ✍️ {(novela.autor || "Desconocido").slice(0, 20)}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
