import { createContext, ReactNode, useState, useContext, useEffect } from "react";
import { User } from "@shared/schema";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

// Mock user data for simulation
const mockUser: User = {
  id: 1,
  username: "johndoe",
  password: "password", // This would be hashed in a real app
  fullName: "John Doe",
  email: "johndoe@example.com",
  phoneNumber: "0712345678",
  idNumber: "12345678",
  dateOfBirth: new Date("1990-01-15"),
  address: "123 Moi Avenue, Nairobi",
  notificationPreferences: {
    paymentReminders: true,
    claimUpdates: true,
    newPlans: true
  },
  createdAt: new Date()
};

interface UserContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (userData: Partial<User>) => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    // Simulate fetching user data
    const fetchUser = async () => {
      try {
        // In a real app, we would fetch the user data from the API
        // const response = await apiRequest("GET", "/api/user");
        // const userData = await response.json();
        // setUser(userData);
        
        // For now, let's immediately set the mock user
        setUser(mockUser);
      } catch (error) {
        // If there's an error, the user is not logged in
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      // In a real app, we would authenticate the user
      // const response = await apiRequest("POST", "/api/login", { username, password });
      // const userData = await response.json();
      // setUser(userData);

      // For now, let's just set the mock user
      setUser(mockUser);
      toast({
        title: "Login successful",
        description: "Welcome back, John Doe!",
      });
    } catch (error) {
      toast({
        title: "Login failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: Partial<User>) => {
    setLoading(true);
    try {
      // In a real app, we would register the user
      // const response = await apiRequest("POST", "/api/register", userData);
      // const newUser = await response.json();
      // setUser(newUser);

      // For now, let's just set the mock user
      setUser(mockUser);
      toast({
        title: "Registration successful",
        description: "Your account has been created!",
      });
    } catch (error) {
      toast({
        title: "Registration failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (userData: Partial<User>) => {
    if (!user) return;
    setLoading(true);
    try {
      // In a real app, we would update the user profile
      // const response = await apiRequest("PATCH", `/api/users/${user.id}`, userData);
      // const updatedUser = await response.json();
      // setUser(updatedUser);

      // For now, let's just update the mock user
      setUser({ ...user, ...userData });
      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully!",
      });
    } catch (error) {
      toast({
        title: "Update failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // In a real app, we would logout the user
    // apiRequest("POST", "/api/logout");
    setUser(null);
    toast({
      title: "Logged out",
      description: "You have been logged out successfully.",
    });
    window.location.href = "/login";
  };

  return (
    <UserContext.Provider
      value={{
        user,
        login,
        register,
        updateProfile,
        logout,
        loading,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
