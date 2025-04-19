import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { 
  InsurancePlan, 
  UserInsurance, 
  Claim,
  Group,
  GroupInsurance,
  Payment 
} from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { useUser } from "./user-context";

interface InsuranceContextType {
  plans: InsurancePlan[];
  userInsurance: UserInsurance | null;
  claims: Claim[];
  payments: Payment[];
  group: Group | null;
  groupInsurance: GroupInsurance | null;
  loadingPlans: boolean;
  loadingUserData: boolean;
  purchaseInsurance: (planId: number, paymentFrequency: string) => Promise<void>;
  fileClaim: (claimData: Partial<Claim>) => Promise<void>;
  makePayment: (amount: number, paymentMethod: string) => Promise<void>;
}

const InsuranceContext = createContext<InsuranceContextType | undefined>(undefined);

export function InsuranceProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();
  const { toast } = useToast();
  const [userInsurance, setUserInsurance] = useState<UserInsurance | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [group, setGroup] = useState<Group | null>(null);
  const [groupInsurance, setGroupInsurance] = useState<GroupInsurance | null>(null);

  // Fetch insurance plans
  const { data: plans = [], isLoading: loadingPlans } = useQuery({
    queryKey: ["/api/insurance-plans"],
    queryFn: async () => {
      try {
        const response = await fetch("/api/insurance-plans", { credentials: "include" });
        if (!response.ok) {
          throw new Error(`${response.status}: ${response.statusText}`);
        }
        return await response.json();
      } catch (error) {
        console.error("Failed to fetch insurance plans:", error);
        
        // Return mock data for demonstration
        return [
          {
            id: 1,
            name: "Dental-Only Cover",
            description: "Basic dental care including checkups, cleanings, and minor procedures.",
            coverageAmount: 10000,
            dailyPremium: 20,
            weeklyPremium: 140,
            monthlyPremium: 600,
            benefits: [
              "Dental checkups & cleanings",
              "Basic dental procedures",
              "Up to KSh 10,000 annual coverage"
            ],
            planType: "individual",
            isPopular: false,
            tag: "Most Affordable"
          },
          {
            id: 2,
            name: "Health + Dental Combo",
            description: "Comprehensive coverage for both medical and dental needs.",
            coverageAmount: 25000,
            dailyPremium: 40,
            weeklyPremium: 280,
            monthlyPremium: 1200,
            benefits: [
              "All dental benefits",
              "Outpatient care & consultations",
              "Prescription medications",
              "Up to KSh 25,000 annual coverage"
            ],
            planType: "individual",
            isPopular: true,
            tag: null
          },
          {
            id: 3,
            name: "Family Cover",
            description: "Complete health protection for you and up to 4 dependents.",
            coverageAmount: 50000,
            dailyPremium: 100,
            weeklyPremium: 700,
            monthlyPremium: 3000,
            benefits: [
              "All combo benefits for the entire family",
              "Maternity benefits",
              "Children's vaccinations",
              "Up to KSh 50,000 annual coverage"
            ],
            planType: "family",
            isPopular: false,
            tag: null
          }
        ];
      }
    },
  });

  // Loading state for user data
  const [loadingUserData, setLoadingUserData] = useState(false);

  // Fetch user insurance data when user changes
  useEffect(() => {
    if (!user) {
      setUserInsurance(null);
      setClaims([]);
      setPayments([]);
      setGroup(null);
      setGroupInsurance(null);
      return;
    }

    const fetchUserData = async () => {
      setLoadingUserData(true);
      try {
        // In a real app, we would fetch from the API
        // const userInsuranceRes = await fetch(`/api/users/${user.id}/insurance`);
        // const userInsuranceData = await userInsuranceRes.json();
        // setUserInsurance(userInsuranceData.length > 0 ? userInsuranceData[0] : null);
        
        // For now, let's set mock data
        setUserInsurance({
          id: 1,
          userId: user.id,
          planId: 2,
          status: "active",
          startDate: new Date(),
          endDate: new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
          paymentFrequency: "weekly",
          nextPaymentDate: new Date(new Date().setDate(new Date().getDate() + 7)),
          nextPaymentAmount: 280
        });

        // Mock claims data
        setClaims([
          {
            id: 1,
            userId: user.id,
            userInsuranceId: 1,
            claimType: "dental",
            serviceDate: new Date(new Date().setDate(new Date().getDate() - 5)),
            providerName: "Nairobi Dental Clinic",
            amount: 1200,
            description: "Dental Checkup",
            status: "in_review",
            documentUrls: [],
            submissionDate: new Date(new Date().setDate(new Date().getDate() - 3)),
            approvalDate: undefined,
            rejectionReason: undefined
          },
          {
            id: 2,
            userId: user.id,
            userInsuranceId: 1,
            claimType: "medication",
            serviceDate: new Date(new Date().setDate(new Date().getDate() - 10)),
            providerName: "City Pharmacy",
            amount: 1200,
            description: "Prescription Medication",
            status: "approved",
            documentUrls: [],
            submissionDate: new Date(new Date().setDate(new Date().getDate() - 8)),
            approvalDate: new Date(new Date().setDate(new Date().getDate() - 2)),
            rejectionReason: undefined
          }
        ]);

        // Mock payments data
        setPayments([
          {
            id: 1,
            userId: user.id,
            userInsuranceId: 1,
            amount: 280,
            paymentMethod: "mpesa",
            status: "completed",
            transactionReference: "TR123456789",
            paymentDate: new Date(new Date().setDate(new Date().getDate() - 7))
          }
        ]);

        // Mock group data
        setGroup({
          id: 1,
          name: "Umoja Group",
          description: "Community health support group",
          createdAt: new Date(new Date().setMonth(new Date().getMonth() - 3)),
          adminUserId: user.id
        });

        // Mock group insurance data
        setGroupInsurance({
          id: 1,
          groupId: 1,
          planId: 3,
          status: "active",
          startDate: new Date(new Date().setMonth(new Date().getMonth() - 3)),
          endDate: new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
          monthlyPremium: 4800,
          nextPaymentDate: new Date(new Date().setDate(new Date().getDate() + 10)),
          collectedAmount: 3600,
          requiredAmount: 4800
        });
      } catch (error) {
        console.error("Error fetching user data:", error);
        toast({
          title: "Error",
          description: "Failed to load your insurance data",
          variant: "destructive",
        });
      } finally {
        setLoadingUserData(false);
      }
    };

    fetchUserData();
  }, [user, toast]);

  // Purchase insurance
  const purchaseInsurance = async (planId: number, paymentFrequency: string) => {
    if (!user) {
      toast({
        title: "Error",
        description: "You must be logged in to purchase insurance",
        variant: "destructive",
      });
      return;
    }

    try {
      // In a real app, we would make an API request
      /*
      const insuranceData = {
        userId: user.id,
        planId,
        status: "active",
        startDate: new Date(),
        paymentFrequency,
      };
      const response = await apiRequest("POST", "/api/user-insurance", insuranceData);
      const newInsurance = await response.json();
      setUserInsurance(newInsurance);
      */

      // For now, let's just update the state with mock data
      const selectedPlan = plans.find(p => p.id === planId);
      if (!selectedPlan) {
        throw new Error("Selected plan not found");
      }

      const nextPaymentDate = new Date();
      let nextPaymentAmount;

      switch (paymentFrequency) {
        case "daily":
          nextPaymentDate.setDate(nextPaymentDate.getDate() + 1);
          nextPaymentAmount = selectedPlan.dailyPremium;
          break;
        case "weekly":
          nextPaymentDate.setDate(nextPaymentDate.getDate() + 7);
          nextPaymentAmount = selectedPlan.weeklyPremium;
          break;
        case "monthly":
          nextPaymentDate.setMonth(nextPaymentDate.getMonth() + 1);
          nextPaymentAmount = selectedPlan.monthlyPremium;
          break;
        default:
          nextPaymentAmount = selectedPlan.monthlyPremium;
      }

      const newInsurance: UserInsurance = {
        id: Date.now(),
        userId: user.id,
        planId,
        status: "active",
        startDate: new Date(),
        endDate: new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
        paymentFrequency,
        nextPaymentDate,
        nextPaymentAmount
      };

      setUserInsurance(newInsurance);
      toast({
        title: "Success",
        description: `You've successfully purchased the ${selectedPlan.name} plan!`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to purchase insurance",
        variant: "destructive",
      });
      throw error;
    }
  };

  // File a claim
  const fileClaim = async (claimData: Partial<Claim>) => {
    if (!user || !userInsurance) {
      toast({
        title: "Error",
        description: "You must be logged in and have an active insurance to file a claim",
        variant: "destructive",
      });
      return;
    }

    try {
      // In a real app, we would make an API request
      /*
      const fullClaimData = {
        ...claimData,
        userId: user.id,
        userInsuranceId: userInsurance.id,
        status: "submitted"
      };
      const response = await apiRequest("POST", "/api/claims", fullClaimData);
      const newClaim = await response.json();
      setClaims(prevClaims => [...prevClaims, newClaim]);
      */

      // For now, let's just update the state with mock data
      const newClaim: Claim = {
        id: Date.now(),
        userId: user.id,
        userInsuranceId: userInsurance.id,
        claimType: claimData.claimType || "other",
        serviceDate: claimData.serviceDate || new Date(),
        providerName: claimData.providerName || "",
        amount: claimData.amount || 0,
        description: claimData.description || "",
        status: "submitted",
        documentUrls: claimData.documentUrls || [],
        submissionDate: new Date(),
        approvalDate: undefined,
        rejectionReason: undefined
      };

      setClaims(prevClaims => [...prevClaims, newClaim]);
      toast({
        title: "Claim Submitted",
        description: "Your claim has been submitted successfully and is under review.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to submit claim",
        variant: "destructive",
      });
      throw error;
    }
  };

  // Make a payment
  const makePayment = async (amount: number, paymentMethod: string) => {
    if (!user || !userInsurance) {
      toast({
        title: "Error",
        description: "You must be logged in and have an active insurance to make a payment",
        variant: "destructive",
      });
      return;
    }

    try {
      // In a real app, we would make an API request
      /*
      const paymentData = {
        userId: user.id,
        userInsuranceId: userInsurance.id,
        amount,
        paymentMethod,
        status: "pending"
      };
      const response = await apiRequest("POST", "/api/payments", paymentData);
      const newPayment = await response.json();
      setPayments(prevPayments => [...prevPayments, newPayment]);
      */

      // For now, let's just update the state with mock data
      const transactionReference = `TR${Date.now()}`;
      const newPayment: Payment = {
        id: Date.now(),
        userId: user.id,
        userInsuranceId: userInsurance.id,
        amount,
        paymentMethod,
        status: "completed", // In a real app, this would initially be 'pending'
        transactionReference,
        paymentDate: new Date()
      };

      setPayments(prevPayments => [...prevPayments, newPayment]);

      // Update the next payment date based on payment frequency
      const plan = plans.find(p => p.id === userInsurance.planId);
      if (plan) {
        const nextPaymentDate = new Date();
        let nextPaymentAmount;

        switch (userInsurance.paymentFrequency) {
          case "daily":
            nextPaymentDate.setDate(nextPaymentDate.getDate() + 1);
            nextPaymentAmount = plan.dailyPremium;
            break;
          case "weekly":
            nextPaymentDate.setDate(nextPaymentDate.getDate() + 7);
            nextPaymentAmount = plan.weeklyPremium;
            break;
          case "monthly":
            nextPaymentDate.setMonth(nextPaymentDate.getMonth() + 1);
            nextPaymentAmount = plan.monthlyPremium;
            break;
        }

        setUserInsurance({
          ...userInsurance,
          nextPaymentDate,
          nextPaymentAmount
        });
      }

      toast({
        title: "Payment Successful",
        description: `Your payment of KSh ${amount} has been processed successfully.`,
      });
    } catch (error) {
      toast({
        title: "Payment Failed",
        description: error instanceof Error ? error.message : "Failed to process payment",
        variant: "destructive",
      });
      throw error;
    }
  };

  return (
    <InsuranceContext.Provider
      value={{
        plans,
        userInsurance,
        claims,
        payments,
        group,
        groupInsurance,
        loadingPlans,
        loadingUserData,
        purchaseInsurance,
        fileClaim,
        makePayment
      }}
    >
      {children}
    </InsuranceContext.Provider>
  );
}

export function useInsurance() {
  const context = useContext(InsuranceContext);
  if (context === undefined) {
    throw new Error("useInsurance must be used within an InsuranceProvider");
  }
  return context;
}
