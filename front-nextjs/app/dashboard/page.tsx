'use client';

import { useEffect, useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const MAX_LECTURAS = 200; // Límite de lecturas en pantalla
const MAX_CHART_POINTS = 10; // Límite de puntos en la gráfica

interface LoRaData {
  duty?: number | string;
  voltage?: number | string;
  current?: number | string;
  pot?: number | string;
  snr?: number | string;
  timestamp?: string;
}

interface ChartDataPoint {
  duty: number;
  voltage: number;
  current: number;
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

          setLecturas((prev) => {
            const newLecturas = [...prev, event.data];
            if (newLecturas.length > MAX_LECTURAS) {
              return newLecturas.slice(-MAX_LECTURAS);
            }
            return newLecturas;
          });

          if (parsedData.duty !== undefined && parsedData.voltage !== undefined && parsedData.current !== undefined && parsedData.timestamp) {
            const dutyVal = Number(parsedData.duty);
            const voltageVal = Number(parsedData.voltage);
            const currentVal = Number(parsedData.current);

            if (!isNaN(dutyVal) && !isNaN(voltageVal) && !isNaN(currentVal)) {
              setChartData((prev) => {
                const newData = [...prev, {
                  duty: dutyVal,
                  voltage: voltageVal,
                  current: currentVal,
                  timestamp: parsedData.timestamp!
                }];

                if (newData.length > MAX_CHART_POINTS) {
                  return newData.slice(-MAX_CHART_POINTS);
                }
                return newData;
              });
            }
          }
        } catch (error) {
          console.error('Error al parsear datos:', error);
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

        {/* Gráfica Voltage/Current vs Duty */}
        <div className="mb-6 border rounded-lg p-4 bg-white">
          <h3 className="font-semibold mb-4 text-lg">Voltage y Current vs Duty</h3>
          {chartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500 italic">
              Esperando datos para la gráfica...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={[...chartData].sort((a, b) => a.duty - b.duty)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="duty"
                  type="number"
                  label={{ value: 'Duty', position: 'insideBottomRight', offset: -5 }}
                  domain={['auto', 'auto']}
                />
                <YAxis
                  label={{ value: 'Value', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
                  labelStyle={{ fontWeight: 'bold' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="voltage"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Voltage (V)"
                />
                <Line
                  type="monotone"
                  dataKey="current"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Current (A)"
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