import React from "react";
import Iframe from "@/components/Iframe";
import ListadoNovelas from "./ListadoNovelas";

const cargarSitio = (id) => {
  return fetch(`http://localhost:8000/api/sitios/${id}/`, { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos);
};

const cargarNovelas = (sitio_id) => {
  return fetch(`http://localhost:8000/api/novelas/sitio/${sitio_id}/`, {
    cache: "no-store",
  })
    .then((res) => res.json())
    .then((datos) => datos);
};

export default async function page({ params }) {
  const { _id } = params;
  const datos = await cargarSitio(_id);
  // console.log(datos);
  const novelas = await cargarNovelas(datos._id);
  // console.log(novelas);
  return (
    <>
      <h1>
        {datos.nombre} - {datos.url} - {datos.idioma}
      </h1>
      <div className="novel">
        {/* <div className="novelPanel">
          <Iframe src={datos.url}/>
        </div> */}
        <ListadoNovelas novelas={novelas} />
      </div>
    </>
  );
}
