import Link from "next/link"
import { Montserrat } from "@next/font/google";

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
  variable: '--mifont'
});

export default function Nav({ datos }) {
  return (
    <nav className={fuente.className}>
      <Link href="/">
        Home
      </Link>
      {/* <Link href="/personas">
        Personas
      </Link> */}
      {datos.map((novel, idx) => (
        <Link key={idx} href={`/sitios/${novel._id.toString()}`}>{novel.nombre}</Link>
      ))}
    </nav>
  );
}
