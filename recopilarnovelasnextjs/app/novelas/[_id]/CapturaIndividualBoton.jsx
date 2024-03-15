"use client";

export default function CapturaIndividualBoton({
  novela_id,
  capitulo_id,
  iframeRef,
}) {
  console.log(novela_id, capitulo_id);

  const post_contenido_caps = async (novela_id, capitulo_id, text) => {
    console.log(novela_id, capitulo_id, text);
  };

  const get_parrafos = async (novela_id, capitulo_id, iframeRef) => {
    console.log(novela_id, capitulo_id, iframeRef)
    
  };

  return (
    <>
      <div
        style={{ cursor: "pointer" }}
      >
        Captura Individual
      </div>
    </>
  );
}
