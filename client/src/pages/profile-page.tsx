import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Header } from "@/components/layout/header";
import { BottomNavigation } from "@/components/layout/bottom-navigation";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { useUser } from "@/context/user-context";
import { useToast } from "@/hooks/use-toast";
import { Lock, Shield } from "lucide-react";
import { format } from "date-fns";

// Create schema for profile form validation
const profileFormSchema = z.object({
  fullName: z
    .string()
    .min(2, "Full name must be at least 2 characters"),
  email: z
    .string()
    .email("Invalid email address"),
  phoneNumber: z
    .string()
    .min(10, "Phone number must be at least 10 characters"),
  idNumber: z
    .string()
    .optional(),
  dateOfBirth: z
    .string()
    .optional(),
  address: z
    .string()
    .optional(),
});

type ProfileFormValues = z.infer<typeof profileFormSchema>;

export default function ProfilePage() {
  const { user, updateProfile, logout } = useUser();
  const { toast } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Notification preferences state
  const [notificationPrefs, setNotificationPrefs] = useState({
    paymentReminders: user?.notificationPreferences?.paymentReminders || true,
    claimUpdates: user?.notificationPreferences?.claimUpdates || true,
    newPlans: user?.notificationPreferences?.newPlans || true,
  });

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: {
      fullName: user?.fullName || "",
      email: user?.email || "",
      phoneNumber: user?.phoneNumber || "",
      idNumber: user?.idNumber || "",
      dateOfBirth: user?.dateOfBirth ? format(new Date(user.dateOfBirth), "yyyy-MM-dd") : "",
      address: user?.address || "",
    },
  });

  const onSubmit = async (data: ProfileFormValues) => {
    try {
      setIsSaving(true);
      
      await updateProfile({
        ...data,
        dateOfBirth: data.dateOfBirth ? new Date(data.dateOfBirth) : undefined,
        notificationPreferences: notificationPrefs,
      });
      
      toast({
        title: "Profile Updated",
        description: "Your profile has been updated successfully",
      });
    } catch (error) {
      console.error("Error updating profile:", error);
      toast({
        title: "Update Failed",
        description: "There was an error updating your profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleNotificationChange = (key: keyof typeof notificationPrefs) => {
    setNotificationPrefs(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleLogout = () => {
    logout();
    toast({
      title: "Logged Out",
      description: "You have been logged out successfully",
    });
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase();
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-neutral-100">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-5 pb-24">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-neutral-800 mb-1">My Profile</h2>
            <p className="text-neutral-600">Manage your personal information and preferences.</p>
          </div>
          
          <Card className="bg-white rounded-xl shadow-sm mb-6">
            <CardContent className="p-8 text-center">
              <p className="text-neutral-700 mb-4">Please log in to view your profile.</p>
              <Button>
                Log In
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
          <h2 className="text-2xl font-bold text-neutral-800 mb-1">My Profile</h2>
          <p className="text-neutral-600">Manage your personal information and preferences.</p>
        </div>

        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            <div className="flex flex-col items-center justify-center py-4 border-b border-neutral-200 mb-4">
              <div className="w-20 h-20 rounded-full bg-primary-light flex items-center justify-center text-primary text-2xl font-bold mb-3">
                {getInitials(user.fullName || "User")}
              </div>
              <h3 className="font-bold text-xl text-neutral-800">{user.fullName}</h3>
              <p className="text-neutral-600">{user.email}</p>
              <p className="text-neutral-600">{user.phoneNumber}</p>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
                <FormField
                  control={form.control}
                  name="fullName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="block text-neutral-700 font-semibold mb-2">Full Name</FormLabel>
                      <FormControl>
                        <Input 
                          className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                          {...field} 
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="block text-neutral-700 font-semibold mb-2">Email Address</FormLabel>
                      <FormControl>
                        <Input 
                          type="email"
                          className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                          {...field} 
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="phoneNumber"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="block text-neutral-700 font-semibold mb-2">Phone Number</FormLabel>
                      <FormControl>
                        <Input 
                          type="tel"
                          className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                          {...field} 
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="idNumber"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="block text-neutral-700 font-semibold mb-2">ID Number</FormLabel>
                      <FormControl>
                        <Input 
                          className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                          {...field} 
                          value={field.value || ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="dateOfBirth"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="block text-neutral-700 font-semibold mb-2">Date of Birth</FormLabel>
                      <FormControl>
                        <Input 
                          type="date"
                          className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                          {...field} 
                          value={field.value || ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="address"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="block text-neutral-700 font-semibold mb-2">Physical Address</FormLabel>
                      <FormControl>
                        <Textarea 
                          rows={2}
                          className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                          {...field} 
                          value={field.value || ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div>
                  <label className="block text-neutral-700 font-semibold mb-2">Notification Preferences</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input 
                        type="checkbox" 
                        checked={notificationPrefs.paymentReminders}
                        onChange={() => handleNotificationChange('paymentReminders')}
                        className="w-5 h-5 mr-3 text-primary border-neutral-300 rounded focus:ring-primary"
                      />
                      <span className="text-neutral-700">Payment reminders</span>
                    </label>
                    <label className="flex items-center">
                      <input 
                        type="checkbox" 
                        checked={notificationPrefs.claimUpdates}
                        onChange={() => handleNotificationChange('claimUpdates')}
                        className="w-5 h-5 mr-3 text-primary border-neutral-300 rounded focus:ring-primary"
                      />
                      <span className="text-neutral-700">Claim status updates</span>
                    </label>
                    <label className="flex items-center">
                      <input 
                        type="checkbox" 
                        checked={notificationPrefs.newPlans}
                        onChange={() => handleNotificationChange('newPlans')}
                        className="w-5 h-5 mr-3 text-primary border-neutral-300 rounded focus:ring-primary"
                      />
                      <span className="text-neutral-700">New plan offerings</span>
                    </label>
                  </div>
                </div>

                <Button 
                  className="w-full py-3"
                  type="submit"
                  disabled={isSaving}
                >
                  {isSaving ? "Saving Changes..." : "Save Changes"}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            <h3 className="font-bold text-lg text-neutral-800 mb-4">Account Security</h3>
            <div className="space-y-3">
              <Button 
                variant="outline"
                className="w-full py-2.5 border border-neutral-300 text-neutral-700 bg-white rounded-lg font-semibold flex justify-center items-center"
              >
                <Lock className="mr-2 h-4 w-4" />
                Change Password
              </Button>
              <Button 
                variant="outline"
                className="w-full py-2.5 border border-neutral-300 text-neutral-700 bg-white rounded-lg font-semibold flex justify-center items-center"
              >
                <Shield className="mr-2 h-4 w-4" />
                Two-Factor Authentication
              </Button>
              <Button 
                variant="outline"
                className="w-full py-2.5 border border-neutral-300 text-neutral-700 bg-white rounded-lg font-semibold flex justify-center items-center"
                onClick={handleLogout}
              >
                Logout
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            <h3 className="font-bold text-lg text-destructive mb-4">Danger Zone</h3>
            <Button 
              variant="outline"
              className="w-full py-2.5 border border-destructive text-destructive bg-white rounded-lg font-semibold"
              onClick={() => setShowDeleteConfirm(true)}
            >
              Delete Account
            </Button>
          </CardContent>
        </Card>
      </main>

      {/* Delete Account Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md rounded-xl">
            <CardContent className="p-6">
              <h3 className="text-xl font-bold text-destructive mb-4">Delete Your Account?</h3>
              <p className="text-neutral-600 mb-6">
                This action cannot be undone. All your data, including insurance coverage, claims, and payment history will be permanently deleted.
              </p>
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  className="flex-1"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    toast({
                      title: "Account Deletion Requested",
                      description: "Your request has been received. Our team will contact you to confirm.",
                    });
                  }}
                >
                  Delete Account
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
