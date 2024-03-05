'use client'
import Boton from "./Boton";
import Image from "next/image";

const cargador = ({src, width})=>{
  return `${src}?w=${width}`
}

export default function Ficha({valor, index}) {
  return (
    <>
      <div className="persona" key={index}>
        <h3>{valor.name.first}</h3>
        <Image 
        loader={cargador}
        src={valor.picture.large}
        width={125}
        height={125}
        alt=""
        />

        {/* <img src={valor.picture.large} alt="" /> */}
        <div>
          <Boton valor={valor}/>
        </div>
      </div>
    </>
  );
}
