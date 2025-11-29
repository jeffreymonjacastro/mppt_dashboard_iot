'use client';

import { useEffect, useState, useRef, useMemo } from 'react';
import LineChartCard from '../../components/LinearChart';
import { LoRaData, ChartDataPoint } from '../../types/lora';

const MAX_LECTURAS = 200; // Límite de lecturas en pantalla
const MAX_CHART_POINTS = 200; // Límite de puntos en la gráfica

const smoothData = (data: ChartDataPoint[], sortKey: keyof ChartDataPoint, smoothKey: keyof ChartDataPoint, windowSize = 5) => {
  if (data.length === 0) return [];

  // 1. Ordenar
  const sorted = [...data].sort((a, b) => (a[sortKey] as number) - (b[sortKey] as number));

  // 2. Media móvil
  return sorted.map((point, index, array) => {
    const start = Math.max(0, index - Math.floor(windowSize / 2));
    const end = Math.min(array.length, index + Math.floor(windowSize / 2) + 1);
    const subset = array.slice(start, end);
    const avg = subset.reduce((sum, p) => sum + (p[smoothKey] as number), 0) / subset.length;

    return { ...point, [smoothKey]: avg };
  });
};

export default function Dashboard() {
  const [lecturas, setLecturas] = useState<string[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [totalReceived, setTotalReceived] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Generar datos suavizados para todas las gráficas
  const currentVsVoltageData = useMemo(() => smoothData(chartData, 'voltage', 'current'), [chartData]);
  const powerVsVoltageData = useMemo(() => smoothData(chartData, 'voltage', 'power'), [chartData]);
  const voltageVsDutyData = useMemo(() => smoothData(chartData, 'duty', 'voltage'), [chartData]);
  const currentVsDutyData = useMemo(() => smoothData(chartData, 'duty', 'current'), [chartData]);

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
              const powerVal = voltageVal * currentVal;

              setChartData((prev) => {
                const newData = [...prev, {
                  duty: dutyVal,
                  voltage: voltageVal,
                  current: currentVal,
                  power: powerVal,
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
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      <div className="mb-4 flex items-center gap-4">
        <h2 className="text-2xl font-bold">Dashboard LoRa</h2>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
          {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
        </div>
      </div>

      <div className="mb-4 p-4 bg-gray-200 rounded-lg">
        <p className="text-sm">
          <strong>Total recibidas:</strong> {totalReceived} |
          <strong> Mostrando:</strong> {lecturas.length} (últimas {MAX_LECTURAS})
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* 1. Corriente vs Voltaje (Top Left) */}
        <LineChartCard
          title="Corriente vs Voltaje"
          data={currentVsVoltageData}
          xKey="voltage"
          yKey="current"
          xLabel="Voltaje (V)"
          yLabel="Corriente (A)"
          lineColor="#9370db"
          yDomain={[1.9, 'auto']}
        />

        {/* 2. Potencia vs Voltaje (Top Right) */}
        <LineChartCard
          title="Potencia vs Voltaje"
          data={powerVsVoltageData}
          xKey="voltage"
          yKey="power"
          xLabel="Voltaje (V)"
          yLabel="Potencia (W)"
          lineColor="#a020f0"
          yDomain={[3, 'auto']}
        />

        {/* 3. Voltaje vs Duty (Bottom Left) */}
        <LineChartCard
          title="Voltaje vs Duty"
          data={voltageVsDutyData}
          xKey="duty"
          yKey="voltage"
          xLabel="Duty"
          yLabel="Voltaje (V)"
          lineColor="#5e2121"
        />

        {/* 4. Corriente vs Duty (Bottom Right) */}
        <LineChartCard
          title="Corriente vs Duty"
          data={currentVsDutyData}
          xKey="duty"
          yKey="current"
          xLabel="Duty"
          yLabel="Corriente (A)"
          lineColor="#1f77b4"
        />
      </div>

      {/* Lista de lecturas */}
      <div className="border rounded-lg p-4 bg-dark max-h-[600px] overflow-y-auto">
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
  )
}