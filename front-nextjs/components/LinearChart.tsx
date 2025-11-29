'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Label
} from 'recharts';
import { LoRaData } from '../types/lora';

interface ChartProps {
  title: string;
  data: LoRaData[];
  xKey: string;
  yKey: string;
  xLabel: string;
  yLabel: string;
  lineColor: string;
  yDomain?: [number | 'auto', number | 'auto'];
}

export default function LineChartCard({
  title,
  data,
  xKey,
  yKey,
  xLabel,
  yLabel,
  lineColor,
  yDomain = ['auto', 'auto']
}: ChartProps) {
  return (
    <div className="w-full h-[350px] bg-white border border-gray-300 rounded-lg shadow-sm p-4 flex flex-col">
      <h3 className="text-center font-bold text-gray-800 mb-4">{title}</h3>

      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 30, left: 20, bottom: 25 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={true} horizontal={true} />

            <XAxis
              dataKey={xKey}
              type="number"
              domain={['auto', 'auto']}
              tick={{ fontSize: 12 }}
              tickLine={false}
            >
              <Label value={xLabel} offset={-10} position="insideBottom" />
            </XAxis>

            <YAxis
              tick={{ fontSize: 12 }}
              domain={yDomain}
            >
              <Label value={yLabel} angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>

            <Tooltip
              contentStyle={{ backgroundColor: '#fff', borderRadius: '5px', border: '1px solid #ccc' }}
              labelStyle={{ fontWeight: 'bold', color: '#333' }}
              formatter={(value: number) => value.toFixed(2)}
            />

            <Legend verticalAlign="bottom" height={36} wrapperStyle={{ paddingTop: '20px' }} />

            <Line
              name={yLabel}
              type="linear"
              dataKey={yKey}
              stroke={lineColor}
              strokeWidth={2}
              dot={{ r: 3, fill: lineColor }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}