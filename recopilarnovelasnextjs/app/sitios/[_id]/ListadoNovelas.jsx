"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";

const cargador = ({ src, width, height }) => {
  return `${src}?w=${width}&h=${height}`;
};

export default function ListadoNovelas({ novelas }) {
  const [novelasFiltradas, setNovelasFiltradas] = useState(novelas); // Estado para las novelas filtradas
  const [generoFiltrado, setGeneroFiltrado] = useState("");

  // useEffect para aplicar el filtro cuando el género filtrado cambia
  useEffect(() => {
    if (generoFiltrado) {
      const filteredNovelas = novelas.filter((novela) =>
        novela.genero.includes(generoFiltrado)
      );
      setNovelasFiltradas(filteredNovelas);
    } else {
      setNovelasFiltradas(novelas); // Mostrar todas las novelas si no hay género filtrado
    }
  }, [generoFiltrado, novelas]);

  return (
    <div className="novelOptions">
      {Array.isArray(novelasFiltradas) ? (
        novelasFiltradas.map((novela, idx) => (
          <div className="NovelDiv" key={novela._id}>
            <Link href={`/novelas/${novela._id}`}>
              <Image
                loader={cargador}
                src={novela.imagen_url}
                width={150}
                height={200}
                className="ListadoNovelaPortada"
                alt={`Portada de ${novela.nombre}`}
              />
              <p>{novela.nombre}</p>
              <input type="hidden" name={`${novela.genero}`} />
            </Link>
          </div>
        ))
      ) : (
        <p>No hay novelas disponibles.</p>
      )}
    </div>
  );
}
