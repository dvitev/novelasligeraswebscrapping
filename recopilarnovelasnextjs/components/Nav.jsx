import Link from "next/link"
import { Montserrat } from "@next/font/google";

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
  variable: '--mifont'
});

export default function Nav({ datos }) {
  // console.log(datos)
  return (
    <nav className={fuente.className}>
      {datos.map((novel, idx) => (
        novel._id==='10101010101010101' ? <Link key={idx} href={`${novel.url}`}>{novel.nombre}</Link> : <Link key={idx} href={`/sitios/${novel._id.toString()}`}>{novel.nombre}</Link>
      ))}
    </nav>
  );
}
