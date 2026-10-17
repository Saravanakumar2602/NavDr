# NavDR — Intelligent Dead Reckoning Application

**Package**: `navigation-app`  
**Identity**: NavDR — GNSS-Fused Intelligent Navigation  
**Target Platform**: Android & iOS (React Native / Expo)

---

## Capabilities & Visual Identity

- **Theme**: Deep navy / near-black automotive dark mode (`#0B0F19`) with electric cyan accent (`#00E5FF`), safety red (`#FF3D00`) for GNSS denial, and bright green (`#00E676`) for healthy status.
- **Header & Branding**: Vector-rendered NavDR logo (stylized navigation arrow + concentric sensor orbit/gyro rings).
- **Map View Placeholder**: Local offline vector canvas map with road geometry, technical grid, separate GNSS & IDR trajectory layers, and heading-aware vehicle marker.
- **Status Dashboard**: Compact grid reporting GNSS status (`AVAILABLE`, `DENIED`, `RECOVERING`), navigation mode (`GNSS + INS`, `IDR`, `FUSION`), IMU status (`ACTIVE`), map status (`OFFLINE`), vehicle speed (km/h), heading (°), and position uncertainty (±m).
- **Outage Demonstration Banner**: Status alerts for GNSS loss (*"GNSS SIGNAL LOST — DEAD RECKONING ACTIVE"*) and restoration (*"GNSS SIGNAL RESTORED — FUSION RECOVERY"*).
- **System & Benchmark Screen**: Core technologies breakdown and IO-VNBD benchmark metrics (M028: 218.93 m vs M029: 48.20 m @ 300 s outage).

---

## State Architecture & Future IDR Engine Integration

The application UI is cleanly decoupled from the navigation computation engine via TypeScript interfaces:

```ts
interface NavigationState {
  pose: { x: number; y: number; latitude: number; longitude: number; heading: number; speed: number };
  positionUncertainty: number;
  gnssStatus: 'AVAILABLE' | 'DENIED' | 'RECOVERING';
  navigationMode: 'GNSS + INS' | 'IDR' | 'FUSION';
  imuStatus: 'ACTIVE' | 'INACTIVE';
  mapStatus: 'OFFLINE' | 'LOADING' | 'AVAILABLE';
  isNavigating: boolean;
}
```

### Integration Flow Architecture

```
Current Prototype:
  DemoDataProvider ──> NavigationContext ──> React Native UI

Future On-Device Production:
  Smartphone IMU (200Hz) ──> Native Bridge ──> On-Device IDR Engine (SpeedNet + EKF) ──> NavigationContext ──> React Native UI
```

---

## How to Run

Navigate to `apps/navigation-app` and execute:

- **Start Metro Server / Expo**:
  ```bash
  npx expo start
  ```
- **Run on Connected Android Device**:
  ```bash
  npx expo run:android
  ```
- **Run on Web Browser**:
  ```bash
  npx expo start --web
  ```
