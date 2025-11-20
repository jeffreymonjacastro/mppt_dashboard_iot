'use client';

import { useEffect, useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const MAX_LECTURAS = 200; // Límite de lecturas en pantalla
const MAX_CHART_POINTS = 10; // Límite de puntos en la gráfica

interface LoRaData {
  POT?: string;
  SNR?: string;
  PAYLOAD?: string;
  timestamp?: string;
  raw_data?: string;
}

interface ChartDataPoint {
  time: string;
  POT: number;
  timestamp: string;
}

export default function Dashboard() {
  const [lecturas, setLecturas] = useState<string[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [totalReceived, setTotalReceived] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || '';
      console.log('Conectando a:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket conectado');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        setTotalReceived(prev => prev + 1);

        try {
          const parsedData: LoRaData = JSON.parse(event.data);

          // Actualizar lista de lecturas
          setLecturas((prev) => {
            const newLecturas = [...prev, event.data];
            if (newLecturas.length > MAX_LECTURAS) {
              return newLecturas.slice(-MAX_LECTURAS);
            }
            return newLecturas;
          });

          // Actualizar datos de la gráfica si tiene POT
          if (parsedData.POT && parsedData.timestamp) {
            const potValue = parseFloat(parsedData.POT);
            if (!isNaN(potValue)) {
              const timeStr = new Date(parsedData.timestamp).toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              });

              setChartData((prev) => {
                const newData = [...prev, {
                  time: timeStr,
                  POT: potValue,
                  timestamp: parsedData.timestamp!
                }];

                // Mantener solo los últimos MAX_CHART_POINTS puntos
                if (newData.length > MAX_CHART_POINTS) {
                  return newData.slice(-MAX_CHART_POINTS);
                }
                return newData;
              });
            }
          }
        } catch (error) {
          console.error('Error al parsear datos:', error);
          // Si no se puede parsear como JSON, agregarlo como string
          setLecturas((prev) => {
            const newLecturas = [...prev, event.data];
            if (newLecturas.length > MAX_LECTURAS) {
              return newLecturas.slice(-MAX_LECTURAS);
            }
            return newLecturas;
          });
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket desconectado. Intentando reconectar...');
        setIsConnected(false);

        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Reconectando...');
          connectWebSocket();
        }, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <>
      <div className="p-4">
        <div className="mb-4 flex items-center gap-4">
          <h2 className="text-2xl font-bold">Dashboard LoRa</h2>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
            {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
          </div>
        </div>

        <div className="mb-4 p-4 bg-gray-100 rounded-lg">
          <p className="text-sm">
            <strong>Total recibidas:</strong> {totalReceived} |
            <strong> Mostrando:</strong> {lecturas.length} (últimas {MAX_LECTURAS})
          </p>
        </div>

        {/* Gráfica POT vs Tiempo */}
        <div className="mb-6 border rounded-lg p-4 bg-white">
          <h3 className="font-semibold mb-4 text-lg">Potencia (POT) vs Tiempo</h3>
          {chartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500 italic">
              Esperando datos para la gráfica...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  label={{ value: 'POT (dBm)', angle: -90, position: 'insideLeft' }}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
                  labelStyle={{ fontWeight: 'bold' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="POT"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                  name="Potencia (dBm)"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Lista de lecturas */}
        <div className="border rounded-lg p-4 bg-white max-h-[600px] overflow-y-auto">
          <h3 className="font-semibold mb-2">Lecturas recibidas:</h3>
          {lecturas.length === 0 ? (
            <p className="text-gray-500 italic">Esperando datos...</p>
          ) : (
            <ul className="space-y-1">
              {lecturas.map((lectura, index) => (
                <li
                  key={index}
                  className="font-mono text-sm p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                >
                  <span className="text-gray-400 mr-2">#{index + 1}</span>
                  {lectura}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  )
}