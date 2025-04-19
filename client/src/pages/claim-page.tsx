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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { useInsurance } from "@/context/insurance-context";
import { useUser } from "@/context/user-context";
import { useToast } from "@/hooks/use-toast";
import { Claim } from "@shared/schema";
import { Upload, ImagePlus, FileText } from "lucide-react";

// Create schema for claim form validation
const claimFormSchema = z.object({
  claimType: z.string({
    required_error: "Please select a claim type",
  }),
  serviceDate: z.string({
    required_error: "Please select the date of service",
  }),
  providerName: z
    .string({
      required_error: "Please enter the provider name",
    })
    .min(2, "Provider name must be at least 2 characters"),
  amount: z
    .string({
      required_error: "Please enter the claim amount",
    })
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: "Amount must be a positive number",
    }),
  description: z
    .string({
      required_error: "Please provide a description",
    })
    .min(10, "Description must be at least 10 characters"),
});

type ClaimFormValues = z.infer<typeof claimFormSchema>;

export default function ClaimPage() {
  const { fileClaim, userInsurance } = useInsurance();
  const { user } = useUser();
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<ClaimFormValues>({
    resolver: zodResolver(claimFormSchema),
    defaultValues: {
      claimType: "",
      serviceDate: new Date().toISOString().substring(0, 10),
      providerName: "",
      amount: "",
      description: "",
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const fileList = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...fileList]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const onSubmit = async (data: ClaimFormValues) => {
    if (!user || !userInsurance) {
      toast({
        title: "Error",
        description: "You need to be logged in and have active insurance to file a claim",
        variant: "destructive",
      });
      return;
    }

    if (step === 1) {
      setStep(2);
      return;
    }

    if (selectedFiles.length === 0) {
      toast({
        title: "Required Documents",
        description: "Please upload at least one supporting document",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmitting(true);

      // In a real app, we would upload the files to a server first
      // then pass the URLs to the fileClaim function
      const documentUrls = selectedFiles.map(
        (file) => `https://storage.bimabora.com/${file.name}`
      );

      const claimData: Partial<Claim> = {
        claimType: data.claimType,
        serviceDate: new Date(data.serviceDate),
        providerName: data.providerName,
        amount: parseFloat(data.amount),
        description: data.description,
        documentUrls,
        userInsuranceId: userInsurance.id,
      };

      await fileClaim(claimData);
      
      // Reset form and go back to first step
      form.reset();
      setSelectedFiles([]);
      setStep(1);
      
      toast({
        title: "Claim Submitted",
        description: "Your claim has been submitted successfully and is being reviewed",
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Submission Failed",
        description: "An error occurred while submitting your claim. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-5 pb-24">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-neutral-800 mb-1">Submit a Claim</h2>
          <p className="text-neutral-600">Complete the form below to file an insurance claim.</p>
        </div>

        <Card className="bg-white rounded-xl shadow-sm mb-6">
          <CardContent className="p-4">
            {/* Step indicator */}
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full ${step === 1 ? 'bg-primary text-white' : 'bg-neutral-200 text-neutral-500'} flex items-center justify-center font-bold`}>1</div>
                <div className="ml-2">
                  <p className={`font-semibold ${step === 1 ? 'text-neutral-800' : 'text-neutral-500'}`}>Claim Details</p>
                  <p className="text-xs text-neutral-500">Basic information</p>
                </div>
              </div>
              <div className="flex-grow mx-2 h-1 bg-neutral-200">
                <div className={`h-full bg-primary ${step === 2 ? 'w-full' : 'w-0'}`}></div>
              </div>
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full ${step === 2 ? 'bg-primary text-white' : 'bg-neutral-200 text-neutral-500'} flex items-center justify-center font-bold`}>2</div>
                <div className="ml-2">
                  <p className={`font-semibold ${step === 2 ? 'text-neutral-800' : 'text-neutral-500'}`}>Documentation</p>
                  <p className="text-xs text-neutral-500">Upload files</p>
                </div>
              </div>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
                {step === 1 && (
                  <>
                    <FormField
                      control={form.control}
                      name="claimType"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="block text-neutral-700 font-semibold mb-2">Claim Type</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50">
                                <SelectValue placeholder="Select claim type" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="dental">Dental Procedure</SelectItem>
                              <SelectItem value="consultation">Doctor Consultation</SelectItem>
                              <SelectItem value="medication">Prescription Medication</SelectItem>
                              <SelectItem value="hospitalization">Hospitalization</SelectItem>
                              <SelectItem value="other">Other Medical Expense</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="serviceDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="block text-neutral-700 font-semibold mb-2">Date of Service</FormLabel>
                          <FormControl>
                            <Input
                              type="date"
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
                      name="providerName"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="block text-neutral-700 font-semibold mb-2">Provider Name</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="Hospital or doctor's name"
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
                      name="amount"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="block text-neutral-700 font-semibold mb-2">Claim Amount (KSh)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="Enter amount"
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
                      name="description"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="block text-neutral-700 font-semibold mb-2">Description</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Briefly describe the treatment or service"
                              className="w-full px-4 py-3 rounded-lg border border-neutral-300 focus:border-primary focus:ring focus:ring-primary-light focus:ring-opacity-50"
                              rows={3}
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </>
                )}

                {step === 2 && (
                  <div className="space-y-5">
                    <div>
                      <label className="block text-neutral-700 font-semibold mb-2">Upload Supporting Documents</label>
                      <p className="text-neutral-600 text-sm mb-4">
                        Please upload receipts, medical reports, prescriptions, or any other relevant documents.
                      </p>

                      <div className="border-2 border-dashed border-neutral-300 rounded-lg p-6 text-center mb-4">
                        <Upload className="h-8 w-8 text-neutral-400 mx-auto mb-2" />
                        <p className="text-neutral-600 mb-2">Drag & drop files here or click to browse</p>
                        <Button variant="outline" type="button" onClick={() => document.getElementById('file-upload')?.click()}>
                          <ImagePlus className="h-4 w-4 mr-2" />
                          Select Files
                        </Button>
                        <input
                          id="file-upload"
                          type="file"
                          multiple
                          onChange={handleFileChange}
                          className="hidden"
                          accept="image/*,.pdf"
                        />
                      </div>

                      {selectedFiles.length > 0 && (
                        <div className="space-y-2 mt-4">
                          <label className="block text-neutral-700 font-semibold">Selected Files</label>
                          {selectedFiles.map((file, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between bg-neutral-50 p-3 rounded-md"
                            >
                              <div className="flex items-center">
                                <FileText className="h-5 w-5 text-neutral-500 mr-2" />
                                <span className="text-sm truncate max-w-[200px]">{file.name}</span>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                type="button"
                                onClick={() => removeFile(index)}
                              >
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="flex space-x-3 pt-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        type="button"
                        onClick={() => setStep(1)}
                      >
                        Back
                      </Button>
                      <Button
                        className="flex-1"
                        type="submit"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? "Submitting..." : "Submit Claim"}
                      </Button>
                    </div>
                  </div>
                )}

                {step === 1 && (
                  <Button className="w-full py-3" type="submit">
                    Continue to Documents
                  </Button>
                )}
              </form>
            </Form>
          </CardContent>
        </Card>
      </main>
      <BottomNavigation />
    </div>
  );
}
