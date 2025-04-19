import { useState } from "react";
import { useLocation } from "wouter";
import { Header } from "@/components/layout/header";
import { BottomNavigation } from "@/components/layout/bottom-navigation";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";
import { useInsurance } from "@/context/insurance-context";
import { useUser } from "@/context/user-context";
import { useToast } from "@/hooks/use-toast";

export default function ExplorePage() {
  const { plans, loadingPlans, purchaseInsurance } = useInsurance();
  const { user } = useUser();
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const [activeTab, setActiveTab] = useState<string>("individual");

  const handleSelectPlan = async (planId: number) => {
    if (!user) {
      toast({
        title: "Login Required",
        description: "Please log in to select a plan",
        variant: "destructive",
      });
      return;
    }

    try {
      await purchaseInsurance(planId, "daily");
      setLocation("/payment");
    } catch (error) {
      console.error("Error selecting plan:", error);
    }
  };

  if (loadingPlans) {
    return (
      <div className="min-h-screen bg-neutral-100">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-5 pb-24">
          <div className="mb-6 h-6 w-40 bg-neutral-200 animate-pulse rounded"></div>
          <div className="flex border-b border-neutral-200 mb-4">
            {["Individual Plans", "Family Plans", "Group Plans"].map((tab, i) => (
              <div key={i} className="flex-1 py-3 text-center">
                <div className="h-6 bg-neutral-200 animate-pulse rounded mx-auto w-24"></div>
              </div>
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm p-4 h-64 animate-pulse"></div>
            ))}
          </div>
        </main>
        <BottomNavigation />
      </div>
    );
  }

  const filteredPlans = plans.filter(plan => plan.planType === activeTab);

  return (
    <div className="min-h-screen bg-neutral-100">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-5 pb-24">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-neutral-800 mb-1">Explore Coverage</h2>
          <p className="text-neutral-600">Find the perfect protection plan for you and your family.</p>
        </div>

        {/* Plan Tabs */}
        <div className="flex border-b border-neutral-200 mb-4">
          <button 
            className={`flex-1 py-3 text-center font-semibold ${activeTab === 'individual' ? 'text-primary border-b-2 border-primary' : 'text-neutral-500'}`}
            onClick={() => setActiveTab('individual')}
          >
            Individual Plans
          </button>
          <button 
            className={`flex-1 py-3 text-center font-semibold ${activeTab === 'family' ? 'text-primary border-b-2 border-primary' : 'text-neutral-500'}`}
            onClick={() => setActiveTab('family')}
          >
            Family Plans
          </button>
          <button 
            className={`flex-1 py-3 text-center font-semibold ${activeTab === 'group' ? 'text-primary border-b-2 border-primary' : 'text-neutral-500'}`}
            onClick={() => setActiveTab('group')}
          >
            Group Plans
          </button>
        </div>

        {/* Plan Cards */}
        <div className="space-y-4">
          {filteredPlans.length > 0 ? (
            filteredPlans.map(plan => (
              <div 
                key={plan.id} 
                className={`bg-white rounded-xl shadow-sm overflow-hidden ${plan.isPopular ? 'border-2 border-primary' : ''}`}
              >
                {plan.isPopular && (
                  <div className="bg-primary text-white text-center py-1 text-sm font-semibold">
                    MOST POPULAR
                  </div>
                )}
                <div className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-lg text-neutral-800">{plan.name}</h3>
                    {plan.tag && (
                      <span className="bg-primary bg-opacity-10 text-primary text-xs font-semibold px-2 py-1 rounded-full">
                        {plan.tag}
                      </span>
                    )}
                  </div>
                  <p className="text-neutral-600 text-sm mb-3">{plan.description}</p>
                  <div className="flex items-baseline mb-3">
                    <span className="text-2xl font-bold text-neutral-800">KSh {plan.dailyPremium}</span>
                    <span className="text-neutral-500 text-sm ml-1">/ day</span>
                  </div>
                  <ul className="space-y-2 mb-4">
                    {plan.benefits?.map((benefit, idx) => (
                      <li key={idx} className="flex items-start">
                        <Check className="h-4 w-4 text-success mr-2 mt-0.5" />
                        <span className="text-neutral-700 text-sm">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className="w-full py-2.5"
                    onClick={() => handleSelectPlan(plan.id)}
                  >
                    Select Plan
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-6 text-center">
              <p className="text-neutral-600 mb-4">No plans available for this category yet.</p>
              <Button onClick={() => setActiveTab('individual')}>
                View Individual Plans
              </Button>
            </div>
          )}
        </div>
      </main>
      <BottomNavigation />
    </div>
  );
}
