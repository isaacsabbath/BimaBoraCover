
import { Router } from "express";
import { storage } from "../storage";
import { z } from "zod";
import { fromZodError } from "zod-validation-error";
import { insertInsurancePlanSchema } from "@shared/schema";

const adminRouter = Router();

// Admin middleware
const isAdmin = async (req: any, res: any, next: any) => {
  const user = await storage.getUser(req.session?.userId);
  if (!user?.isAdmin) {
    return res.status(403).json({ message: "Unauthorized" });
  }
  next();
};

adminRouter.use(isAdmin);

// Users
adminRouter.get("/users", async (req, res) => {
  const users = await storage.getAllUsers();
  res.json(users);
});

// Claims
adminRouter.get("/claims", async (req, res) => {
  const claims = await storage.getAllClaims();
  res.json(claims);
});

adminRouter.post("/claims/:id/approve", async (req, res) => {
  const id = parseInt(req.params.id);
  const claim = await storage.updateClaim(id, {
    status: "approved",
    approvalDate: new Date(),
  });
  res.json(claim);
});

adminRouter.post("/claims/:id/reject", async (req, res) => {
  const id = parseInt(req.params.id);
  const claim = await storage.updateClaim(id, {
    status: "rejected",
    rejectionReason: req.body.reason,
  });
  res.json(claim);
});

// Payments
adminRouter.get("/payments", async (req, res) => {
  const payments = await storage.getAllPayments();
  res.json(payments);
});

// Insurance Plans
adminRouter.get("/plans", async (req, res) => {
  const plans = await storage.getAllInsurancePlans();
  res.json(plans);
});

adminRouter.post("/plans", async (req, res) => {
  try {
    const planData = insertInsurancePlanSchema.parse(req.body);
    const plan = await storage.createInsurancePlan(planData);
    res.status(201).json(plan);
  } catch (err) {
    if (err instanceof z.ZodError) {
      const validationError = fromZodError(err);
      return res.status(400).json({ message: validationError.message });
    }
    res.status(500).json({ message: "Failed to create plan" });
  }
});

export default adminRouter;
