import ListadoCapitulos from "./ListadoCapitulos";

const cargarNovela = (id) => {
  return fetch(`http://192.168.1.11:8000/api/novelas/${id}/`, {
    cache: "no-store",
  })
    .then((res) => res.json())
    .then((datos) => datos[0]);
};

const cargarCapitulosNovela = (id) => {
  return fetch(`http://192.168.1.11:8000/api/capitulosnovela/${id}/`, {
    cache: "no-store",
  })
    .then((res) => res.json())
    .then((datos) => datos);
};

const enviarContenidoCapitulo=()=>{

};

export default async function page({ params }) {
  const { _id } = params;
  const datos = await cargarNovela(_id);
  // console.log(datos);
  const capitulos = await cargarCapitulosNovela(_id);
  // console.log(capitulos);
  return (
    <>
      <h1>
        {datos.nombre}
      </h1>
      <ListadoCapitulos capitulos={capitulos} novela_id={_id}/>
    </>
  );
}
