"use client";

export default function BotonesDescarga({novela_id}) {
  const obtenerEpub = (novela_id) => {
    const url = `http://192.168.1.11:8000/api/generar_epub/${novela_id}/`;
    window.open(url, "_blank");
  };
  const obtenerPdf = (novela_id) => {
    const url = `http://192.168.1.11:8000/api/generar_pdf/${novela_id}/`;
    window.open(url, "_blank");
  };

  return (
    <>
      <button className="EpubNovel" onClick={() => {
          obtenerEpub(novela_id);
        }}
      >
        Epub
      </button>
      <button className="PDFNovel" onClick={() => {
          obtenerPdf(novela_id);
        }}
      >
        PDF
      </button>
    </>
  );
}
