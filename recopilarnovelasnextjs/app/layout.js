import Nav from "@/components/Nav";
import "../styles/estilos.css";
import { Montserrat } from "@next/font/google";

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
});

const cargarPaginas = () => {
  return fetch("http://localhost:8000/api/sitios/?format=json")
    .then((res) => res.json())
    .then((datos) => datos);
};

export const metadata = {
  title: "Next.js",
  description: "Generado por David Vite Vergara",
};

export default async function RootLayout({ children }) {
  const datos = await cargarPaginas();
  return (
    <html lang="es">
      <body>
        <Nav datos={datos}/>
        <div className={fuente.className}>{children}</div>
      </body>
    </html>
  );
}
