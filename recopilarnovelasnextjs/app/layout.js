import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import "../styles/estilos.css";
import { Montserrat } from "@next/font/google";

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
});

const cargarPaginas = () => {
  return fetch("http://192.168.1.11:8000/api/sitios/?format=json")
    .then((res) => res.json())
    .then((datos) => datos);
};

export const metadata = {
  title: "Novelas",
  description: "Generado por David Vite Vergara",
};

export default async function RootLayout({ children }) {
  const datos = await cargarPaginas();
  datos.unshift({"_id":"10101010101010101", "nombre":"Home", "url":"/", "idioma":"es", "created_at": "2020-03-13T13:49:14.946000Z", "updated_at": "2020-03-13T13:49:15.265000Z"})
  // console.log(datos)
  return (
    <html lang="es">
      <body>
        <Nav datos={datos}/>
        <div className={fuente.className}>{children}</div>
        <Footer/>
      </body>
    </html>
  );
}
