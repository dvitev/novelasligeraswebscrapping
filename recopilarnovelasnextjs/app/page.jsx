"use client";
import Image from "next/image";
import imagen2 from "../public/imagenes/martial-peak-ombyb1.png";

export default function page() {
  return (
    <>
      <div>Pagina Principal</div>
      <div className="caja">
        <Image
          src="/imagenes/sere-la-matriarca-en-esta-vida-9fdch0.png"
          width={240}
          height={326}
          layout="responsive"
        />
      </div>
      <div className="caja">
        <Image src={imagen2} layout="responsive" />
      </div>
    </>
  );
}
