"use client";
import Iframe from "@/components/Iframe";
import React, { useState } from "react";
// import CapturaIndividualBoton from "./CapturaIndividualBoton";

export default function ListadoCapitulos({ capitulos, novela_id }) {
  const [url, setUrl] = useState("");
  const [_id, set_id] = useState("");
  //   console.log(capitulos);
  return (
    <>
      <div className="novel">
        <div className="novelPanel">
          <Iframe src={url} _id={_id} />
        </div>
        <div className="listadoCapitulos">
          {capitulos.map((cap) => (
            <div
              className={
                url === cap.url ? "capitulo capituloactivo" : "capitulo"
              }
              key={cap._id}
              id={cap._id}
              onClick={() => {
                setUrl(cap.url);
                set_id(cap._id);
              }}
              style={{ cursor: "pointer" }}
            >
              {cap.nombre}
            </div>
          ))}
        </div>
      </div>
      {/* {url !== "" ? (
        <div className="opcionesCapituloNovela">
          <CapturaIndividualBoton
            novela_id={novela_id}
            capitulo_id={_id}
          />
          <div>Captura Masiva</div>
        </div>
      ) : null} */}
    </>
  );
}
