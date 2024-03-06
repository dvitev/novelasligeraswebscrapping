import React from "react";
import Iframe from "@/components/Iframe";

const cargarSitio=()=>{
  return fetch("http://localhost:8000/api/sitios/1/?format=json", { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos);
}

export default async function page() {
  const datos = await cargarSitio();
  console.log(datos)
  return (
    <>
      <h1>{datos.nombre} - {datos.url} - {datos.idioma}</h1>
      <div className="novel">
        <div className="novelPanel">
          <Iframe src={datos.url} />
        </div>
        <div className="novelOptions">
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
          <div className="">
            <button>a</button>
          </div>
        </div>
      </div>
    </>
  );
}
