const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getHeaders() {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };
  if (typeof window !== "undefined") {
    const mockUser = localStorage.getItem("mock_user");
    if (mockUser) {
      headers["X-Mock-User"] = mockUser;
    }
  }
  return headers;
}

export async function fetchRooms() {
  const res = await fetch(`${API_BASE_URL}/tickets/rooms`, { headers: getHeaders() });
  if (!res.ok) {
    throw new Error("Failed to fetch rooms");
  }
  return res.json();
}

export async function fetchTickets(roomId?: string) {
  const url = roomId 
    ? `${API_BASE_URL}/tickets?room_id=${roomId}` 
    : `${API_BASE_URL}/tickets`;
    
  const res = await fetch(url, { headers: getHeaders() });
  if (!res.ok) {
    throw new Error("Failed to fetch tickets");
  }
  return res.json();
}

export async function fetchTicketDetails(ticketId: string) {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, { headers: getHeaders() });
  if (!res.ok) {
    throw new Error("Failed to fetch ticket details");
  }
  return res.json();
}

export async function createTicket(ticketData: any) {
  const res = await fetch(`${API_BASE_URL}/tickets`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(ticketData),
  });
  if (!res.ok) throw new Error("Failed to create ticket");
  return res.json();
}

export async function postMessage(ticketId: string, content: string, type: string = "comment") {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/messages`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ content, type }),
  });
  if (!res.ok) throw new Error("Failed to post message");
  return res.json();
}

export async function updateTicket(ticketId: string, updates: any) {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, {
    method: "PATCH",
    headers: getHeaders(),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update ticket");
  return res.json();
}

export async function approveTicket(ticketId: string) {
  const res = await fetch(`${API_BASE_URL}/tickets/${ticketId}/approve`, {
    method: "PATCH",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to approve ticket");
  return res.json();
}

export async function fetchAllUsers() {
  const res = await fetch(`${API_BASE_URL}/users`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

export async function fetchNotifications() {
  const res = await fetch(`${API_BASE_URL}/notifications`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch notifications");
  return res.json();
}

export async function markNotificationRead(id: string) {
  const res = await fetch(`${API_BASE_URL}/notifications/${id}/read`, {
    method: "PATCH",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to mark notification as read");
  return res.json();
}

export async function fetchAllRooms() {
  const res = await fetch(`${API_BASE_URL}/rooms/all`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch all rooms");
  return res.json();
}
