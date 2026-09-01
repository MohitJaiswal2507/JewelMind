# JewelMind Frontend Application

React 19 + TypeScript + Vite + Tailwind CSS web client for the JewelMind AI Jewellery Platform.

---

## Directory Layout
```text
src/
├── components/   # Reusable UI elements
├── pages/        # Application view routes
├── layouts/      # Layout shells
├── hooks/        # Custom React hooks
├── services/     # Backend API integration clients
├── types/        # TypeScript interfaces & types
├── utils/        # Utility helpers
├── assets/       # Media and static graphics
├── App.tsx       # Root component & router
├── main.tsx      # Application entrypoint
└── index.css     # Tailwind CSS entrypoint
```

---

## Getting Started (Local Development)

```bash
npm install
npm run dev
```
Runs the local development server at `http://localhost:5173`.

## Production Build
```bash
npm run build
```
Type checks and bundles the application into `dist/`.
