import ListadoCapitulos from "./ListadoCapitulos";
import PortadaNovela from "./PortadaNovela";
import Link from "next/link";
import ValidarBotonesDescarga from "./ValidarBotonesDescarga";

// Utiliza un cargador de imágenes para optimizar las imágenes.
const cargador = ({ src, width, height }) => {
  return `${src}?w=${width}&h=${height}`;
};

// Función para cargar datos de una novela específica.
const cargarNovela = async (id) => {
  const res = await fetch(`http://192.168.1.11:8000/api/novelas/${id}/`, {
    cache: "no-store",
  });
  const datos = await res.json();
  return datos[0];
};

// Función para cargar los capítulos de una novela específica.
const cargarCapitulosNovela = async (id) => {
  const res = await fetch(`http://192.168.1.11:8000/api/capitulosnovela/${id}/`, {
    cache: "no-store",
  });
  const datos = await res.json();
  return datos;
};

// Componente de página principal.
export default async function Page({ params }) {
  const { _id } = params;

  // Carga los datos de la novela y sus capítulos.
  const datos = await cargarNovela(_id);
  const capitulos = await cargarCapitulosNovela(_id);

  return (
    <>
      <h1>{datos.nombre}</h1>
      <ListadoCapitulos capitulos={capitulos} novela_id={_id} />
      <div className="novelDownload">
        <ValidarBotonesDescarga novela_id = {datos._id}/>
      </div>
      <div className="contenedordatosnovela">
        <div className="contenedorportada">
          <PortadaNovela imagen_url={datos.imagen_url} />
        </div>
        <div className="contenedorsinopsis">
          <div className="sinopsisdato">
            <h4>novela_id</h4>
            <p>{datos._id}</p>
          </div>
          <div className="sinopsisdato">
            <h4>nombre_novela:</h4>
            <p>{datos.nombre}</p>
          </div>
          <div className="sinopsisdato">
            <h4>Capitulos:</h4>
            <p>{capitulos.length}</p>
          </div>
          <div className="sinopsisdato">
            <h4>sinopsis:</h4>
            <p dangerouslySetInnerHTML={{ __html: datos.sinopsis.replace(/\r\n/g, "<br>") }} />
          </div>
          <div className="sinopsisdato">
            <h4>autor:</h4>
            <p>{datos.autor}</p>
          </div>
          <div className="sinopsisdato">
            <h4>genero:</h4>
            <div className="sinopsisgenerodato">
              {datos.genero.split(", ").map((e, idx) => (
                <label key={idx}>{e}</label>
              ))}
            </div>
          </div>
          <div className="sinopsisdato">
            <h4>status:</h4>
            <p>{datos.status}</p>
          </div>
          <div className="sinopsisdato">
            <h4>url:</h4>
            <Link href={datos.url}>{datos.url}</Link>
          </div>
        </div>
      </div>
    </>
  );
}
