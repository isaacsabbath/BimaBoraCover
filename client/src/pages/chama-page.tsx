import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { Header } from "@/components/layout/header";
import { BottomNavigation } from "@/components/layout/bottom-navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Wallet, 
  UserPlus, 
  Stethoscope, 
  Users,
} from "lucide-react";
import { useInsurance } from "@/context/insurance-context";
import { useUser } from "@/context/user-context";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";

export default function ChamaPage() {
  const { group, groupInsurance, loadingUserData } = useInsurance();
  const { user } = useUser();
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const [showContributeModal, setShowContributeModal] = useState(false);
  const [showCreateChamaModal, setShowCreateChamaModal] = useState(false);
  const [contributionAmount, setContributionAmount] = useState(400);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chamaName, setChamaName] = useState("");
  const [chamaDescription, setChamaDescription] = useState("");

  const handleCreateChama = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    
    try {
      setIsSubmitting(true);
      const response = await fetch("/api/groups", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: chamaName,
          description: chamaDescription,
          adminUserId: user.id,
        }),
      });

      if (!response.ok) throw new Error("Failed to create chama");

      toast({
        title: "Success",
        description: "Your chama has been created successfully",
      });
      setShowCreateChamaModal(false);
      // Refresh the page to show the new chama
      window.location.reload();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create chama. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Mock group activities for demonstration
  const [groupActivities, setGroupActivities] = useState([
    {
      id: 1,
      type: "payment",
      title: "Jane Doe made a contribution",
      description: "KSh 400 • 2 days ago",
      icon: <Wallet className="h-5 w-5 text-secondary" />
    },
    {
      id: 2,
      type: "claim",
      title: "New claim submitted",
      description: "Dental procedure for Mary N. • 5 days ago",
      icon: <Stethoscope className="h-5 w-5 text-warning" />
    },
    {
      id: 3,
      type: "member",
      title: "New member joined",
      description: "John Kamau • 1 week ago",
      icon: <UserPlus className="h-5 w-5 text-success" />
    }
  ]);

  const makeContribution = () => {
    if (!user || !group) {
      toast({
        title: "Error",
        description: "You need to be logged in and be a member of a group to make contributions",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    // Simulate API call
    setTimeout(() => {
      // Add a new activity
      const newActivity = {
        id: Date.now(),
        type: "payment",
        title: `${user.fullName} made a contribution`,
        description: `KSh ${contributionAmount} • Just now`,
        icon: <Wallet className="h-5 w-5 text-secondary" />
      };

      setGroupActivities([newActivity, ...groupActivities]);

      // Update the collected amount (this would be done server-side in a real app)
      if (groupInsurance) {
        // This is just for UI demonstration
        const newCollectedAmount = Math.min(
          (groupInsurance.collectedAmount || 0) + contributionAmount,
          groupInsurance.requiredAmount
        );
        
        // In a real app, you would update this through the API
        // and the context would automatically refresh
      }

      setShowContributeModal(false);
      setIsSubmitting(false);

      toast({
        title: "Contribution Successful",
        description: `Your contribution of KSh ${contributionAmount} has been received.`,
      });
    }, 1500);
  };

  if (loadingUserData) {
    return (
      <div className="min-h-screen bg-neutral-100">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-5 pb-24">
          <div className="mb-6 h-6 w-40 bg-neutral-200 animate-pulse rounded"></div>
          <Card className="bg-white rounded-xl shadow-sm mb-6">
            <CardContent className="p-4">
              <div className="h-40 bg-neutral-100 animate-pulse rounded"></div>
            </CardContent>
          </Card>
        </main>
        <BottomNavigation />
      </div>
    );
  }

  if (!group || !groupInsurance) {
    return (
      <div className="min-h-screen bg-neutral-100">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-5 pb-24">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-neutral-800 mb-1">My Chama</h2>
            <p className="text-neutral-600">Manage your group insurance with your community.</p>
          </div>
          
          <Card className="bg-white rounded-xl shadow-sm mb-6">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-neutral-100 flex items-center justify-center mx-auto mb-4">
                <Users className="h-8 w-8 text-neutral-400" />
              </div>
              <p className="text-neutral-700 mb-4">You're not part of any Chama group yet.</p>
              <p className="text-neutral-600 text-sm mb-6">
                Join a Chama group to pool resources with your community for better insurance coverage.
              </p>
              <Button>
                Join or Create a Chama
              </Button>
            </CardContent>
          </Card>
        </main>
        <BottomNavigation />
      </div>
    );
  }

  const collectionProgress = Math.min(
    100,
    Math.round((groupInsurance.collectedAmount / groupInsurance.requiredAmount) * 100)
  );

  return (
    <div className="min-h-screen bg-neutral-100">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-5 pb-24">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-neutral-800 mb-1">My Chama</h2>
          <p className="text-neutral-600">Manage your group insurance with your community.</p>
        </div>

        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className="w-12 h-12 rounded-full bg-primary-light flex items-center justify-center text-primary font-bold mr-3">
                  {group.name.split(' ').map(part => part[0]).join('').toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-neutral-800">{group.name}</h3>
                  <p className="text-sm text-neutral-500">
                    12 members • Created {format(new Date(group.createdAt), "MMM d, yyyy")}
                  </p>
                </div>
              </div>
              <span className="bg-success bg-opacity-10 text-success text-xs font-semibold px-2 py-1 rounded-full">
                Active
              </span>
            </div>

            <div className="flex flex-col sm:flex-row sm:justify-between gap-4 py-3 border-y border-neutral-200">
              <div>
                <p className="text-neutral-500 text-sm">Group Plan</p>
                <p className="font-bold text-neutral-800">Family Coverage Plus</p>
              </div>
              <div>
                <p className="text-neutral-500 text-sm">Monthly Premium</p>
                <p className="font-bold text-neutral-800">
                  KSh {groupInsurance.monthlyPremium.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-neutral-500 text-sm">Your Contribution</p>
                <p className="font-bold text-neutral-800">
                  KSh 400 <span className="text-xs text-neutral-500">/ month</span>
                </p>
              </div>
            </div>

            <div className="my-4">
              <p className="text-neutral-700 font-semibold mb-3">Group Payment Status</p>
              <div className="h-3 w-full bg-neutral-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-success rounded-full" 
                  style={{ width: `${collectionProgress}%` }}
                ></div>
              </div>
              <div className="flex justify-between mt-1">
                <p className="text-xs text-neutral-500">
                  KSh {groupInsurance.collectedAmount.toLocaleString()} collected
                </p>
                <p className="text-xs text-neutral-500">
                  KSh {(groupInsurance.requiredAmount - groupInsurance.collectedAmount).toLocaleString()} remaining
                </p>
              </div>
              <p className="text-sm text-neutral-600 mt-2">
                Next payment due: {format(new Date(groupInsurance.nextPaymentDate), "d MMM yyyy")}
              </p>
            </div>

            <div className="mt-4">
              <Button 
                className="w-full py-2.5 mb-2"
                onClick={() => setShowContributeModal(true)}
              >
                Make Contribution
              </Button>
              <Button 
                variant="outline"
                className="w-full py-2.5 mb-2 hover:bg-neutral-100"
                onClick={() => setLocation("/group-details")}
              >
                View Group Details
              </Button>
              <Button
                variant="outline"
                className="w-full py-2.5 hover:bg-primary hover:text-white transition-colors"
                onClick={() => setShowCreateChamaModal(true)}
              >
                Create New Chama
              </Button>

      {/* Create Chama Modal */}
      {showCreateChamaModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md rounded-xl">
            <CardContent className="p-6">
              <h3 className="text-xl font-bold text-neutral-800 mb-4">Create New Chama</h3>
              <form onSubmit={handleCreateChama} className="space-y-4">
                <div>
                  <label className="block text-neutral-700 font-semibold mb-2">
                    Chama Name
                  </label>
                  <input
                    type="text"
                    value={chamaName}
                    onChange={(e) => setChamaName(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50 hover:border-primary"
                    placeholder="Enter chama name"
                  />
                </div>
                <div>
                  <label className="block text-neutral-700 font-semibold mb-2">
                    Description
                  </label>
                  <textarea
                    value={chamaDescription}
                    onChange={(e) => setChamaDescription(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50 hover:border-primary"
                    placeholder="Describe your chama"
                    rows={3}
                  />
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    className="flex-1 hover:bg-neutral-100"
                    onClick={() => setShowCreateChamaModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1 hover:bg-primary-dark"
                  >
                    Create Chama
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
            </div>
          </CardContent>
        </Card>

        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-neutral-800">Recent Group Activity</h3>
          </div>
          
          <Card className="bg-white rounded-xl shadow-sm">
            <CardContent className="p-0">
              <div className="divide-y divide-neutral-100">
                {groupActivities.map((activity) => (
                  <div key={activity.id} className="p-4 flex items-start">
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center mr-3 flex-shrink-0
                      ${activity.type === 'payment' ? 'bg-secondary bg-opacity-10' : ''}
                      ${activity.type === 'claim' ? 'bg-warning bg-opacity-10' : ''}
                      ${activity.type === 'member' ? 'bg-success bg-opacity-10' : ''}
                    `}>
                      {activity.icon}
                    </div>
                    <div className="flex-grow">
                      <h4 className="font-semibold text-neutral-800">{activity.title}</h4>
                      <p className="text-neutral-500 text-sm">{activity.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Contribution Modal */}
      {showContributeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md rounded-xl">
            <CardContent className="p-6">
              <h3 className="text-xl font-bold text-neutral-800 mb-4">Make a Contribution</h3>
              
              <div className="mb-6">
                <label className="block text-neutral-700 font-semibold mb-2">
                  Contribution Amount (KSh)
                </label>
                <input
                  type="number"
                  value={contributionAmount}
                  onChange={(e) => setContributionAmount(parseInt(e.target.value))}
                  className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                />
              </div>
              
              <div className="mb-6">
                <label className="block text-neutral-700 font-semibold mb-2">
                  Payment Method
                </label>
                <div className="border border-primary rounded-lg p-3 flex items-center">
                  <div className="w-10 h-10 rounded-full bg-neutral-100 flex items-center justify-center mr-3">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 0C5.373 0 0 5.373 0 12C0 18.627 5.373 24 12 24C18.627 24 24 18.627 24 12C24 5.373 18.627 0 12 0Z" fill="#4CAF50"/>
                      <path d="M17 7H7C6.448 7 6 7.448 6 8V16C6 16.552 6.448 17 7 17H17C17.552 17 18 16.552 18 16V8C18 7.448 17.552 7 17 7Z" fill="white"/>
                      <path d="M13 12C13 12.552 12.552 13 12 13C11.448 13 11 12.552 11 12C11 11.448 11.448 11 12 11C12.552 11 13 11.448 13 12Z" fill="#4CAF50"/>
                    </svg>
                  </div>
                  <div className="flex-grow">
                    <p className="font-semibold text-neutral-800">M-Pesa</p>
                    <p className="text-sm text-neutral-600">Pay directly from your mobile money</p>
                  </div>
                  <input 
                    type="radio" 
                    checked={true}
                    className="w-5 h-5 text-primary"
                    readOnly
                  />
                </div>
              </div>
              
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowContributeModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={makeContribution}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Processing..." : "Pay Now"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <BottomNavigation />
    </div>
  );
}
