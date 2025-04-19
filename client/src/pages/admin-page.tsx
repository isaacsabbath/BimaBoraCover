
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { PlusCircle, Search } from "lucide-react";
import { Header } from "@/components/layout/header";
import { useToast } from "@/hooks/use-toast";
import { User, Claim, InsurancePlan, Payment } from "@shared/schema";

export default function AdminPage() {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");

  // Fetch data
  const { data: users = [] } = useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: () => fetch("/api/admin/users").then((res) => res.json()),
  });

  const { data: claims = [] } = useQuery<Claim[]>({
    queryKey: ["admin", "claims"],
    queryFn: () => fetch("/api/admin/claims").then((res) => res.json()),
  });

  const { data: payments = [] } = useQuery<Payment[]>({
    queryKey: ["admin", "payments"],
    queryFn: () => fetch("/api/admin/payments").then((res) => res.json()),
  });

  const { data: plans = [] } = useQuery<InsurancePlan[]>({
    queryKey: ["admin", "plans"],
    queryFn: () => fetch("/api/admin/plans").then((res) => res.json()),
  });

  const handleClaimAction = async (id: number, action: "approve" | "reject") => {
    try {
      await fetch(`/api/admin/claims/${id}/${action}`, { method: "POST" });
      toast({
        title: "Success",
        description: `Claim ${action}ed successfully`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${action} claim`,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
        
        <Tabs defaultValue="claims">
          <TabsList>
            <TabsTrigger value="claims">Claims</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="payments">Payments</TabsTrigger>
            <TabsTrigger value="plans">Insurance Plans</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <div className="my-4 flex gap-4">
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-xs"
              icon={<Search className="h-4 w-4" />}
            />
            <Dialog>
              <DialogTrigger asChild>
                <Button>
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Add New
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add New Item</DialogTitle>
                </DialogHeader>
                {/* Add form based on selected tab */}
              </DialogContent>
            </Dialog>
          </div>

          <TabsContent value="claims" className="space-y-4">
            <DataTable
              data={claims}
              columns={[
                { accessorKey: "id", header: "ID" },
                { accessorKey: "claimType", header: "Type" },
                { accessorKey: "amount", header: "Amount" },
                { accessorKey: "status", header: "Status" },
                {
                  id: "actions",
                  cell: ({ row }) => (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleClaimAction(row.original.id, "approve")}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleClaimAction(row.original.id, "reject")}
                      >
                        Reject
                      </Button>
                    </div>
                  ),
                },
              ]}
            />
          </TabsContent>

          {/* Other tab contents */}
        </Tabs>
      </main>
    </div>
  );
}
