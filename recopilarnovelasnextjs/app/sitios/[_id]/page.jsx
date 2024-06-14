
import ListadoNovelas from "./ListadoNovelas";
import ListGeneros from "./ListGeneros";

const cargarSitio = (id) => {
  return fetch(`http://192.168.1.11:8000/api/sitios/${id}/`, { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos[0]);
};

const cargarGeneros = (id) => {
  return fetch(`http://192.168.1.11:8000/api/generos/${id}/`, { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos['generos']);
};

const cargarNovelas = (sitio_id) => {
  console.log(sitio_id)
  return fetch(`http://192.168.1.11:8000/api/novelassitio/${sitio_id}/`, {
    cache: "no-store",
  })
    .then((res) => res.json())
    .then((datos) => datos);
};

export default async function page({ params }) {
  const { _id } = params;
  // console.log(_id)
  const datos = await cargarSitio(_id);
  // console.log(datos);
  const generos = await cargarGeneros(_id);
  // console.log(generos);
  const novelas = await cargarNovelas(_id)
  // console.log(novelas);
  return (
    <>
      <h1>
        {datos.nombre} - {datos.url} - {datos.idioma}
      </h1>
      <ListGeneros datos={generos}/>
      <div className="novel">
        <ListadoNovelas novelas={novelas} />
      </div>
    </>
  );
}
