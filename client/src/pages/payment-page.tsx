import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { Header } from "@/components/layout/header";
import { BottomNavigation } from "@/components/layout/bottom-navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useInsurance } from "@/context/insurance-context";
import { useUser } from "@/context/user-context";
import { useToast } from "@/hooks/use-toast";
import { format, addDays, addWeeks, addMonths, addYears } from "date-fns";
import { apiRequest } from "@/lib/queryClient";
import { Loader2, Smartphone, Users, CreditCard } from "lucide-react";

export default function PaymentPage() {
  const { userInsurance, plans, makePayment, loadingUserData } = useInsurance();
  const { user } = useUser();
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const [selectedPaymentFrequency, setSelectedPaymentFrequency] = useState<'daily' | 'weekly' | 'monthly' | 'yearly'>('monthly');
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<'mpesa' | 'chama' | 'bank'>('mpesa');
  const [phoneNumber, setPhoneNumber] = useState(user?.phoneNumber || "");
  const [stkResult, setStkResult] = useState<{
    success: boolean;
    message: string;
    paymentId?: number;
    checkoutRequestId?: string;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Find the plan associated with user's insurance
  const userPlan = userInsurance && plans.find(p => p.id === userInsurance.planId);

  // Calculate premium based on selected frequency
  const getPremiumAmount = () => {
    if (!userPlan) return 0;
    
    switch (selectedPaymentFrequency) {
      case 'daily':
        return userPlan.dailyPremium;
      case 'weekly':
        return userPlan.weeklyPremium;
      case 'monthly':
        return userPlan.monthlyPremium;
      case 'yearly':
        return userPlan.yearlyPremium;
      default:
        return userPlan.dailyPremium;
    }
  };

  // Calculate next coverage date based on selected frequency
  const getNextCoverageDate = () => {
    const today = new Date();
    
    switch (selectedPaymentFrequency) {
      case 'daily':
        return format(addDays(today, 1), 'dd MMM yyyy');
      case 'weekly':
        return format(addWeeks(today, 1), 'dd MMM yyyy');
      case 'monthly':
        return format(addMonths(today, 1), 'dd MMM yyyy');
      case 'yearly':
        return format(addYears(today, 1), 'dd MMM yyyy');
      default:
        return format(addDays(today, 1), 'dd MMM yyyy');
    }
  };

  const handleMpesaPayment = async () => {
    if (!phoneNumber || phoneNumber.length < 10) {
      toast({
        title: "Invalid Phone Number",
        description: "Please enter a valid Kenyan phone number",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsProcessing(true);
      const amount = getPremiumAmount();
      
      // Format phone number (ensure it has the correct format)
      let formattedPhone = phoneNumber.replace(/\D/g, ''); // Remove non-digit characters
      
      // Handle local format (starting with 0)
      if (formattedPhone.startsWith('0')) {
        formattedPhone = formattedPhone.substring(1); // Remove leading zero
      }
      
      // Remove country code if it's too long
      if (formattedPhone.startsWith('254') && formattedPhone.length > 12) {
        formattedPhone = formattedPhone.substring(3);
      }
      
      // Ensure the number has at most 12 digits as required by the API
      if (formattedPhone.length > 12) {
        formattedPhone = formattedPhone.substring(0, 12);
      }
      
      // Verify user and insurance data again
      if (!user || !userInsurance) {
        toast({
          title: "Error",
          description: "Missing user or insurance data. Please try again.",
          variant: "destructive",
        });
        return;
      }
      
      // Call the M-Pesa STK push API
      const response = await apiRequest("POST", "/api/mpesa/stk-push", {
        phoneNumber: formattedPhone,
        amount,
        userId: user.id,
        userInsuranceId: userInsurance.id,
        accountReference: `Insurance-${userInsurance.id}`,
        transactionDesc: `Premium payment for ${user.fullName || 'BimaBora customer'}`,
      });
      
      const result = await response.json();
      setStkResult(result);
      
      if (result.success) {
        toast({
          title: "M-Pesa Request Sent",
          description: "Please check your phone to complete the payment",
        });
      } else {
        toast({
          title: "M-Pesa Request Failed",
          description: result.message || "Failed to initiate payment",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("M-Pesa payment error:", error);
      toast({
        title: "Payment Failed",
        description: "There was an error processing your payment. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleChamaPayment = async () => {
    try {
      setIsProcessing(true);
      const amount = getPremiumAmount();
      await makePayment(amount, 'chama');
      
      toast({
        title: "Payment Request Sent",
        description: "Your payment request has been sent to your Chama/SACCO administrator",
      });
    } catch (error) {
      console.error("Chama payment error:", error);
      toast({
        title: "Payment Failed",
        description: "There was an error processing your payment. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleBankPayment = async () => {
    try {
      setIsProcessing(true);
      const amount = getPremiumAmount();
      await makePayment(amount, 'bank');
      
      toast({
        title: "Payment Successful",
        description: `Your payment of KSh ${amount} has been processed. Your coverage is active until ${getNextCoverageDate()}.`,
      });
      
      // Redirect to home page
      setLocation('/');
    } catch (error) {
      console.error("Bank payment error:", error);
      toast({
        title: "Payment Failed",
        description: "There was an error processing your payment. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleMakePayment = async () => {
    if (!user || !userInsurance) {
      toast({
        title: "Error",
        description: "You need to be logged in and have active insurance to make payments",
        variant: "destructive",
      });
      return;
    }

    switch (selectedPaymentMethod) {
      case 'mpesa':
        await handleMpesaPayment();
        break;
      case 'chama':
        await handleChamaPayment();
        break;
      case 'bank':
        await handleBankPayment();
        break;
      default:
        await handleMpesaPayment();
    }
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

  if (!userInsurance || !userPlan) {
    return (
      <div className="min-h-screen bg-neutral-100">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-5 pb-24">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-neutral-800 mb-1">Make a Payment</h2>
            <p className="text-neutral-600">Choose your preferred payment method and frequency.</p>
          </div>
          
          <Card className="bg-white rounded-xl shadow-sm mb-6">
            <CardContent className="p-8 text-center">
              <p className="text-neutral-700 mb-4">You don't have any active insurance plan.</p>
              <Button onClick={() => setLocation('/explore')}>
                Explore Insurance Plans
              </Button>
            </CardContent>
          </Card>
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
          <h2 className="text-2xl font-bold text-neutral-800 mb-1">Make a Payment</h2>
          <p className="text-neutral-600">Choose your preferred payment method and frequency.</p>
        </div>

        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            <div className="mb-5">
              <p className="text-neutral-700 font-semibold mb-2">Current Plan</p>
              <div className="flex items-center justify-between bg-neutral-100 p-3 rounded-lg">
                <div>
                  <h4 className="font-bold text-neutral-800">{userPlan.name}</h4>
                  <p className="text-sm text-neutral-600">Coverage: KSh {userPlan.coverageAmount.toLocaleString()}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-neutral-800">
                    KSh {userPlan.dailyPremium} <span className="text-xs font-normal">/ day</span>
                  </p>
                  <p className="text-sm text-neutral-600">
                    KSh {userPlan.weeklyPremium} <span className="text-xs font-normal">/ week</span>
                  </p>
                </div>
              </div>
            </div>

            <div className="mb-5">
              <p className="text-neutral-700 font-semibold mb-2">Payment Frequency</p>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <button 
                  className={`p-3 ${selectedPaymentFrequency === 'daily' 
                    ? 'border-2 border-primary bg-primary bg-opacity-5' 
                    : 'border border-neutral-300'} 
                    rounded-lg text-center`}
                  onClick={() => setSelectedPaymentFrequency('daily')}
                >
                  <p className={`font-bold ${selectedPaymentFrequency === 'daily' ? 'text-primary' : 'text-neutral-700'}`}>Daily</p>
                  <p className="text-xs text-neutral-600">KSh {userPlan.dailyPremium}</p>
                </button>
                <button 
                  className={`p-3 ${selectedPaymentFrequency === 'weekly' 
                    ? 'border-2 border-primary bg-primary bg-opacity-5' 
                    : 'border border-neutral-300'} 
                    rounded-lg text-center`}
                  onClick={() => setSelectedPaymentFrequency('weekly')}
                >
                  <p className={`font-bold ${selectedPaymentFrequency === 'weekly' ? 'text-primary' : 'text-neutral-700'}`}>Weekly</p>
                  <p className="text-xs text-neutral-600">KSh {userPlan.weeklyPremium}</p>
                </button>
                <button 
                  className={`p-3 ${selectedPaymentFrequency === 'monthly' 
                    ? 'border-2 border-primary bg-primary bg-opacity-5' 
                    : 'border border-neutral-300'} 
                    rounded-lg text-center`}
                  onClick={() => setSelectedPaymentFrequency('monthly')}
                >
                  <p className={`font-bold ${selectedPaymentFrequency === 'monthly' ? 'text-primary' : 'text-neutral-700'}`}>Monthly</p>
                  <p className="text-xs text-neutral-600">KSh {userPlan.monthlyPremium}</p>
                </button>
                <button 
                  className={`p-3 ${selectedPaymentFrequency === 'yearly' 
                    ? 'border-2 border-primary bg-primary bg-opacity-5' 
                    : 'border border-neutral-300'} 
                    rounded-lg text-center`}
                  onClick={() => setSelectedPaymentFrequency('yearly')}
                >
                  <p className={`font-bold ${selectedPaymentFrequency === 'yearly' ? 'text-primary' : 'text-neutral-700'}`}>Yearly</p>
                  <p className="text-xs text-neutral-600">KSh {userPlan.yearlyPremium}</p>
                  <p className="text-[10px] text-green-600 font-medium">Save up to 15%</p>
                </button>
              </div>
            </div>

            <div className="mb-5">
              <p className="text-neutral-700 font-semibold mb-2">Payment Method</p>
              <div className="space-y-3">
                <div 
                  className={`border ${selectedPaymentMethod === 'mpesa' ? 'border-primary' : 'border-neutral-300'} rounded-lg p-3 flex items-center cursor-pointer`}
                  onClick={() => setSelectedPaymentMethod('mpesa')}
                >
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
                    checked={selectedPaymentMethod === 'mpesa'} 
                    onChange={() => setSelectedPaymentMethod('mpesa')} 
                    className="w-5 h-5 text-primary"
                  />
                </div>

                <div 
                  className={`border ${selectedPaymentMethod === 'chama' ? 'border-primary' : 'border-neutral-300'} rounded-lg p-3 flex items-center cursor-pointer`}
                  onClick={() => setSelectedPaymentMethod('chama')}
                >
                  <div className="w-10 h-10 rounded-full bg-neutral-100 flex items-center justify-center mr-3">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" fill="#1F97E5"/>
                    </svg>
                  </div>
                  <div className="flex-grow">
                    <p className="font-semibold text-neutral-800">Chama/SACCO</p>
                    <p className="text-sm text-neutral-600">Pay through your group</p>
                  </div>
                  <input 
                    type="radio" 
                    checked={selectedPaymentMethod === 'chama'} 
                    onChange={() => setSelectedPaymentMethod('chama')} 
                    className="w-5 h-5 text-primary"
                  />
                </div>

                <div 
                  className={`border ${selectedPaymentMethod === 'bank' ? 'border-primary' : 'border-neutral-300'} rounded-lg p-3 flex items-center cursor-pointer`}
                  onClick={() => setSelectedPaymentMethod('bank')}
                >
                  <div className="w-10 h-10 rounded-full bg-neutral-100 flex items-center justify-center mr-3">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 10V17H7V10H4ZM10 10V17H13V10H10ZM2 22H21V19H2V22ZM16 10V17H19V10H16ZM11.5 1L2 6V8H21V6L11.5 1Z" fill="#6C757D"/>
                    </svg>
                  </div>
                  <div className="flex-grow">
                    <p className="font-semibold text-neutral-800">Bank Transfer</p>
                    <p className="text-sm text-neutral-600">Pay from your bank account</p>
                  </div>
                  <input 
                    type="radio" 
                    checked={selectedPaymentMethod === 'bank'} 
                    onChange={() => setSelectedPaymentMethod('bank')} 
                    className="w-5 h-5 text-primary"
                  />
                </div>
              </div>
            </div>

            {selectedPaymentMethod === 'mpesa' && (
              <div className="mb-5">
                <p className="text-neutral-700 font-semibold mb-2">M-Pesa Phone Number</p>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                    <Smartphone className="h-5 w-5 text-neutral-500" />
                  </div>
                  <Input
                    type="tel"
                    placeholder="e.g. 0712345678"
                    className="pl-10"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                  />
                </div>
                <p className="text-xs text-neutral-500 mt-1">
                  Enter your M-Pesa phone number starting with 07 (e.g. 0712345678)
                </p>
              </div>
            )}

            {stkResult && (
              <div className={`mb-5 p-3 rounded-lg ${stkResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <p className={`font-medium ${stkResult.success ? 'text-green-700' : 'text-red-700'}`}>
                  {stkResult.success ? 'M-Pesa Request Sent' : 'M-Pesa Request Failed'}
                </p>
                <p className="text-sm mt-1">
                  {stkResult.message}
                </p>
              </div>
            )}

            <div className="mb-5 pt-3 border-t border-neutral-200">
              <div className="flex justify-between mb-2">
                <p className="text-neutral-600">Premium Amount</p>
                <p className="font-semibold text-neutral-800">KSh {getPremiumAmount().toFixed(2)}</p>
              </div>
              <div className="flex justify-between mb-3">
                <p className="text-neutral-600">Transaction Fee</p>
                <p className="font-semibold text-neutral-800">KSh 0.00</p>
              </div>
              <div className="flex justify-between font-bold">
                <p className="text-neutral-800">Total Payment</p>
                <p className="text-primary text-lg">KSh {getPremiumAmount().toFixed(2)}</p>
              </div>
            </div>

            <Button 
              className="w-full py-3" 
              onClick={handleMakePayment}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>Pay Now</>
              )}
            </Button>
            <p className="text-center text-xs text-neutral-500 mt-3">
              Your coverage will be active immediately after payment
            </p>
          </CardContent>
        </Card>
      </main>
      <BottomNavigation />
    </div>
  );
}
