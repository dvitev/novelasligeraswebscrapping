import "@/styles/globals.css";
import { Montserrat } from "next/font/google";
import Link from "next/link";

const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata = {
  title: "📚 Novelas Manager",
  description: "Gestiona y descarga tus novelas favoritas",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className={montserrat.className}>
        <div className="app-layout">
          <main className="app-main">{children}</main>
          <footer className="footer">
            © {new Date().getFullYear()} Novelas Manager — Gestión y descarga de
            novelas ligeras.
          </footer>
        </div>
      </body>
    </html>
  );
}
