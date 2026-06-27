"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createUser, updateUser, deleteUser, fetchAllRooms, fetchAllUsers, createRoom } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertCircle, CheckCircle2, Loader2, UserPlus, ShieldAlert, Edit2, Trash2, X } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

export default function StaffManagementPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "therapist",
    room_ids: [] as string[],
    phone: "",
    nid: "",
    joining_date: ""
  });

  // Check if current user is owner (in real app, we'd check their role token)
  const { data: users, isLoading: loadingUsers } = useQuery({
    queryKey: ['admin-users'],
    queryFn: fetchAllUsers
  });

  const { data: rooms } = useQuery({
    queryKey: ['admin-rooms'],
    queryFn: fetchAllRooms
  });

  const [editingUser, setEditingUser] = useState<any>(null);
  const [editFormData, setEditFormData] = useState({ name: "", email: "", password: "", role: "", room_ids: [] as string[], phone: "", nid: "", joining_date: "" });

  const [roomFormData, setRoomFormData] = useState({ name: "", type: "branch" });
  const [roomSuccess, setRoomSuccess] = useState(false);
  const [roomError, setRoomError] = useState<string | null>(null);

  const createRoomMutation = useMutation({
    mutationFn: createRoom,
    onSuccess: () => {
      setRoomSuccess(true);
      setRoomError(null);
      setRoomFormData({ name: "", type: "branch" });
      queryClient.invalidateQueries({ queryKey: ["admin-rooms"] });
      queryClient.invalidateQueries({ queryKey: ["allRooms"] });
      queryClient.invalidateQueries({ queryKey: ["rooms"] });
      setTimeout(() => setRoomSuccess(false), 4000);
    },
    onError: (err: any) => {
      setRoomError(err.message);
      setRoomSuccess(false);
    },
  });
  const currentUserRole = "owner"; // Assumed owner role for this restricted page

  const updateMutation = useMutation({
    mutationFn: (data: any) => updateUser(data.id, data.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setEditingUser(null);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    }
  });

  const handleEditClick = (user: any) => {
    setEditFormData({
      name: user.name,
      email: user.email,
      password: "",
      role: user.role,
      room_ids: user.room_ids || [],
      phone: user.phone || "",
      nid: user.nid || "",
      joining_date: user.joining_date || ""
    });
    setEditingUser(user);
  };

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      setSuccess(true);
      setError(null);
      setFormData({ name: "", email: "", password: "", role: "therapist", room_ids: [], phone: "", nid: "", joining_date: "" });
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setTimeout(() => setSuccess(false), 5000);
    },
    onError: (err: any) => {
      setError(err.message);
      setSuccess(false);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const filteredUsers = users?.filter((user: any) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      (user.name && user.name.toLowerCase().includes(q)) ||
      (user.staff_id && user.staff_id.toLowerCase().includes(q)) ||
      (user.email && user.email.toLowerCase().includes(q)) ||
      (user.phone && user.phone.toLowerCase().includes(q)) ||
      (user.nid && user.nid.toLowerCase().includes(q)) ||
      (user.joining_date && user.joining_date.toLowerCase().includes(q))
    );
  });

  return (
    <>
      <div className="flex-1 overflow-auto bg-slate-50 p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <UserPlus className="h-8 w-8 text-indigo-500" />
            Staff Management
          </h1>
          <p className="text-slate-500 mt-2">Provision new employee accounts and assign them to branches.</p>
          <Alert className="mt-4 bg-amber-500/10 border-amber-500/20 text-amber-500">
            <ShieldAlert className="h-4 w-4" />
            <AlertDescription>
              This area is highly restricted. Only Owners can create new staff accounts. Accounts created here bypass email verification and are active immediately.
            </AlertDescription>
          </Alert>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* Left Column (Create Account & Create Room stack) */}
          <div className="lg:col-span-1 space-y-8 flex flex-col">
            <Card className="bg-white border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-xl text-slate-900">Create Account</CardTitle>
                <CardDescription className="text-slate-500">Fill out the details for the new staff member.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-400 p-3">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">{error}</AlertDescription>
                    </Alert>
                  )}
                  {success && (
                    <Alert className="bg-green-500/10 border-green-500/20 text-green-400 p-3">
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertDescription className="text-xs">User successfully created.</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Full Name</label>
                    <Input required placeholder="Jane Doe" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Email Address</label>
                    <Input type="email" required placeholder="jane@biw.com" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Temporary Password</label>
                    <Input type="text" required placeholder="password123" value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Role</label>
                    <Select value={formData.role} onValueChange={(val) => setFormData({...formData, role: val || "therapist"})}>
                      <SelectTrigger className="bg-slate-50 border-slate-200 text-slate-900">
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent className="bg-white border-slate-200 text-slate-900">
                        <SelectItem value="therapist">Therapist</SelectItem>
                        <SelectItem value="manager">Branch Manager</SelectItem>
                        <SelectItem value="hr">HR</SelectItem>
                        <SelectItem value="it_team">IT Support</SelectItem>
                        <SelectItem value="executive">Executive</SelectItem>
                        <SelectItem value="cleaner">Cleaner</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Phone Number</label>
                    <Input placeholder="e.g. 017XXXXXXXX" value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">NID / Birth Certificate Number</label>
                    <Input placeholder="e.g. 2864914250" value={formData.nid} onChange={(e) => setFormData({...formData, nid: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Joining Date</label>
                    <Input placeholder="e.g. 20 August 2024" value={formData.joining_date} onChange={(e) => setFormData({...formData, joining_date: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Initial Branch(es) / Department(s)</label>
                    <div className="border border-slate-200 bg-slate-50 rounded-md p-3 max-h-48 overflow-y-auto space-y-2">
                      {rooms?.map((r: any) => (
                        <label key={r.id} className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
                          <input
                            type="checkbox"
                            className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500"
                            checked={formData.room_ids.includes(r.id)}
                            onChange={(e) => {
                              const newRoomIds = e.target.checked 
                                ? [...formData.room_ids, r.id]
                                : formData.room_ids.filter((id) => id !== r.id);
                              setFormData({...formData, room_ids: newRoomIds});
                            }}
                          />
                          {r.name} ({r.type})
                        </label>
                      ))}
                      {(!rooms || rooms.length === 0) && <p className="text-xs text-slate-500">No rooms available.</p>}
                    </div>
                  </div>

                  <Button type="submit" disabled={createMutation.isPending} className="w-full bg-indigo-500 hover:bg-indigo-600 text-white mt-4">
                    {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <UserPlus className="h-4 w-4 mr-2" />}
                    Provision Account
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-xl text-slate-900">Create Room</CardTitle>
                <CardDescription className="text-slate-500">Add a new department or branch (e.g. Doctors).</CardDescription>
              </CardHeader>
              <CardContent>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!roomFormData.name.trim()) return;
                    createRoomMutation.mutate(roomFormData);
                  }}
                  className="space-y-4"
                >
                  {roomError && (
                    <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-400 p-3">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">{roomError}</AlertDescription>
                    </Alert>
                  )}
                  {roomSuccess && (
                    <Alert className="bg-green-500/10 border-green-500/20 text-green-400 p-3">
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertDescription className="text-xs">Room created successfully.</AlertDescription>
                    </Alert>
                  )}
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Room Name</label>
                    <Input
                      required
                      placeholder="e.g. Doctors"
                      value={roomFormData.name}
                      onChange={(e) => setRoomFormData({ ...roomFormData, name: e.target.value })}
                      className="bg-slate-50 border-slate-200 text-slate-900"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-700">Room Type</label>
                    <Select value={roomFormData.type} onValueChange={(val) => setRoomFormData({ ...roomFormData, type: val || "branch" })}>
                      <SelectTrigger className="bg-slate-50 border-slate-200 text-slate-900">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="branch">Branch</SelectItem>
                        <SelectItem value="department">Department</SelectItem>
                        <SelectItem value="founder">Founder</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    disabled={createRoomMutation.isPending}
                    className="w-full bg-indigo-500 hover:bg-indigo-600 text-white mt-2"
                  >
                    {createRoomMutation.isPending ? (
                      <><Loader2 className="h-4 w-4 animate-spin mr-2" />Creating…</>
                    ) : (
                      "Create Room"
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Right Column (Active Staff Directory) */}
          <Card className="lg:col-span-2 bg-white border-slate-200 shadow-sm flex flex-col h-full self-start">
            <CardHeader>
              <CardTitle className="text-xl text-slate-900">Active Staff Directory</CardTitle>
              <CardDescription className="text-slate-500">All users currently in the system.</CardDescription>
              <div className="mt-4">
                <Input
                  placeholder="Search by name, ID, email, phone, or NID/Birth Certificate..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-slate-50 border-slate-200 text-slate-900"
                />
              </div>
            </CardHeader>
            <CardContent>
              {loadingUsers ? (
                <div className="flex flex-col gap-3 animate-pulse">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex flex-col gap-2 flex-1">
                        <div className="flex items-center gap-2">
                          <Skeleton className="h-4 w-32 bg-slate-200" />
                          <Skeleton className="h-3.5 w-16 bg-slate-200" />
                        </div>
                        <Skeleton className="h-3.5 w-48 bg-slate-200" />
                      </div>
                      <Skeleton className="h-7 w-20 bg-slate-200 rounded-md" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="max-h-[640px] overflow-y-auto pr-2 flex flex-col gap-3 custom-scrollbar">
                  {filteredUsers?.map((user: any) => (
                    <div key={user.id} className={`p-4 rounded-xl border ${user.has_penalty ? 'border-red-200 bg-red-50/50 hover:bg-red-50' : 'border-slate-200 bg-slate-50/50 hover:bg-slate-50'} flex flex-col sm:flex-row sm:items-start sm:items-center justify-between gap-3 transition-colors`}>
                      <div className="flex flex-col min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-slate-900 truncate">{user.name}</p>
                          {user.staff_id && (
                            <span className="text-[10px] bg-indigo-100 text-indigo-700 font-mono px-1.5 py-0.5 rounded">ID: {user.staff_id}</span>
                          )}
                          {user.has_penalty && (
                            <span className="text-[10px] bg-red-500 text-white font-bold px-1.5 py-0.5 rounded flex items-center gap-1 uppercase tracking-wider">
                              <AlertCircle className="w-3 h-3" /> Penalty
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-500 truncate">{user.email}</p>
                        
                        {/* Display phone, NID, and joining date */}
                        <div className="text-xs text-slate-500 mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
                          {user.phone && <span className="flex items-center gap-1">📞 {user.phone}</span>}
                          {user.nid && <span className="flex items-center gap-1">🪪 NID/Cert: {user.nid}</span>}
                          {user.joining_date && <span className="flex items-center gap-1">📅 Hired: {user.joining_date}</span>}
                        </div>

                        {user.has_penalty && user.penalty_reasons?.length > 0 && (
                          <div className="mt-2 flex flex-col gap-1">
                            {user.penalty_reasons.map((reason: string, i: number) => (
                              <p key={i} className="text-[11px] font-medium text-red-600 flex items-center gap-1">
                                • {reason}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <span className="bg-white px-3 py-1 rounded-md text-xs font-medium capitalize text-slate-600 border border-slate-200 shadow-sm inline-block">
                          {user.role.replace('_', ' ')}
                        </span>
                        {currentUserRole === "owner" && (
                          <div className="flex gap-1 border-l border-slate-200 pl-3">
                            <button onClick={() => handleEditClick(user)} className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors" title="Edit User">
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button onClick={() => { if(confirm("Are you sure you want to delete this user? This cannot be undone.")) { deleteMutation.mutate(user.id) } }} className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors" title="Delete User">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
      
      {/* Edit User Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h3 className="font-semibold text-slate-900">Edit Staff Account</h3>
              <button onClick={() => setEditingUser(null)}><X className="w-5 h-5 text-slate-400 hover:text-slate-600" /></button>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Full Name</label>
                  <Input value={editFormData.name} onChange={(e) => setEditFormData({...editFormData, name: e.target.value})} className="bg-slate-50" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Email Address</label>
                  <Input type="email" value={editFormData.email} onChange={(e) => setEditFormData({...editFormData, email: e.target.value})} className="bg-slate-50" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">New Password (leave blank to keep current)</label>
                  <Input type="text" placeholder="New password" value={editFormData.password} onChange={(e) => setEditFormData({...editFormData, password: e.target.value})} className="bg-slate-50" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Role</label>
                  <Select value={editFormData.role} onValueChange={(val) => setEditFormData({...editFormData, role: val || ""})}>
                    <SelectTrigger className="bg-slate-50"><SelectValue placeholder="Select role" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="therapist">Therapist</SelectItem>
                      <SelectItem value="manager">Branch Manager</SelectItem>
                      <SelectItem value="hr">HR</SelectItem>
                      <SelectItem value="it_team">IT Support</SelectItem>
                      <SelectItem value="executive">Executive</SelectItem>
                      <SelectItem value="cleaner">Cleaner</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Phone Number</label>
                  <Input value={editFormData.phone} onChange={(e) => setEditFormData({...editFormData, phone: e.target.value})} className="bg-slate-50" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">NID / Birth Certificate Number</label>
                  <Input value={editFormData.nid} onChange={(e) => setEditFormData({...editFormData, nid: e.target.value})} className="bg-slate-50" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Joining Date</label>
                  <Input value={editFormData.joining_date} onChange={(e) => setEditFormData({...editFormData, joining_date: e.target.value})} className="bg-slate-50" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Assign to Branch(es)</label>
                  <div className="border border-slate-200 bg-slate-50 rounded-md p-3 max-h-48 overflow-y-auto space-y-2">
                    {rooms?.map((r: any) => (
                      <label key={r.id} className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
                        <input
                          type="checkbox"
                          className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500"
                          checked={editFormData.room_ids.includes(r.id)}
                          onChange={(e) => {
                            const newRoomIds = e.target.checked 
                              ? [...editFormData.room_ids, r.id]
                              : editFormData.room_ids.filter((id) => id !== r.id);
                            setEditFormData({...editFormData, room_ids: newRoomIds});
                          }}
                        />
                        {r.name} ({r.type})
                      </label>
                    ))}
                    {(!rooms || rooms.length === 0) && <p className="text-xs text-slate-500">No rooms available.</p>}
                  </div>
                </div>
                
                <Button 
                  className="w-full mt-4 bg-indigo-500 hover:bg-indigo-600 text-white" 
                  disabled={updateMutation.isPending}
                  onClick={() => {
                    const payload: any = {};
                    if(editFormData.name) payload.name = editFormData.name;
                    if(editFormData.email) payload.email = editFormData.email;
                    if(editFormData.password) payload.password = editFormData.password;
                    if(editFormData.role) payload.role = editFormData.role;
                    if(editFormData.room_ids && editFormData.room_ids.length > 0) payload.room_ids = editFormData.room_ids;
                    payload.phone = editFormData.phone;
                    payload.nid = editFormData.nid;
                    payload.joining_date = editFormData.joining_date;
                    updateMutation.mutate({ id: editingUser.id, payload });
                  }}
                >
                  {updateMutation.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
