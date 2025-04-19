import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { ZodError } from "zod";
import { fromZodError } from "zod-validation-error";
import { 
  insertUserSchema, 
  insertClaimSchema, 
  insertPaymentSchema, 
  insertGroupSchema,
  insertGroupMemberSchema,
  insertUserInsuranceSchema,
  insertGroupInsuranceSchema,
  insertGroupActivitySchema
} from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Error handling middleware for Zod validation errors
  const handleZodError = (err: unknown, res: Response) => {
    if (err instanceof ZodError) {
      const validationError = fromZodError(err);
      return res.status(400).json({ message: validationError.message });
    }
    return res.status(500).json({ message: 'Internal Server Error' });
  };

  // Insurance Plans API
  app.get("/api/insurance-plans", async (req, res) => {
    try {
      const planType = req.query.type as string | undefined;
      const plans = await storage.getAllInsurancePlans(planType);
      res.json(plans);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch insurance plans" });
    }
  });

  app.get("/api/insurance-plans/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const plan = await storage.getInsurancePlan(id);
      if (!plan) {
        return res.status(404).json({ message: "Insurance plan not found" });
      }
      res.json(plan);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch insurance plan" });
    }
  });

  // User API
  app.post("/api/users", async (req, res) => {
    try {
      const userData = insertUserSchema.parse(req.body);
      const existingUser = await storage.getUserByUsername(userData.username);
      if (existingUser) {
        return res.status(400).json({ message: "Username already exists" });
      }
      const user = await storage.createUser(userData);
      res.status(201).json(user);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.get("/api/users/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const user = await storage.getUser(id);
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      res.json(user);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  app.patch("/api/users/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const existingUser = await storage.getUser(id);
      if (!existingUser) {
        return res.status(404).json({ message: "User not found" });
      }
      const updatedUser = await storage.updateUser(id, req.body);
      res.json(updatedUser);
    } catch (err) {
      res.status(500).json({ message: "Failed to update user" });
    }
  });

  // User Insurance API
  app.post("/api/user-insurance", async (req, res) => {
    try {
      const userInsuranceData = insertUserInsuranceSchema.parse(req.body);
      const user = await storage.getUser(userInsuranceData.userId);
      const plan = await storage.getInsurancePlan(userInsuranceData.planId);
      
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      if (!plan) {
        return res.status(404).json({ message: "Insurance plan not found" });
      }
      
      const userInsurance = await storage.createUserInsurance(userInsuranceData);
      res.status(201).json(userInsurance);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.get("/api/user-insurance/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const userInsurance = await storage.getUserInsurance(id);
      if (!userInsurance) {
        return res.status(404).json({ message: "User insurance not found" });
      }
      res.json(userInsurance);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch user insurance" });
    }
  });

  app.get("/api/users/:userId/insurance", async (req, res) => {
    try {
      const userId = parseInt(req.params.userId);
      const userInsurances = await storage.getUserInsuranceByUserId(userId);
      res.json(userInsurances);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch user insurance" });
    }
  });

  // Claims API
  app.post("/api/claims", async (req, res) => {
    try {
      const claimData = insertClaimSchema.parse(req.body);
      const user = await storage.getUser(claimData.userId);
      const userInsurance = await storage.getUserInsurance(claimData.userInsuranceId);
      
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      if (!userInsurance) {
        return res.status(404).json({ message: "User insurance not found" });
      }
      
      const claim = await storage.createClaim({
        ...claimData,
        status: "submitted",
      });
      
      res.status(201).json(claim);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.get("/api/claims/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const claim = await storage.getClaim(id);
      if (!claim) {
        return res.status(404).json({ message: "Claim not found" });
      }
      res.json(claim);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch claim" });
    }
  });

  app.get("/api/users/:userId/claims", async (req, res) => {
    try {
      const userId = parseInt(req.params.userId);
      const claims = await storage.getClaimsByUserId(userId);
      res.json(claims);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch claims" });
    }
  });

  app.patch("/api/claims/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const existingClaim = await storage.getClaim(id);
      if (!existingClaim) {
        return res.status(404).json({ message: "Claim not found" });
      }
      const updatedClaim = await storage.updateClaim(id, req.body);
      res.json(updatedClaim);
    } catch (err) {
      res.status(500).json({ message: "Failed to update claim" });
    }
  });

  // Payments API
  app.post("/api/payments", async (req, res) => {
    try {
      const paymentData = insertPaymentSchema.parse(req.body);
      const user = await storage.getUser(paymentData.userId);
      const userInsurance = await storage.getUserInsurance(paymentData.userInsuranceId);
      
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      if (!userInsurance) {
        return res.status(404).json({ message: "User insurance not found" });
      }
      
      // Simulate payment processing
      const payment = await storage.createPayment({
        ...paymentData,
        status: "completed", // In a real app, this would initially be 'pending'
        transactionReference: `TR${Date.now()}`,
      });
      
      // Update user insurance with next payment info
      const plan = await storage.getInsurancePlan(userInsurance.planId);
      if (plan) {
        let nextPaymentAmount;
        let nextPaymentDate = new Date();
        
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
        
        await storage.updateUserInsurance(userInsurance.id, {
          nextPaymentDate,
          nextPaymentAmount,
        });
      }
      
      res.status(201).json(payment);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.get("/api/payments/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const payment = await storage.getPayment(id);
      if (!payment) {
        return res.status(404).json({ message: "Payment not found" });
      }
      res.json(payment);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch payment" });
    }
  });

  app.get("/api/users/:userId/payments", async (req, res) => {
    try {
      const userId = parseInt(req.params.userId);
      const payments = await storage.getPaymentsByUserId(userId);
      res.json(payments);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch payments" });
    }
  });

  // Groups (Chama) API
  app.post("/api/groups", async (req, res) => {
    try {
      const groupData = insertGroupSchema.parse(req.body);
      const adminUser = await storage.getUser(groupData.adminUserId);
      
      if (!adminUser) {
        return res.status(404).json({ message: "Admin user not found" });
      }
      
      const group = await storage.createGroup(groupData);
      
      // Add admin as a member
      await storage.createGroupMember({
        groupId: group.id,
        userId: adminUser.id,
        role: "admin"
      });
      
      res.status(201).json(group);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.get("/api/groups/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const group = await storage.getGroup(id);
      if (!group) {
        return res.status(404).json({ message: "Group not found" });
      }
      
      // Get members
      const members = await storage.getGroupMembersByGroupId(id);
      
      // Get group insurance if any
      const insurance = await storage.getGroupInsuranceByGroupId(id);
      
      res.json({
        ...group,
        members,
        insurance
      });
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch group" });
    }
  });

  app.get("/api/users/:userId/groups", async (req, res) => {
    try {
      const userId = parseInt(req.params.userId);
      const groups = await storage.getGroupsByUserId(userId);
      res.json(groups);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch groups" });
    }
  });

  // Group Members API
  app.post("/api/group-members", async (req, res) => {
    try {
      const memberData = insertGroupMemberSchema.parse(req.body);
      const group = await storage.getGroup(memberData.groupId);
      const user = await storage.getUser(memberData.userId);
      
      if (!group) {
        return res.status(404).json({ message: "Group not found" });
      }
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      
      const groupMember = await storage.createGroupMember(memberData);
      
      // Create activity for new member
      await storage.createGroupActivity({
        groupId: group.id,
        userId: user.id,
        activityType: "member_join",
        description: `${user.fullName} joined the group`,
        amount: 0,
      });
      
      res.status(201).json(groupMember);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.delete("/api/group-members/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const success = await storage.deleteGroupMember(id);
      if (!success) {
        return res.status(404).json({ message: "Group member not found" });
      }
      res.status(204).send();
    } catch (err) {
      res.status(500).json({ message: "Failed to delete group member" });
    }
  });

  // Group Insurance API
  app.post("/api/group-insurance", async (req, res) => {
    try {
      const insuranceData = insertGroupInsuranceSchema.parse(req.body);
      const group = await storage.getGroup(insuranceData.groupId);
      const plan = await storage.getInsurancePlan(insuranceData.planId);
      
      if (!group) {
        return res.status(404).json({ message: "Group not found" });
      }
      if (!plan) {
        return res.status(404).json({ message: "Insurance plan not found" });
      }
      
      const groupInsurance = await storage.createGroupInsurance(insuranceData);
      res.status(201).json(groupInsurance);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.patch("/api/group-insurance/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const existingInsurance = await storage.getGroupInsurance(id);
      if (!existingInsurance) {
        return res.status(404).json({ message: "Group insurance not found" });
      }
      const updatedInsurance = await storage.updateGroupInsurance(id, req.body);
      res.json(updatedInsurance);
    } catch (err) {
      res.status(500).json({ message: "Failed to update group insurance" });
    }
  });

  // Group Activities API
  app.post("/api/group-activities", async (req, res) => {
    try {
      const activityData = insertGroupActivitySchema.parse(req.body);
      const group = await storage.getGroup(activityData.groupId);
      const user = await storage.getUser(activityData.userId);
      
      if (!group) {
        return res.status(404).json({ message: "Group not found" });
      }
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      
      const activity = await storage.createGroupActivity(activityData);
      
      // If it's a contribution, update the group insurance collected amount
      if (activityData.activityType === "contribution" && activityData.amount) {
        const groupInsurance = await storage.getGroupInsuranceByGroupId(group.id);
        if (groupInsurance) {
          const newCollectedAmount = (groupInsurance.collectedAmount || 0) + activityData.amount;
          await storage.updateGroupInsurance(groupInsurance.id, {
            collectedAmount: newCollectedAmount
          });
        }
      }
      
      res.status(201).json(activity);
    } catch (err) {
      handleZodError(err, res);
    }
  });

  app.get("/api/groups/:groupId/activities", async (req, res) => {
    try {
      const groupId = parseInt(req.params.groupId);
      const activities = await storage.getGroupActivitiesByGroupId(groupId);
      res.json(activities);
    } catch (err) {
      res.status(500).json({ message: "Failed to fetch group activities" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
