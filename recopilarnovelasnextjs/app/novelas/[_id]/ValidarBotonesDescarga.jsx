import BotonesDescarga from "./BotonesDescarga";

const conteoCapitulos =(novela_id)=>{
    return fetch(`http://192.168.1.11:8000/api/conteocapitulosnovela/${novela_id}/`, { cache: "no-store" })
    .then((res) => res.json())
    .then((datos) => datos);
}
export default async function ValidarBotonesDescarga({novela_id}) {
    // console.log(novela_id);
    const conteocap = await conteoCapitulos(novela_id);
    console.log(conteocap);
  return (
    <>{
        conteocap.cantidad_capitulos===conteocap.cantidad_contenido_capitulos ? <BotonesDescarga novela_id={novela_id}/> : null
    }</>
  )
}
