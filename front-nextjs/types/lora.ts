export interface LoRaData {
  duty?: number | string;
  voltage?: number | string;
  current?: number | string;
  pot?: number | string;
  snr?: number | string;
  timestamp?: string;
  power?: number;
}

export interface ChartDataPoint {
  duty: number;
  voltage: number;
  current: number;
  power: number;
  timestamp: string;
}
