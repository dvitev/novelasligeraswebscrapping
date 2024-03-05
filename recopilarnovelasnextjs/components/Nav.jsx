import Link from "next/link"
import { Montserrat } from "@next/font/google";

const fuente = Montserrat({
  weight: "400",
  subsets: ["latin"],
  variable: '--mifont'
});

export default function Nav() {
  return (
    <>
      <nav className={fuente.className}>
        <Link href="/">Home</Link>
        {/* <Link href="/about">About</Link> */}
        <Link href="/personas">Personas</Link>
        {/* <Link href="/quienesSomos">Quienes Somos</Link> */}
        <Link href="/novelbin">Novel Bin</Link>
      </nav>
    </>
  );
}
