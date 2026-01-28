import { Carrinho, UsoCarrinho, Funcionario } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'https://bakendgestaolim.onrender.com';

// Helper to handle response
async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Network response was not ok');
    }
    return response.json();
}

export const api = {
    // --- Auth ---
    login: async (email: string, password: string) => {
        return fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        }).then(handleResponse<{ user: { id: number, email: string } }>);
    },

    signup: async (email: string, password: string) => {
        return fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        }).then(handleResponse<{ success: boolean }>);
    },

    logout: async () => {
        return fetch(`${API_URL}/auth/logout`, { method: 'POST' }).then(handleResponse<{ success: boolean }>);
    },

    getMe: async () => {
        return fetch(`${API_URL}/auth/me`).then(handleResponse<{ user: any, isAdmin: boolean }>);
    },

    // --- Carrinhos ---
    getCarrinhos: async () => {
        return fetch(`${API_URL}/carrinhos`).then(handleResponse<Carrinho[]>);
    },

    createCarrinho: async (carrinho: Partial<Carrinho>) => {
        return fetch(`${API_URL}/carrinhos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(carrinho),
        }).then(handleResponse<{ success: boolean }>);
    },

    getUsosAtivos: async () => {
        return fetch(`${API_URL}/uso_carrinho/ativos`).then(handleResponse<UsoCarrinho[]>);
    },

    // --- Operations ---
    validateNif: async (nif: string) => {
        return fetch(`${API_URL}/funcionarios/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nif }),
        }).then(handleResponse<Funcionario>);
    },

    checkout: async (carrinhoId: number, funcionarioId: number) => {
        return fetch(`${API_URL}/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ carrinho_id: carrinhoId, funcionario_id: funcionarioId }),
        }).then(handleResponse<{ success: boolean }>);
    },

    returnCart: async (carrinhoId: number, funcionarioId: number) => {
        return fetch(`${API_URL}/return`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ carrinho_id: carrinhoId, funcionario_id: funcionarioId }),
        }).then(handleResponse<{ success: boolean }>);
    },

    // --- Admin ---
    updateCarrinho: async (id: number, data: Partial<Carrinho>) => {
        return fetch(`${API_URL}/admin/carrinhos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        }).then(handleResponse<{ success: boolean }>);
    },

    deleteCarrinho: async (id: number) => {
        return fetch(`${API_URL}/admin/carrinhos/${id}`, { method: 'DELETE' }).then(handleResponse<{ success: boolean }>);
    },

    getFuncionarios: async () => {
        return fetch(`${API_URL}/admin/funcionarios`).then(handleResponse<Funcionario[]>);
    },

    createFuncionario: async (data: Partial<Funcionario>) => {
        return fetch(`${API_URL}/admin/funcionarios`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        }).then(handleResponse<{ success: boolean }>);
    },

    updateFuncionario: async (id: number, data: Partial<Funcionario>) => {
        return fetch(`${API_URL}/admin/funcionarios/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        }).then(handleResponse<{ success: boolean }>);
    },

    deleteFuncionario: async (id: number) => {
        return fetch(`${API_URL}/admin/funcionarios/${id}`, { method: 'DELETE' }).then(handleResponse<{ success: boolean }>);
    },

    getHistorico: async () => {
        return fetch(`${API_URL}/admin/historico`).then(handleResponse<UsoCarrinho[]>);
    }
};
