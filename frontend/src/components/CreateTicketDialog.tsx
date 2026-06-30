"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { createTicket, fetchAllRooms, fetchAllUsers, fetchRoomMembers } from "@/lib/api";

export function CreateTicketDialog({ roomId }: { roomId?: string | null }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("low");
  const [dueDate, setDueDate] = useState("");
  const [selectedRoomId, setSelectedRoomId] = useState<string>(roomId || "");
  const [assignedToId, setAssignedToId] = useState<string>("");
  const [assigneeSearch, setAssigneeSearch] = useState("");
  const queryClient = useQueryClient();

  const { data: rooms } = useQuery({ queryKey: ["allRooms"], queryFn: fetchAllRooms });

  const selectedRoom = rooms?.find((r: any) => r.id === selectedRoomId);
  const isUniversalRoom = selectedRoom?.type === "universal" || selectedRoom?.name?.toLowerCase() === "universal";

  const { data: roomMembers } = useQuery({
    queryKey: ["roomMembers", selectedRoomId],
    queryFn: () => fetchRoomMembers(selectedRoomId),
    enabled: !!selectedRoomId && !isUniversalRoom,
  });

  const filteredUsers = roomMembers || [];

  const createTicketMutation = useMutation({
    mutationFn: async (newTicket: any) => {
      return await createTicket(newTicket);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      setOpen(false);
      setTitle("");
      setDescription("");
      setPriority("low");
      setDueDate("");
      setSelectedRoomId(roomId || "");
      setAssignedToId("");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRoomId) return;
    createTicketMutation.mutate({
      title,
      description,
      priority,
      room_ids: [selectedRoomId],
      ...(assignedToId && assignedToId !== "none" && { assigned_to_id: assignedToId }),
      ...(dueDate && { due_date: new Date(dueDate).toISOString() })
    });
  };

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>New Ticket</Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Ticket</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Brief summary of the issue"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Provide detailed context..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              className="min-h-[100px]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Select value={priority} onValueChange={(val) => setPriority(val || "low")}>
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="room">Room</Label>
            <Select value={selectedRoomId} onValueChange={(val) => { setSelectedRoomId(val || ""); setAssignedToId(""); }} required>
              <SelectTrigger>
                <SelectValue placeholder="Select a room">
                  {rooms?.find((r: any) => r.id === selectedRoomId)?.name || "Select a room"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {rooms?.map((r: any) => (
                  <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {isUniversalRoom ? (
            <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-md text-sm text-indigo-800">
              <span className="font-semibold">Notice Board:</span> Announcements in the Universal room are broadcast to all employees. No assignee required.
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="assignee">Assign To</Label>
              <Select
                value={assignedToId}
                onValueChange={(val) => setAssignedToId(val || "")}
                onOpenChange={(open) => {
                  if (!open) setAssigneeSearch("");
                }}
                disabled={!selectedRoomId}
              >
                <SelectTrigger>
                  <SelectValue placeholder={selectedRoomId ? "Select an assignee (Optional)" : "Select a room first"}>
                    {assignedToId === "none" ? "Unassigned" : (filteredUsers.find((u: any) => u.id === assignedToId)?.name || (selectedRoomId ? "Select an assignee (Optional)" : "Select a room first"))}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  <div className="p-1">
                    <Input
                      placeholder="Search assignee..."
                      value={assigneeSearch}
                      onChange={(e) => setAssigneeSearch(e.target.value)}
                      onKeyDown={(e) => e.stopPropagation()}
                      onPointerDown={(e) => e.stopPropagation()}
                      onMouseDown={(e) => e.stopPropagation()}
                      onClick={(e) => e.stopPropagation()}
                      className="h-8 text-xs mb-1 bg-slate-50 focus:bg-white"
                    />
                  </div>
                  <SelectItem value="none">Unassigned</SelectItem>
                  {(() => {
                    const filtered = filteredUsers.filter((u: any) => {
                      const query = assigneeSearch.toLowerCase().trim();
                      if (!query) return true;
                      const nameMatch = u.name?.toLowerCase().includes(query);
                      const staffIdMatch = u.staff_id?.toLowerCase().includes(query);
                      return nameMatch || staffIdMatch;
                    });

                    if (filtered.length === 0) {
                      return (
                        <div className="text-slate-400 text-center py-2 text-xs">
                          No staff found
                        </div>
                      );
                    }

                    return filtered.map((u: any) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.staff_id ? `[${u.staff_id}] ` : ""}
                        {u.name}
                      </SelectItem>
                    ));
                  })()}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="due_date">Deadline (Optional)</Label>
            <Input
              id="due_date"
              type="datetime-local"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="pt-4 flex justify-end">
            <Button
              type="submit"
              disabled={createTicketMutation.isPending}
            >
              {createTicketMutation.isPending ? "Creating..." : "Submit Ticket"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
    </>
  );
}
