import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/components/atoms/**/*.{js,jsx,ts,tsx}",
    "./src/components/molecules/**/*.{js,jsx,ts,tsx}",
    "./src/components/organisms/**/*.{js,jsx,ts,tsx}",
    "./src/components/templates/**/*.{js,jsx,ts,tsx}",
  ],
};

export default config;
