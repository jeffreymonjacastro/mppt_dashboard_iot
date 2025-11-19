"use client";

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api';

export default function Home() {
  const [data, setData] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await apiClient.get('/health');
        setData(res.data);
      } catch (error) {
        console.error("Error al obtener los datos:", error);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <div>
          {data ? JSON.stringify(data) : "Loading..."}
        </div>
      </main>
    </div>
  );
}
