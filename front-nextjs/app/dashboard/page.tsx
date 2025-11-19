'use client';

import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [lecturas, setLecturas] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WEBSOCKET_URL || '');

    console.log(process.env.NEXT_PUBLIC_WEBSOCKET_URL);

    ws.onopen = () => {
      console.log('Conectado');
    };

    ws.onmessage = (event) => {
      setLecturas((prev) => [...prev, event.data]);
    };

    ws.onerror = (error) => {
      console.error('Error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <>
      <div>
        <h2>Lecturas recibidas ({lecturas.length}):</h2>
        <ul>
          {lecturas.map((lectura, index) => (
            <li key={index}>{lectura}</li>
          ))}
        </ul>
      </div>
    </>
  )
}