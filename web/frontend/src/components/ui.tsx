import { ReactNode } from 'react'

interface ButtonProps {
    children: ReactNode
    onClick?: () => void
    variant?: 'primary' | 'secondary' | 'danger' | 'success'
    size?: 'sm' | 'md' | 'lg'
    disabled?: boolean
    className?: string
    type?: 'button' | 'submit' | 'reset'
}

export function Button({
    children,
    onClick,
    variant = 'primary',
    size = 'md',
    disabled = false,
    className = '',
    type = 'button',
}: ButtonProps) {
    const baseClasses = 'font-semibold rounded-lg transition-colors duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2'

    const variantClasses = {
        primary: 'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500 disabled:bg-primary-300',
        secondary: 'bg-dark-200 text-dark-900 hover:bg-dark-300 focus:ring-dark-500 disabled:bg-dark-100',
        danger: 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500 disabled:bg-red-300',
        success: 'bg-green-500 text-white hover:bg-green-600 focus:ring-green-500 disabled:bg-green-300',
    }

    const sizeClasses = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
    }

    return (
        <button
            type={type}
            onClick={onClick}
            disabled={disabled}
            className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
        >
            {children}
        </button>
    )
}

interface InputProps {
    label?: string
    type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'textarea'
    value: string | number
    onChange: (value: string | number) => void
    placeholder?: string
    error?: string
    disabled?: boolean
    rows?: number
    className?: string
}

export function Input({
    label,
    type = 'text',
    value,
    onChange,
    placeholder,
    error,
    disabled = false,
    rows = 3,
    className = '',
}: InputProps) {
    const baseClasses = 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
    const errorClasses = error ? 'border-red-500 bg-red-50' : 'border-dark-300 bg-white'

    const Component = type === 'textarea' ? 'textarea' : 'input'

    return (
        <div className={className}>
            {label && <label className="block text-sm font-semibold text-dark-900 mb-2">{label}</label>}
            {Component === 'textarea' ? (
                <textarea
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    disabled={disabled}
                    rows={rows}
                    className={`${baseClasses} ${errorClasses} resize-none`}
                />
            ) : (
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    disabled={disabled}
                    className={`${baseClasses} ${errorClasses}`}
                />
            )}
            {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
        </div>
    )
}

interface CardProps {
    children: ReactNode
    className?: string
}

export function Card({ children, className = '' }: CardProps) {
    return (
        <div className={`bg-dark-800 rounded-lg shadow-md p-6 ${className}`}>
            {children}
        </div>
    )
}

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg'
}

export function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
    }

    return (
        <div className="flex justify-center items-center">
            <div className={`${sizeClasses[size]} border-4 border-dark-200 border-t-primary-500 rounded-full animate-spin`} />
        </div>
    )
}

interface AlertProps {
    type: 'success' | 'error' | 'warning' | 'info'
    message: string
    onClose?: () => void
}

export function Alert({ type, message, onClose }: AlertProps) {
    const bgClasses = {
        success: 'bg-green-50 border-green-500 text-green-900',
        error: 'bg-red-50 border-red-500 text-red-900',
        warning: 'bg-yellow-50 border-yellow-500 text-yellow-900',
        info: 'bg-blue-50 border-blue-500 text-blue-900',
    }

    return (
        <div className={`border-l-4 p-4 rounded ${bgClasses[type]} animate-fade-in`}>
            <div className="flex justify-between items-center">
                <p>{message}</p>
                {onClose && (
                    <button onClick={onClose} className="text-xl font-bold cursor-pointer">
                        ×
                    </button>
                )}
            </div>
        </div>
    )
}

interface BadgeProps {
    children: ReactNode
    variant?: 'primary' | 'success' | 'danger' | 'warning' | 'info'
    className?: string
}

export function Badge({ children, variant = 'primary', className = '' }: BadgeProps) {
    const variantClasses = {
        primary: 'bg-primary-100 text-primary-800',
        success: 'bg-green-100 text-green-800',
        danger: 'bg-red-100 text-red-800',
        warning: 'bg-yellow-100 text-yellow-800',
        info: 'bg-blue-100 text-blue-800',
    }

    return (
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${variantClasses[variant]} ${className}`}>
            {children}
        </span>
    )
}
