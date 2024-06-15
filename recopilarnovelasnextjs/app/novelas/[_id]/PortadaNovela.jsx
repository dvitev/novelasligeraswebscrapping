"use client";

import Image from "next/image";

const cargador = ({ src, width, height }) => {
  return `${src}?w=${width}&h=${height}`;
};

export default function PortadaNovela({ imagen_url }) {
  return (
    <Image loader={cargador} src={imagen_url} width={160} height={200} className="ListadoNovelaPortada" alt={imagen_url}/>
  );
}
