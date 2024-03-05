import Ficha from "./Ficha";

const cargarDatos = () => {
  return fetch("https://randomuser.me/api/?results=8", { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos.results);
};

export default async function page() {
  const datos = await cargarDatos();
  return (
    <>
      <div className="personas">
        {datos.map((valor, index) => (
          <Ficha key={index} valor={valor}/>
        ))}
      </div>
    </>
  );
}
