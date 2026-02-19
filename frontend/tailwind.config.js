/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'brutal-bg': '#fdfbf7',
                'brutal-black': '#121212',
                'brutal-red': '#ff4d4d',
                'brutal-green': '#00ebc7',
                'brutal-yellow': '#fde24f',
                'brutal-blue': '#1b9aaa',
            },
            boxShadow: {
                'brutal': '4px 4px 0px 0px #121212',
                'brutal-lg': '8px 8px 0px 0px #121212',
                'brutal-sm': '2px 2px 0px 0px #121212',
            },
            borderWidth: {
                '3': '3px',
            },
            keyframes: {
                "accordion-down": {
                    from: { height: "0" },
                    to: { height: "var(--radix-accordion-content-height)" },
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: "0" },
                },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [],
}
