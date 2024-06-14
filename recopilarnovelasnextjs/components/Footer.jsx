"use client";

export default function Footer() {
  const today = new Date()
  return (
    <footer>
      <p>
        © {today.getFullYear()} Proyecto Recopilacion de Novelas. Todos los derechos
        reservados.
      </p>
    </footer>
  );
}
