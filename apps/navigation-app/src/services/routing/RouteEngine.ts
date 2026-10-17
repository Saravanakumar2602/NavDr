import { Coordinate, Route, RouteStatus, RouteError } from '../../types/navigation';

export interface RouteCalculationResult {
  success: boolean;
  route?: Route;
  status: RouteStatus;
  error?: RouteError;
  errorMessage?: string;
  calculationTimeMs?: number;
}

export interface RouteEngine {
  calculateRoute(origin: Coordinate, destination: Coordinate): Promise<RouteCalculationResult>;
  isAvailable(): boolean;
}
