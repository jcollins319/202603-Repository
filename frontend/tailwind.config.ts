import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        sale: "#ef4444",
        purchase: "#22c55e",
      },
    },
  },
  plugins: [],
};
export default config;
