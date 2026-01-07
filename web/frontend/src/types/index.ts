// API Response Types
export interface User {
    id: number
    username: string
    email: string
    role: string
    created_at?: string
}

export interface Group {
    id: number
    name: string
    description: string
    members_count: number
    created_at?: string
}

export interface Action {
    id?: string
    action_type: 'ban' | 'kick' | 'mute' | 'unmute' | 'promote' | 'demote' | 'warn' | 'pin' | 'unpin'
    group_id: number
    user_id: number
    reason?: string
    duration_minutes?: number
    initiated_by?: number
    timestamp?: string
    status?: string
}

export interface ActionResponse {
    status: string
    action_id?: string
    message?: string
    error?: string
}

export interface DashboardStats {
    timestamp: string
    users_count: number
    groups_count: number
    status: string
    recent_actions?: Action[]
    active_groups?: number
    total_actions?: number
}

export interface HealthResponse {
    status: 'healthy' | 'unhealthy'
    service: string
    version: string
    database?: string
    centralized_api?: string
}

// Auth Types
export interface AuthState {
    isAuthenticated: boolean
    user?: User
    token?: string
}

export interface LoginRequest {
    username: string
    password: string
}

export interface LoginResponse {
    token: string
    user: User
}

// Table Data
export interface TableColumn<T> {
    key: keyof T
    label: string
    sortable?: boolean
    width?: string
}

export interface PaginationState {
    currentPage: number
    pageSize: number
    total: number
    totalPages: number
}
