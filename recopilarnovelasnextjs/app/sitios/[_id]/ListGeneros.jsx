'use client';
import { Montserrat } from "@next/font/google";
import { useState } from 'react';

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
  variable: "--mifont",
});

export default function ListGeneros({ datos, onFiltrar }) {
  const [selectedGenero, setSelectedGenero] = useState('');
  
  const filtrar = () => {
    if (!selectedGenero) {
      alert('Debe seleccionar un género primero');
    } else {
      alert(`Buscando ${selectedGenero}`);
    }
  };

  const handleGeneroChange = (event) => {
    setSelectedGenero(event.target.value);
  };

  return (
    <div className="generos">
      <label htmlFor="browsergenero" className="browsergenero">Generos: </label>
      <input list="browsers" name="browsergenero" className="browsergenero" id="browsergenero" placeholder="Todos" onChange={handleGeneroChange} value={selectedGenero}/>
      <datalist id="browsers">
        {datos.map((genero,idx)=>(
          <option key={idx} value={genero}/>
        ))}
      </datalist>
      {datos.length >0 ? (
        <input type="button" value={'Filtrar'} className="buttongenero" onClick={filtrar} />
      ) : null}
    </div>
  );
}
