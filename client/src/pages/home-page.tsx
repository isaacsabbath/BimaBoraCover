import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { 
  PlusCircle, 
  Wallet, 
  Users, 
  HelpCircle,
  Stethoscope,
  Pill
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { BottomNavigation } from "@/components/layout/bottom-navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useUser } from "@/context/user-context";
import { useInsurance } from "@/context/insurance-context";
import { format } from "date-fns";

export default function HomePage() {
  const { user } = useUser();
  const { 
    userInsurance, 
    plans, 
    claims, 
    loadingUserData 
  } = useInsurance();
  const [, setLocation] = useLocation();
  const [activePlan, setActivePlan] = useState<{ name: string; coverageAmount: number } | null>(null);

  useEffect(() => {
    if (userInsurance && plans.length > 0) {
      const plan = plans.find(p => p.id === userInsurance.planId);
      if (plan) {
        setActivePlan({
          name: plan.name,
          coverageAmount: plan.coverageAmount
        });
      }
    } else {
      setActivePlan(null);
    }
  }, [userInsurance, plans]);

  const formatCurrency = (amount: number) => {
    return `KSh ${amount.toLocaleString()}`;
  };

  const formatDate = (date: Date | undefined) => {
    if (!date) return "";
    return format(new Date(date), "dd MMM");
  };

  if (loadingUserData) {
    return (
      <div className="min-h-screen bg-neutral-100">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-5 pb-24">
          <div className="mb-6 h-6 w-40 bg-neutral-200 animate-pulse rounded"></div>
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
            <div className="h-24 bg-neutral-100 animate-pulse rounded"></div>
          </div>
          <div className="h-6 w-32 bg-neutral-200 animate-pulse rounded mb-4"></div>
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
            <div className="h-28 bg-neutral-100 animate-pulse rounded"></div>
          </div>
          <div className="h-6 w-32 bg-neutral-200 animate-pulse rounded mb-4"></div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm p-4 h-24 animate-pulse"></div>
            ))}
          </div>
        </main>
        <BottomNavigation />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-100">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-5 pb-24">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-neutral-800 mb-1">Jambo, {user?.fullName?.split(' ')[0] || 'User'}!</h2>
          <p className="text-neutral-600">Your protection journey begins here.</p>
        </div>

        {/* Summary Card */}
        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-lg text-neutral-800">My Coverage</h3>
              {userInsurance && (
                <span className="bg-success bg-opacity-10 text-success text-xs font-semibold px-2 py-1 rounded-full">
                  Active
                </span>
              )}
            </div>
            
            {userInsurance && activePlan ? (
              <>
                <div className="flex flex-col sm:flex-row sm:justify-between gap-4">
                  <div>
                    <p className="text-neutral-500 text-sm">Current Plan</p>
                    <p className="font-bold text-neutral-800">{activePlan.name}</p>
                  </div>
                  <div>
                    <p className="text-neutral-500 text-sm">Coverage Amount</p>
                    <p className="font-bold text-neutral-800">{formatCurrency(activePlan.coverageAmount)}</p>
                  </div>
                  <div>
                    <p className="text-neutral-500 text-sm">Next Payment</p>
                    <p className="font-bold text-neutral-800">
                      {formatCurrency(userInsurance.nextPaymentAmount || 0)} 
                      <span className="text-xs text-neutral-500">
                        {" on "}{formatDate(userInsurance.nextPaymentDate)}
                      </span>
                    </p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-neutral-200">
                  <Button 
                    className="w-full py-2"
                    onClick={() => setLocation('/payment')}
                  >
                    View Details
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-center py-6">
                <p className="text-neutral-600 mb-4">You don't have any active insurance coverage yet.</p>
                <Button 
                  className="w-full sm:w-auto"
                  onClick={() => setLocation('/explore')}
                >
                  Explore Plans
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Claims */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-neutral-800">Recent Claims</h3>
            {claims.length > 2 && (
              <Button 
                variant="link" 
                className="text-secondary text-sm font-semibold"
                onClick={() => setLocation('/claim')}
              >
                View All
              </Button>
            )}
          </div>
          
          {claims.length > 0 ? (
            claims.slice(0, 2).map((claim) => (
              <Card key={claim.id} className="bg-white rounded-xl shadow-sm p-4 mb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-start">
                    <div className="w-10 h-10 rounded-full bg-warning bg-opacity-10 flex items-center justify-center mr-3">
                      {claim.claimType === 'dental' ? (
                        <Stethoscope className="h-5 w-5 text-warning" />
                      ) : (
                        <Pill className="h-5 w-5 text-warning" />
                      )}
                    </div>
                    <div>
                      <h4 className="font-semibold text-neutral-800">{claim.description}</h4>
                      <p className="text-neutral-500 text-sm">Claim #{claim.id}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`
                      bg-opacity-10 text-xs font-semibold px-2 py-1 rounded-full
                      ${claim.status === 'approved' ? 'bg-success text-success' : ''}
                      ${claim.status === 'in_review' ? 'bg-warning text-warning' : ''}
                      ${claim.status === 'rejected' ? 'bg-destructive text-destructive' : ''}
                      ${claim.status === 'submitted' ? 'bg-secondary text-secondary' : ''}
                    `}>
                      {claim.status === 'in_review' ? 'In Review' : 
                       claim.status === 'approved' ? 'Approved' :
                       claim.status === 'rejected' ? 'Rejected' : 'Submitted'}
                    </span>
                    <p className="text-neutral-500 text-sm mt-1">
                      {claim.status === 'approved' 
                        ? `Payment: ${formatCurrency(claim.amount)}` 
                        : `Submitted: ${formatDate(claim.submissionDate)}`}
                    </p>
                  </div>
                </div>
              </Card>
            ))
          ) : (
            <Card className="bg-white rounded-xl shadow-sm p-4">
              <div className="text-center py-4">
                <p className="text-neutral-600 mb-2">No claims yet</p>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setLocation('/claim')}
                >
                  File a Claim
                </Button>
              </div>
            </Card>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mb-6">
          <h3 className="font-bold text-lg text-neutral-800 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Button 
              variant="outline" 
              className="bg-white rounded-xl shadow-sm p-4 flex flex-col items-center justify-center h-24"
              onClick={() => setLocation('/claim')}
            >
              <PlusCircle className="h-6 w-6 text-primary mb-2" />
              <span className="text-neutral-800 text-sm font-semibold">New Claim</span>
            </Button>
            <Button 
              variant="outline" 
              className="bg-white rounded-xl shadow-sm p-4 flex flex-col items-center justify-center h-24"
              onClick={() => setLocation('/payment')}
            >
              <Wallet className="h-6 w-6 text-primary mb-2" />
              <span className="text-neutral-800 text-sm font-semibold">Make Payment</span>
            </Button>
            <Button 
              variant="outline" 
              className="bg-white rounded-xl shadow-sm p-4 flex flex-col items-center justify-center h-24"
              onClick={() => setLocation('/chama')}
            >
              <Users className="h-6 w-6 text-primary mb-2" />
              <span className="text-neutral-800 text-sm font-semibold">My Chama</span>
            </Button>
            <Button 
              variant="outline" 
              className="bg-white rounded-xl shadow-sm p-4 flex flex-col items-center justify-center h-24"
            >
              <HelpCircle className="h-6 w-6 text-primary mb-2" />
              <span className="text-neutral-800 text-sm font-semibold">Get Help</span>
            </Button>
          </div>
        </div>
      </main>
      <BottomNavigation />
    </div>
  );
}
