import Link from 'next/link';

export default function NotFound() {
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>404 - Página no encontrada</h1>
        <p style={styles.message}>
          La página que buscas no existe o fue movida.
        </p>
        <div style={styles.links}>
          <Link href="/" style={styles.link}>
            Ir al inicio
          </Link>
          <Link href="/sitios" style={styles.link}>
            Ver sitios
          </Link>
          <Link href="/novelas" style={styles.link}>
            Ver novelas
          </Link>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
    padding: '20px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '40px',
    maxWidth: '400px',
    width: '100%',
    textAlign: 'center',
    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#333',
    marginBottom: '16px',
  },
  message: {
    fontSize: '16px',
    color: '#666',
    marginBottom: '24px',
    lineHeight: '1.5',
  },
  links: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  link: {
    color: '#4a90d9',
    textDecoration: 'none',
    fontSize: '16px',
    padding: '10px',
    borderRadius: '8px',
    transition: 'background-color 0.2s',
  },
};