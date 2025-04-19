import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import HomePage from "@/pages/home-page";
import ExplorePage from "@/pages/explore-page";
import ClaimPage from "@/pages/claim-page";
import PaymentPage from "@/pages/payment-page";
import ChamaPage from "@/pages/chama-page";
import ProfilePage from "@/pages/profile-page";
import LoginPage from "@/pages/login-page";
import RegisterPage from "@/pages/register-page";
import { UserProvider } from "@/context/user-context";
import { InsuranceProvider } from "@/context/insurance-context";

function Router() {
  return (
    <Switch>
      <Route path="/" component={HomePage} />
      <Route path="/explore" component={ExplorePage} />
      <Route path="/claim" component={ClaimPage} />
      <Route path="/payment" component={PaymentPage} />
      <Route path="/chama" component={ChamaPage} />
      <Route path="/profile" component={ProfilePage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/register" component={RegisterPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <UserProvider>
          <InsuranceProvider>
            <Toaster />
            <Router />
          </InsuranceProvider>
        </UserProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
