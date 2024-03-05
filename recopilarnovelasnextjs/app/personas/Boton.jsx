'use client'
import miCss from "./boton.module.css"

export default function Boton({valor}) {
  const masinfo = () => {
    alert(`El apellido de  ${valor.name.first} es ${valor.name.last}`);
  };
  return (
    <>
      <button className={miCss.boton} onClick={masinfo}>Mas info</button>
    </>
  );
}
