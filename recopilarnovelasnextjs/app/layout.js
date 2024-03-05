import Nav from "@/components/Nav";
import "../styles/estilos.css";
import { Montserrat } from "@next/font/google";

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
});

export const metadata = {
  title: "Next.js",
  description: "Generado por David Vite Vergara",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <Nav />
        <div className={fuente.className}>{children}</div>
      </body>
    </html>
  );
}
