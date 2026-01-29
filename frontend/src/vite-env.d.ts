/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PROJECT_ROOT?: string;
  readonly VITE_SKILL_LIBRARY_PATH?: string;
  readonly VITE_CHARACTER_LIBRARY_PATH?: string;
  readonly DEV: boolean;
  readonly MODE: string;
  readonly PROD: boolean;
  readonly SSR: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
