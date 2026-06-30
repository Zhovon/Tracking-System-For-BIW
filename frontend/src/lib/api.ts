import { supabase } from './supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(session?.access_token ? { 'Authorization': `Bearer ${session.access_token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  // If we are sending FormData, we must let the browser set the Content-Type with the boundary
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  // Hard bust Next.js and Vercel edge caching by adding a unique timestamp to GET requests
  let finalEndpoint = endpoint;
  if (!options.method || options.method.toUpperCase() === 'GET') {
    const separator = endpoint.includes('?') ? '&' : '?';
    finalEndpoint = `${endpoint}${separator}_t=${new Date().getTime()}`;
  }

  const res = await fetch(`${API_BASE_URL}${finalEndpoint}`, {
    ...options,
    cache: 'no-store', // Hard opt-out of Next.js fetch cache
    headers: {
      ...headers,
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Pragma": "no-cache",
    },
  });

  if (!res.ok) {
    let errorMessage = 'An error occurred';
    try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorMessage;
    } catch (e) {
        // ignore
    }
    throw new Error(errorMessage);
  }

  return res.json();
}

export async function fetchRooms() {
  return fetchApi("/tickets/rooms");
}

export async function fetchTickets(params?: { room_id?: string, assignee_staff_id?: string, status?: string }) {
  const query = new URLSearchParams();
  if (params?.room_id && params.room_id !== "undefined" && params.room_id !== "null") query.append("room_id", params.room_id);
  if (params?.assignee_staff_id && params.assignee_staff_id !== "undefined" && params.assignee_staff_id !== "null") query.append("assignee_staff_id", params.assignee_staff_id);
  if (params?.status && params.status !== "undefined" && params.status !== "null") query.append("status", params.status);
  
  const queryString = query.toString();
  return fetchApi(`/tickets${queryString ? `?${queryString}` : ''}`);
}

export async function fetchTicketDetails(ticketId: string) {
  return fetchApi(`/tickets/${ticketId}`);
}

export async function createTicket(ticketData: any) {
  return fetchApi(`/tickets`, {
    method: "POST",
    body: JSON.stringify(ticketData),
  });
}

export async function postMessage(ticketId: string, content: string, type: string = "comment", file?: File | null) {
  const formData = new FormData();
  formData.append("content", content);
  formData.append("type", type);
  if (file) {
    formData.append("file", file);
  }

  return fetchApi(`/tickets/${ticketId}/messages`, {
    method: "POST",
    body: formData,
  });
}

export async function updateTicket(ticketId: string, updates: any) {
  return fetchApi(`/tickets/${ticketId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export async function approveTicket(ticketId: string) {
  return fetchApi(`/tickets/${ticketId}/approve`, {
    method: "PATCH",
  });
}

export async function fetchAllUsers() {
  return fetchApi(`/users`);
}

export async function fetchRoomMembers(roomId: string) {
  return fetchApi(`/users?room_id=${roomId}`);
}

export async function fetchCurrentUser() {
  return fetchApi(`/users/me`);
}

export async function createUser(userData: any) {
  return fetchApi(`/users`, {
    method: "POST",
    body: JSON.stringify(userData),
  });
}

export async function fetchNotifications(skip: number = 0, limit: number = 20) {
  return fetchApi(`/notifications?skip=${skip}&limit=${limit}`);
}

export async function markNotificationRead(id: string) {
  return fetchApi(`/notifications/${id}/read`, {
    method: "PATCH",
  });
}

export async function fetchAllRooms() {
  return fetchApi(`/rooms/all`);
}

export async function createRoom(roomData: { name: string; type: string }) {
  return fetchApi('/rooms', {
    method: 'POST',
    body: JSON.stringify(roomData),
  });
}

export async function updateUser(userId: string, userData: any) {
  return fetchApi(`/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(userData),
  });
}

export async function deleteUser(userId: string) {
  return fetchApi(`/users/${userId}`, {
    method: "DELETE",
  });
}
