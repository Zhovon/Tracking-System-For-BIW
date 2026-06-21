"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { createTicket, fetchAllRooms, fetchAllUsers } from "@/lib/api";

export function CreateTicketDialog({ roomId }: { roomId?: string | null }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("low");
  const [dueDate, setDueDate] = useState("");
  const [selectedRoomId, setSelectedRoomId] = useState<string>(roomId || "");
  const [assignedToId, setAssignedToId] = useState<string>("");
  const queryClient = useQueryClient();

  const { data: rooms } = useQuery({ queryKey: ["rooms"], queryFn: fetchAllRooms });
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: fetchAllUsers });

  const filteredUsers = users?.filter((u: any) => selectedRoomId && u.room_ids?.includes(selectedRoomId)) || [];

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
      ...(assignedToId && { assigned_to_id: assignedToId }),
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
            <Select value={selectedRoomId} onValueChange={(val) => { setSelectedRoomId(val); setAssignedToId(""); }} required>
              <SelectTrigger>
                <SelectValue placeholder="Select a room" />
              </SelectTrigger>
              <SelectContent>
                {rooms?.map((r: any) => (
                  <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="assignee">Assign To</Label>
            <Select value={assignedToId} onValueChange={setAssignedToId} disabled={!selectedRoomId}>
              <SelectTrigger>
                <SelectValue placeholder={selectedRoomId ? "Select an assignee (Optional)" : "Select a room first"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Unassigned</SelectItem>
                {filteredUsers.map((u: any) => (
                  <SelectItem key={u.id} value={u.id}>{u.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
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
