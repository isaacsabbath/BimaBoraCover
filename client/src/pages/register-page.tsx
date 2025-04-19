import { useForm } from "react-hook-form";
import { useUser } from "@/context/user-context";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";

export default function RegisterPage() {
  const { register } = useUser();
  const [, setLocation] = useLocation();
  const form = useForm({
    defaultValues: {
      fullName: "",
      phoneNumber: "",
      pin: "",
    },
  });

  const onSubmit = async (data: {
    fullName: string;
    phoneNumber: string;
    pin: string;
  }) => {
    try {
      await register({
        ...data,
        username: data.phoneNumber, // Use phone number as username
        password: data.pin,
      });
      setLocation("/");
    } catch (error) {
      // Error is handled by the UserContext
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md hover:shadow-lg transition-shadow duration-200">
        <CardContent className="p-6">
          <h1 className="text-2xl font-bold text-neutral-800 mb-6">Create an Account</h1>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="fullName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your full name" {...field} className="hover:border-primary focus:border-primary" />
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
                    <FormLabel>Phone Number</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your phone number" {...field} className="hover:border-primary focus:border-primary" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="pin"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>PIN</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="Create a PIN" maxLength={4} {...field} className="hover:border-primary focus:border-primary" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full hover:bg-primary-dark transition-colors">
                Register
              </Button>
              <p className="text-center text-sm text-neutral-600">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => setLocation("/login")}
                  className="text-primary hover:underline"
                >
                  Login
                </button>
              </p>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}