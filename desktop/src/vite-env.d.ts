/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_RADAR_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
