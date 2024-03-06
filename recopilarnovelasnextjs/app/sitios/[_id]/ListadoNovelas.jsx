"use client";

import Image from "next/image";
import Link from "next/link";
const cargador = ({ src, width, height }) => {
  return `${src}?w=${width}&h=${height}`;
};

export default function ListadoNovelas({ novelas }) {
  return (
    <div className="novelOptions">
      {Array.isArray(novelas) ? (
        novelas.map((novela, idx) => (
          <Link href={`/novelas/${novela._id}`} key={idx}>
            <Image
              loader={cargador}
              src={novela.imagen_url}
              width={150}
              height={200}
            />
            <p>{novela.nombre}</p>
            <p>{novela.genero}</p>
          </Link>
        ))
      ) : (
        <Link href={`/novelas/${novelas._id}`}>
          <Image
            loader={cargador}
            src={novelas.imagen_url}
            width={150}
            height={200}
          />
          <h3>{novelas.nombre}</h3>
          <p>{novelas.genero}</p>
        </Link>
      )}
    </div>
  );
}
