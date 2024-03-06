import React from "react";
import Iframe from "@/components/Iframe";

const cargarSitio=(id)=>{
  return fetch(`http://localhost:8000/api/sitios/${id}/`, { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos);
}

const cargarNovela=(_id)=>{
  return fetch(`http://localhost:8000/api/novelas/${_id}/`, { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos);
}

export default async function page({params}) {
  const {_id} = params
  const datos = await cargarSitio(_id);
  console.log(datos)
  return (
    <>
      <h1>{datos.nombre} - {datos.url} - {datos.idioma}</h1>
      <div className="novel">
        {/* <div className="novelPanel">
          <Iframe src={datos.url}/>
        </div> */}
        <div className="novelOptions">
          <div >
            <button>Opcion1</button>
          </div>
          <div>
            <button>Opcion2</button>
          </div>
          <div>
            <button>Opcion3</button>
          </div>
          <div>
            <button>Opcion4</button>
          </div>
          <div>
            <button>Opcion5</button>
          </div>
          <div>
            <button>Opcion6</button>
          </div>
          <div>
            <button>Opcion7</button>
          </div>
          <div>
            <button>Opcion8</button>
          </div>
        </div>
      </div>
    </>
  );
}
