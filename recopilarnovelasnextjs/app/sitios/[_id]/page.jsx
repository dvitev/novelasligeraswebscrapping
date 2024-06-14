"use client";

import { useState, useEffect } from "react";
import ListadoNovelas from "./ListadoNovelas";
import ListGeneros from "./ListGeneros";

const cargarSitio = async (id) => {
  const res = await fetch(`http://192.168.1.11:8000/api/sitios/${id}/`, {
    cache: "no-store",
  });
  const datos = await res.json();
  return datos[0];
};

const cargarGeneros = async (id) => {
  const res = await fetch(`http://192.168.1.11:8000/api/generos/${id}/`, {
    cache: "no-store",
  });
  const datos = await res.json();
  return datos["generos"];
};

const cargarNovelas = async (sitio_id) => {
  const res = await fetch(`http://192.168.1.11:8000/api/novelassitio/${sitio_id}/`, {
    cache: "no-store",
  });
  const datos = await res.json();
  return datos;
};

export default async function page({ params }) {
  const { _id } = params;
  // console.log(_id)
  const [datos, setDatos] = useState({});
  const [generos, setGeneros] = useState([]);
  const [novelas, setNovelas] = useState([]);
  const [novelasFiltradas, setNovelasFiltradas] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const sitioDatos = await cargarSitio(_id);
        const sitioGeneros = await cargarGeneros(_id);
        const sitioNovelas = await cargarNovelas(_id);

        setDatos(sitioDatos);
        setGeneros(sitioGeneros);
        setNovelas(sitioNovelas);
        setNovelasFiltradas(sitioNovelas); // Inicialmente, mostrar todas las novelas
      } catch (error) {
        console.error("Error al cargar los datos:", error);
      }
    };

    fetchData();
  }, [_id]);

  const handleFiltrarNovelas = (genero) => {
    const filtradas = genero
      ? novelas.filter((novela) => novela.genero.includes(genero))
      : novelas;
    setNovelasFiltradas(filtradas);
  };

  return (
    <>
      <h1>
        {datos.nombre} - {datos.url} - {datos.idioma}
      </h1>
      <ListGeneros datos={generos} onFiltrar={handleFiltrarNovelas} />
      <div className="novel">
        <ListadoNovelas novelas={novelas} />
      </div>
    </>
  );
}
