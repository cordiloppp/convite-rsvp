import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { PublicConfig } from "../api/types";

const DEFAULT_CONFIG: PublicConfig = {
  brand_name: "Convite",
  brand_url: "/",
  timezone: "America/Tijuana",
};

const ConfigContext = createContext<PublicConfig>(DEFAULT_CONFIG);

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState(DEFAULT_CONFIG);

  useEffect(() => {
    api
      .config()
      .then(setConfig)
      .catch(() => undefined);
  }, []);

  return <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>;
}

export const useConfig = () => useContext(ConfigContext);
