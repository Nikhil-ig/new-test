import axios, { AxiosInstance, AxiosError } from 'axios'
import { User, Group, Action, ActionResponse, DashboardStats, HealthResponse } from '../types'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002/api'

class APIClient {
    private client: AxiosInstance
    private token: string | null = null

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json',
            },
        })

        // Load token from localStorage
        this.token = localStorage.getItem('auth_token')
        if (this.token) {
            this.setAuthHeader(this.token)
        }

        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                if (this.token) {
                    config.headers.Authorization = `Bearer ${this.token}`
                }
                return config
            },
            (error) => Promise.reject(error)
        )

        // Response interceptor
        this.client.interceptors.response.use(
            (response) => response,
            (error: AxiosError) => {
                if (error.response?.status === 401) {
                    // Handle unauthorized
                    this.clearAuth()
                    window.location.href = '/login'
                }
                return Promise.reject(error)
            }
        )
    }

    setAuthHeader(token: string) {
        this.token = token
        this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
        localStorage.setItem('auth_token', token)
    }

    clearAuth() {
        this.token = null
        delete this.client.defaults.headers.common['Authorization']
        localStorage.removeItem('auth_token')
    }

    // Health Check
    async healthCheck(): Promise<HealthResponse> {
        const response = await this.client.get<HealthResponse>('/health')
        return response.data
    }

    // Users
    async getUsers(): Promise<User[]> {
        const response = await this.client.get<User[]>('/users')
        return response.data
    }

    async getUserById(id: number): Promise<User> {
        const response = await this.client.get<User>(`/users/${id}`)
        return response.data
    }

    async createUser(userData: Partial<User>): Promise<User> {
        const response = await this.client.post<User>('/users', userData)
        return response.data
    }

    async updateUser(id: number, userData: Partial<User>): Promise<User> {
        const response = await this.client.put<User>(`/users/${id}`, userData)
        return response.data
    }

    async deleteUser(id: number): Promise<void> {
        await this.client.delete(`/users/${id}`)
    }

    // Groups
    async getGroups(): Promise<Group[]> {
        const response = await this.client.get<Group[]>('/groups')
        return response.data
    }

    async getGroupById(id: number): Promise<Group> {
        const response = await this.client.get<Group>(`/groups/${id}`)
        return response.data
    }

    async createGroup(groupData: Partial<Group>): Promise<Group> {
        const response = await this.client.post<Group>('/groups', groupData)
        return response.data
    }

    async updateGroup(id: number, groupData: Partial<Group>): Promise<Group> {
        const response = await this.client.put<Group>(`/groups/${id}`, groupData)
        return response.data
    }

    async deleteGroup(id: number): Promise<void> {
        await this.client.delete(`/groups/${id}`)
    }

    // Actions
    async executeAction(action: Action): Promise<ActionResponse> {
        const response = await this.client.post<ActionResponse>('/actions/execute', action)
        return response.data
    }

    async getActions(): Promise<Action[]> {
        const response = await this.client.get<Action[]>('/actions')
        return response.data
    }

    // Dashboard
    async getDashboardStats(): Promise<DashboardStats> {
        const response = await this.client.get<DashboardStats>('/dashboard/stats')
        return response.data
    }
}

export const apiClient = new APIClient()
