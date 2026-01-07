import { useState } from 'react'
import { LogIn } from 'lucide-react'
import { Card, Button, Input, Alert } from '../components/ui'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../api/client'

export function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const navigate = useNavigate()

    console.log('Login component rendering')

    const handleLogin = async () => {
        try {
            if (!email || !password) {
                setError('Please fill in all fields')
                return
            }

            setLoading(true)
            // Call API login - we'll add this method to the client
            const response = await fetch('http://localhost:8002/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            })

            if (!response.ok) throw new Error('Login failed')

            const data = await response.json()
            apiClient.setAuthHeader(data.access_token)
            navigate('/')
        } catch (err) {
            setError('Invalid credentials')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleDemoLogin = () => {
        // Demo login for testing
        const demoToken = 'demo-token-' + Date.now()
        apiClient.setAuthHeader(demoToken)
        localStorage.setItem('token', demoToken)
        navigate('/')
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-900 via-dark-900 to-dark-800 flex items-center justify-center p-4">
            <Card className="w-full max-w-md bg-dark-800 border border-dark-700">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-full mb-4">
                        <LogIn className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white">Bot Manager</h1>
                    <p className="text-dark-400 mt-2">Admin Dashboard</p>
                </div>

                {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

                <div className="space-y-4">
                    <Input
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(v) => setEmail(String(v))}
                        placeholder="admin@example.com"
                    />
                    <Input
                        label="Password"
                        type="password"
                        value={password}
                        onChange={(v) => setPassword(String(v))}
                        placeholder="••••••••"
                    />

                    <Button
                        onClick={handleLogin}
                        disabled={loading}
                        variant="primary"
                        size="lg"
                        className="w-full"
                    >
                        {loading ? 'Logging in...' : 'Login'}
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-dark-600"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-dark-800 text-dark-400">or</span>
                        </div>
                    </div>

                    <Button
                        onClick={handleDemoLogin}
                        variant="secondary"
                        size="lg"
                        className="w-full"
                    >
                        Demo Login
                    </Button>
                </div>

                <p className="text-center text-dark-400 text-sm mt-6">
                    Default credentials: admin@example.com / password123
                </p>
            </Card>
        </div>
    )
}
