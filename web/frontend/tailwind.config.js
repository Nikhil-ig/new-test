module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    safelist: [
        // Dark colors
        'bg-dark-50', 'bg-dark-100', 'bg-dark-200', 'bg-dark-300', 'bg-dark-400', 'bg-dark-500', 'bg-dark-600', 'bg-dark-700', 'bg-dark-800', 'bg-dark-900',
        'text-dark-50', 'text-dark-100', 'text-dark-200', 'text-dark-300', 'text-dark-400', 'text-dark-500', 'text-dark-600', 'text-dark-700', 'text-dark-800', 'text-dark-900',
        'border-dark-50', 'border-dark-100', 'border-dark-200', 'border-dark-300', 'border-dark-400', 'border-dark-500', 'border-dark-600', 'border-dark-700', 'border-dark-800', 'border-dark-900',
        'hover:bg-dark-50', 'hover:bg-dark-100', 'hover:bg-dark-200', 'hover:bg-dark-300', 'hover:bg-dark-400', 'hover:bg-dark-500', 'hover:bg-dark-600', 'hover:bg-dark-700', 'hover:bg-dark-800', 'hover:bg-dark-900',
        // Primary colors
        'bg-primary-50', 'bg-primary-100', 'bg-primary-200', 'bg-primary-300', 'bg-primary-400', 'bg-primary-500', 'bg-primary-600', 'bg-primary-700', 'bg-primary-800', 'bg-primary-900',
        'text-primary-50', 'text-primary-100', 'text-primary-200', 'text-primary-300', 'text-primary-400', 'text-primary-500', 'text-primary-600', 'text-primary-700', 'text-primary-800', 'text-primary-900',
        'border-primary-50', 'border-primary-100', 'border-primary-200', 'border-primary-300', 'border-primary-400', 'border-primary-500', 'border-primary-600', 'border-primary-700', 'border-primary-800', 'border-primary-900',
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f0f9ff',
                    100: '#e0f2fe',
                    200: '#bae6fd',
                    300: '#7dd3fc',
                    400: '#38bdf8',
                    500: '#0ea5e9',
                    600: '#0284c7',
                    700: '#0369a1',
                    800: '#075985',
                    900: '#0c3d66',
                },
                dark: {
                    50: '#f9fafb',
                    100: '#f3f4f6',
                    200: '#e5e7eb',
                    300: '#d1d5db',
                    400: '#9ca3af',
                    500: '#6b7280',
                    600: '#4b5563',
                    700: '#374151',
                    800: '#1f2937',
                    900: '#111827',
                }
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-in-out',
                'slide-in': 'slideIn 0.3s ease-in-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideIn: {
                    '0%': { transform: 'translateX(-10px)', opacity: '0' },
                    '100%': { transform: 'translateX(0)', opacity: '1' },
                },
            },
        },
    },
    plugins: [],
}
