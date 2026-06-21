"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTickets, fetchTicketDetails, postMessage, updateTicket, fetchAllUsers, fetchAllRooms, approveTicket, fetchCurrentUser } from "@/lib/api";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import { Loader2, Ticket, MessageSquare, Send, CheckCircle2, AlertCircle, ArrowLeft, Paperclip, Download, X, Search, Calendar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CreateTicketDialog } from "@/components/CreateTicketDialog";
import { Input } from "@/components/ui/input";
import { supabase } from "@/lib/supabase";
function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const roomId = searchParams.get("room_id");
  const ticketId = searchParams.get("ticket_id");
  const [sortBy, setSortBy] = useState<"newest" | "oldest">("newest");
  const [filterStaffId, setFilterStaffId] = useState("");
  const [filterStatus, setFilterStatus] = useState<"active" | "resolved">("active");
  const [comment, setComment] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  // Supabase Realtime for Tickets and Messages
  useEffect(() => {
    const channel = supabase.channel('dashboard_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'messages' },
        () => {
          if (ticketId) {
            queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
          }
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'tickets' },
        () => {
          queryClient.invalidateQueries({ queryKey: ["tickets"] });
          if (ticketId) {
            queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [ticketId, queryClient]);
  const { data: fetchedTickets, isLoading, error } = useQuery({
    queryKey: ["tickets", roomId, filterStaffId],
    queryFn: () => fetchTickets({
      room_id: roomId || undefined,
      assignee_staff_id: filterStaffId || undefined,
    }),
    enabled: true,
  });

  const tickets = fetchedTickets ? [...fetchedTickets]
    .filter((t: any) => filterStatus === "resolved" ? t.status === "resolved" : t.status !== "resolved")
    .sort((a, b) => {
      if (sortBy === "newest") {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    }) : [];

  const { data: selectedTicket, isLoading: isTicketLoading, error: ticketError } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => fetchTicketDetails(ticketId as string),
    enabled: !!ticketId,
  });

  const postMessageMutation = useMutation({
    mutationFn: (data: { content: string, file?: File | null }) => postMessage(ticketId as string, data.content, "comment", data.file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      setComment("");
      setSelectedFile(null);
    }
  });

  const updateTicketMutation = useMutation({
    mutationFn: (updates: any) => updateTicket(ticketId as string, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    }
  });

  const { data: allUsers } = useQuery({
    queryKey: ["allUsers"],
    queryFn: fetchAllUsers,
  });

  const { data: currentUser } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
  });
  
  const currentUserRole = currentUser?.role || "";

  const approveTicketMutation = useMutation({
    mutationFn: () => approveTicket(ticketId as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    }
  });

  const { data: allRooms } = useQuery({
    queryKey: ["allRooms"],
    queryFn: fetchAllRooms,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open": return "bg-blue-100 text-blue-800";
      case "in_progress": return "bg-amber-100 text-amber-800";
      case "approved": return "bg-emerald-100 text-emerald-800";
      case "resolved": return "bg-slate-100 text-slate-800";
      default: return "bg-slate-100 text-slate-800";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "text-red-600";
      case "medium": return "text-amber-600";
      case "low": return "text-green-600";
      default: return "text-slate-600";
    }
  };

  return (
    <div className="flex flex-1 h-full overflow-hidden bg-white">
      {/* Middle Column (Feed) */}
      <div className={`flex flex-col border-r border-slate-200 ${ticketId ? 'w-1/3 min-w-[320px] max-w-sm hidden md:flex' : 'w-full'}`}>
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Ticket className="w-5 h-5 text-slate-500" />
              Tickets
            </h2>
            {roomId && (
              <Badge variant="outline" className="text-xs font-normal text-slate-500">
                Filtered
              </Badge>
            )}
          </div>
          {["owner", "manager", "hr", "it_team"].includes(currentUserRole) && (
            <CreateTicketDialog roomId={roomId} />
          )}
        </div>

        <div className="p-4 border-b border-slate-200 space-y-3 bg-slate-50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input 
              placeholder="Search by Staff ID (e.g. 0005)" 
              value={filterStaffId} 
              onChange={(e) => setFilterStaffId(e.target.value)}
              className="pl-9 bg-white"
            />
          </div>
          <div className="flex bg-slate-200/50 p-1 rounded-lg">
            <button 
              onClick={() => setFilterStatus("active")}
              className={`flex-1 text-sm py-1.5 font-medium rounded-md transition-colors ${filterStatus === "active" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              Active
            </button>
            <button 
              onClick={() => setFilterStatus("resolved")}
              className={`flex-1 text-sm py-1.5 font-medium rounded-md transition-colors ${filterStatus === "resolved" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              Resolved
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-8 flex justify-center text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-500 text-sm">
              Failed to load tickets.
            </div>
          ) : tickets?.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              No tickets found in this room.
            </div>
          ) : (
            <div className="divide-y divide-slate-200">
              {tickets?.map((ticket: any) => (
                <div
                  key={ticket.id}
                  onClick={() => router.push(`?${new URLSearchParams({
                    ...(roomId && { room_id: roomId }),
                    ticket_id: ticket.id
                  }).toString()}`)}
                  className={`p-4 cursor-pointer transition-all duration-200 hover:bg-slate-50 hover:shadow-sm hover:z-10 relative hover:-translate-y-0.5 active:scale-[0.98] ${
                    ticket.id === ticketId ? "bg-indigo-50/60 shadow-[inset_4px_0_0_0_#6366f1]" : ""
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium uppercase tracking-wider flex items-center gap-1">
                      <span className={`w-2 h-2 rounded-full ${getPriorityColor(ticket.priority).replace('text-', 'bg-')}`} />
                      {ticket.priority}
                    </span>
                    <div className="flex gap-1">
                      {ticket.approval_status === "pending" && (
                        <Badge variant="outline" className="text-[10px] uppercase font-bold text-amber-500 border-amber-200">
                          Pending
                        </Badge>
                      )}
                      <Badge variant="secondary" className={`text-[10px] uppercase font-bold border-none ${getStatusColor(ticket.status)}`}>
                        {ticket.status.replace("_", " ")}
                      </Badge>
                    </div>
                  </div>
                  <h3 className="font-semibold text-slate-900 text-sm mb-1 leading-tight line-clamp-2">
                    {ticket.title}
                  </h3>
                  <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
                    <span className="truncate flex-1">
                      {ticket.creator.name}
                    </span>
                    <span className="flex-shrink-0">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel (Detail View) */}
      {ticketId ? (
        <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden animate-in slide-in-from-right-8 fade-in duration-300">
          {isTicketLoading ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin mb-4 text-indigo-500" />
              <p>Loading ticket details...</p>
            </div>
          ) : ticketError ? (
            <div className="flex-1 flex flex-col items-center justify-center text-red-500 p-8 text-center">
              <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
              <p className="text-lg font-semibold text-slate-900">Failed to load ticket</p>
              <p className="text-sm text-slate-500 mt-2 max-w-md">
                {(ticketError as Error).message || "An unexpected error occurred. The ticket may have been deleted or you don't have permission to view it."}
              </p>
            </div>
          ) : selectedTicket ? (
            <>
              <div className="p-6 bg-white border-b border-slate-200 flex-shrink-0">
                {/* Mobile Back Button */}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="md:hidden mb-4 -ml-2 text-slate-500 flex items-center gap-2 w-fit hover:bg-slate-100"
                  onClick={() => {
                    const params = new URLSearchParams(window.location.search);
                    params.delete('ticket_id');
                    router.push(`?${params.toString()}`);
                  }}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Tickets
                </Button>

                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    {selectedTicket.approval_status === "pending" && (
                      <Badge variant="outline" className="text-amber-500 border-amber-200 uppercase text-xs tracking-wider">
                        Pending Approval
                      </Badge>
                    )}
                    <Badge variant="secondary" className={`${getStatusColor(selectedTicket.status)} uppercase text-xs tracking-wider border-none`}>
                      {selectedTicket.status.replace("_", " ")}
                    </Badge>
                    <span className={`text-sm font-medium uppercase flex items-center gap-1 ${getPriorityColor(selectedTicket.priority)}`}>
                      Priority: {selectedTicket.priority}
                    </span>
                    {selectedTicket.due_date && (
                      <span className={`text-sm font-medium flex items-center gap-1 ${new Date(selectedTicket.due_date) < new Date() && selectedTicket.status !== "resolved" ? "text-red-600 animate-pulse" : "text-slate-500"}`}>
                        <Calendar className="w-4 h-4" />
                        Due: {new Date(selectedTicket.due_date).toLocaleString()}
                        {new Date(selectedTicket.due_date) < new Date() && selectedTicket.status !== "resolved" && " (OVERDUE)"}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {selectedTicket.approval_status === "pending" && currentUserRole === "owner" && (
                      <Button 
                        variant="default" 
                        size="sm" 
                        className="bg-amber-500 hover:bg-amber-600 text-white"
                        onClick={() => approveTicketMutation.mutate()}
                        disabled={approveTicketMutation.isPending}
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Approve
                      </Button>
                    )}
                    {selectedTicket.status !== "resolved" && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-emerald-600 border-emerald-200 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                        onClick={() => updateTicketMutation.mutate({ status: "resolved" })}
                        disabled={updateTicketMutation.isPending}
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Mark Resolved
                      </Button>
                    )}
                  </div>
                </div>
                <h1 className="text-2xl font-bold text-slate-900 mb-2">
                  {selectedTicket.title}
                </h1>
                
                <div className="flex flex-col md:flex-row gap-4 mt-4 mb-2">
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase mb-1">Assignee</p>
                    <Select 
                      value={selectedTicket.assignee?.id || selectedTicket.assigned_to_id || (typeof selectedTicket.assignee === "string" ? selectedTicket.assignee : null) || "unassigned"} 
                      onValueChange={(val) => updateTicketMutation.mutate({ assigned_to_id: val === "unassigned" ? null : val })}
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 text-xs w-full md:w-[180px]">
                        <div className="truncate">
                          {(() => {
                            const assigneeId = selectedTicket.assignee?.id || selectedTicket.assigned_to_id || (typeof selectedTicket.assignee === "string" ? selectedTicket.assignee : null);
                            const foundUser = allUsers?.find((u: any) => u.id === assigneeId);
                            if (foundUser) {
                              return `${foundUser.staff_id ? `[${foundUser.staff_id}] ` : ""}${foundUser.name}`;
                            }
                            if (selectedTicket.assignee && typeof selectedTicket.assignee === 'object') {
                              return `${selectedTicket.assignee.staff_id ? `[${selectedTicket.assignee.staff_id}] ` : ""}${selectedTicket.assignee.name}`;
                            }
                            return "Unassigned";
                          })()}
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unassigned">Unassigned</SelectItem>
                        {(() => {
                          const assigneeId = selectedTicket.assignee?.id || selectedTicket.assigned_to_id || (typeof selectedTicket.assignee === "string" ? selectedTicket.assignee : null);
                          return allUsers?.filter((u: any) => 
                            selectedTicket.rooms?.some((r: any) => u.room_ids?.includes(r.id)) || u.id === assigneeId
                          ).map((u: any) => (
                            <SelectItem key={u.id} value={u.id} className="text-xs">
                              {u.staff_id ? `[${u.staff_id}] ` : ""}{u.name} ({u.role.replace('_', ' ')})
                            </SelectItem>
                          ));
                        })()}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase mb-1">Escalate to Department</p>
                    <Select 
                      value="placeholder"
                      onValueChange={(val) => updateTicketMutation.mutate({ add_room_id: val })}
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 text-xs w-full md:w-[180px]">
                        <SelectValue placeholder="Escalate..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="placeholder" disabled>Escalate...</SelectItem>
                        {allRooms?.filter((r: any) => 
                          r.type !== 'branch' && !selectedTicket.rooms?.some((tr: any) => tr.id === r.id)
                        ).map((r: any) => (
                          <SelectItem key={r.id} value={r.id} className="text-xs">
                            {r.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mt-3 mb-4">
                  {selectedTicket.rooms?.map((room: any) => (
                    <Badge key={room.id} variant="secondary" className="bg-slate-100 text-slate-600 border border-slate-200">
                      #{room.name}
                    </Badge>
                  ))}
                </div>

                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <span>Opened by <strong className="text-slate-700">{selectedTicket.creator.name}</strong></span>
                  <span>•</span>
                  <span>{new Date(selectedTicket.created_at).toLocaleString()}</span>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
                <div className="max-w-4xl mx-auto">
                  {/* Original Description */}
                  <div className="mb-8 bg-white rounded-xl p-5 shadow-sm border border-slate-100">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3 border-b border-slate-100 pb-2">Description</h3>
                    <p className="text-slate-700 text-sm whitespace-pre-wrap leading-relaxed">
                      {selectedTicket.description}
                    </p>
                  </div>
                  
                  {/* Thread Area */}
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-500 mb-4 uppercase tracking-wider">
                    <MessageSquare className="w-4 h-4" />
                    Thread
                  </div>
                  
                  <div className="space-y-4 mb-8">
                    {selectedTicket.messages?.map((msg: any) => (
                      msg.type === "status_change" ? (
                        <div key={msg.id} className="flex justify-center my-4">
                          <span className="text-xs font-medium text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
                            {msg.author.name} {msg.content.toLowerCase()}
                          </span>
                        </div>
                      ) : (
                        <div key={msg.id} className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm text-slate-900">{msg.author.name}</span>
                            <span className="text-xs text-slate-400">{new Date(msg.created_at).toLocaleString()}</span>
                          </div>
                          <p className="text-sm text-slate-700 whitespace-pre-wrap">{msg.content}</p>
                          {msg.attachment_name && (
                            <div className="mt-3">
                              <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/tickets/messages/${msg.id}/attachment`} target="_blank" rel="noreferrer" className="inline-flex items-center px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-medium hover:bg-indigo-100 transition-colors border border-indigo-100">
                                <Paperclip className="w-3.5 h-3.5 mr-2" />
                                {msg.attachment_name}
                                <Download className="w-3.5 h-3.5 ml-2 opacity-70" />
                              </a>
                            </div>
                          )}
                        </div>
                      )
                    ))}
                    
                    {selectedTicket.messages?.length === 0 && (
                      <div className="text-center text-slate-400 text-sm py-4">
                        No messages yet. Start the conversation!
                      </div>
                    )}
                  </div>
                  
                  {/* Reply Box */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                    {selectedFile && (
                      <div className="mb-2 flex items-center">
                        <span className="inline-flex items-center px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full border border-indigo-100">
                          <Paperclip className="w-3 h-3 mr-1" />
                          <span className="max-w-[200px] truncate">{selectedFile.name}</span>
                          <button onClick={() => setSelectedFile(null)} className="ml-2 text-indigo-400 hover:text-indigo-600">
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      </div>
                    )}
                    <Textarea 
                      placeholder="Type your message here..."
                      className="min-h-[100px] border-none focus-visible:ring-0 shadow-none resize-none p-0"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-100">
                      <div>
                        <input 
                          type="file" 
                          id="file-upload" 
                          className="hidden" 
                          onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                              setSelectedFile(e.target.files[0]);
                            }
                          }}
                        />
                        <label htmlFor="file-upload" className="cursor-pointer inline-flex items-center justify-center w-8 h-8 rounded-full text-slate-400 hover:text-indigo-500 hover:bg-indigo-50 transition-colors">
                          <Paperclip className="w-4 h-4" />
                        </label>
                      </div>
                      <Button 
                        size="sm" 
                        disabled={(!comment.trim() && !selectedFile) || postMessageMutation.isPending}
                        onClick={() => postMessageMutation.mutate({ content: comment, file: selectedFile })}
                      >
                        {postMessageMutation.isPending ? "Sending..." : "Send Message"}
                        {!postMessageMutation.isPending && <Send className="w-4 h-4 ml-2" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>
      ) : (
        <div className="hidden md:flex flex-1 flex-col items-center justify-center bg-slate-50/50 text-slate-400">
          <Ticket className="w-16 h-16 mb-4 text-slate-200" />
          <p className="text-lg font-medium text-slate-500">Select a ticket to view details</p>
          <p className="text-sm text-slate-400 max-w-sm text-center mt-2">
            Click on any ticket in the feed on the left to see its full description and message thread.
          </p>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 flex justify-center text-slate-400"><Loader2 className="w-6 h-6 animate-spin" /></div>}>
      <DashboardContent />
    </Suspense>
  );
}
