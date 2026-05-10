'use client';

import { useEffect } from 'react';

export default function Error({ error, reset }) {
  useEffect(() => {
    console.error('Error en la aplicación:', error);
  }, [error]);

  const isNotFound = error?.message?.includes('404') || error?.digest === 'NOT_FOUND';

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>
          {isNotFound ? 'Página no encontrada' : 'Algo salió mal'}
        </h1>
        <p style={styles.message}>
          {isNotFound
            ? 'La página que buscas no existe o fue eliminada.'
            : 'Ha ocurrido un error inesperado. Por favor, intenta de nuevo.'}
        </p>
        <button
          onClick={() => window.location.href = '/'}
          style={styles.button}
        >
          Volver al inicio
        </button>
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
    fontSize: '24px',
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
  button: {
    backgroundColor: '#4a90d9',
    color: 'white',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '8px',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
};