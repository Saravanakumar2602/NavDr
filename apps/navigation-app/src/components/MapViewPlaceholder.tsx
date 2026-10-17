import React from 'react';
import { NavigationMap } from './map/NavigationMap';
import { VehiclePose, TrajectoryPoint, GnssStatus, Destination, Route } from '../types/navigation';

interface MapViewProps {
  pose: VehiclePose;
  gnssPoints: TrajectoryPoint[];
  idrPoints: TrajectoryPoint[];
  gnssStatus: GnssStatus;
  lastKnownPose: VehiclePose | null;
  confidence?: number;
  isNavigating?: boolean;
  destination?: Destination | null;
  route?: Route | null;
}

export const MapViewPlaceholder: React.FC<MapViewProps> = (props) => {
  return <NavigationMap {...props} />;
};
