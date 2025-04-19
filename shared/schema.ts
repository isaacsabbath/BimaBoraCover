import { pgTable, text, serial, integer, boolean, date, json, timestamp, doublePrecision } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Users
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  fullName: text("full_name").notNull(),
  email: text("email").notNull(),
  phoneNumber: text("phone_number").notNull(),
  idNumber: text("id_number"),
  dateOfBirth: date("date_of_birth"),
  address: text("address"),
  notificationPreferences: json("notification_preferences").$type<{
    paymentReminders: boolean;
    claimUpdates: boolean;
    newPlans: boolean;
  }>(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
  fullName: true,
  email: true,
  phoneNumber: true,
  idNumber: true,
  dateOfBirth: true,
  address: true,
  notificationPreferences: true,
});

// Insurance plans
export const insurancePlans = pgTable("insurance_plans", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description").notNull(),
  coverageAmount: integer("coverage_amount").notNull(),
  dailyPremium: doublePrecision("daily_premium").notNull(),
  weeklyPremium: doublePrecision("weekly_premium").notNull(),
  monthlyPremium: doublePrecision("monthly_premium").notNull(),
  benefits: json("benefits").$type<string[]>(),
  planType: text("plan_type").notNull(), // 'individual', 'family', 'group'
  isPopular: boolean("is_popular").default(false),
  tag: text("tag"), // e.g., 'Most Affordable', null if no tag
});

export const insertInsurancePlanSchema = createInsertSchema(insurancePlans).pick({
  name: true,
  description: true,
  coverageAmount: true,
  dailyPremium: true,
  weeklyPremium: true,
  monthlyPremium: true,
  benefits: true,
  planType: true,
  isPopular: true,
  tag: true,
});

// User insurance subscriptions
export const userInsurance = pgTable("user_insurance", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").notNull(),
  planId: integer("plan_id").notNull(),
  status: text("status").notNull(), // 'active', 'inactive', 'pending'
  startDate: date("start_date").notNull(),
  endDate: date("end_date"),
  paymentFrequency: text("payment_frequency").notNull(), // 'daily', 'weekly', 'monthly'
  nextPaymentDate: date("next_payment_date"),
  nextPaymentAmount: doublePrecision("next_payment_amount"),
});

export const insertUserInsuranceSchema = createInsertSchema(userInsurance).pick({
  userId: true,
  planId: true,
  status: true,
  startDate: true,
  endDate: true,
  paymentFrequency: true,
  nextPaymentDate: true,
  nextPaymentAmount: true,
});

// Claims
export const claims = pgTable("claims", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").notNull(),
  userInsuranceId: integer("user_insurance_id").notNull(),
  claimType: text("claim_type").notNull(), // 'dental', 'consultation', 'medication', 'hospitalization', 'other'
  serviceDate: date("service_date").notNull(),
  providerName: text("provider_name").notNull(),
  amount: doublePrecision("amount").notNull(),
  description: text("description").notNull(),
  status: text("status").notNull(), // 'submitted', 'in_review', 'approved', 'rejected'
  documentUrls: json("document_urls").$type<string[]>(),
  submissionDate: timestamp("submission_date").defaultNow(),
  approvalDate: timestamp("approval_date"),
  rejectionReason: text("rejection_reason"),
});

export const insertClaimSchema = createInsertSchema(claims).pick({
  userId: true,
  userInsuranceId: true,
  claimType: true,
  serviceDate: true,
  providerName: true,
  amount: true,
  description: true,
  status: true,
  documentUrls: true,
});

// Payments
export const payments = pgTable("payments", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").notNull(),
  userInsuranceId: integer("user_insurance_id").notNull(),
  amount: doublePrecision("amount").notNull(),
  paymentMethod: text("payment_method").notNull(), // 'mpesa', 'chama', 'bank'
  status: text("status").notNull(), // 'pending', 'completed', 'failed'
  transactionReference: text("transaction_reference"),
  paymentDate: timestamp("payment_date").defaultNow(),
});

export const insertPaymentSchema = createInsertSchema(payments).pick({
  userId: true,
  userInsuranceId: true,
  amount: true,
  paymentMethod: true,
  status: true,
  transactionReference: true,
});

// Chama/Groups
export const groups = pgTable("groups", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  createdAt: timestamp("created_at").defaultNow(),
  adminUserId: integer("admin_user_id").notNull(),
});

export const insertGroupSchema = createInsertSchema(groups).pick({
  name: true,
  description: true,
  adminUserId: true,
});

// Group Members
export const groupMembers = pgTable("group_members", {
  id: serial("id").primaryKey(),
  groupId: integer("group_id").notNull(),
  userId: integer("user_id").notNull(),
  joinedAt: timestamp("joined_at").defaultNow(),
  role: text("role").notNull(), // 'admin', 'member'
});

export const insertGroupMemberSchema = createInsertSchema(groupMembers).pick({
  groupId: true,
  userId: true,
  role: true,
});

// Group Insurance
export const groupInsurance = pgTable("group_insurance", {
  id: serial("id").primaryKey(),
  groupId: integer("group_id").notNull(),
  planId: integer("plan_id").notNull(),
  status: text("status").notNull(), // 'active', 'inactive', 'pending'
  startDate: date("start_date").notNull(),
  endDate: date("end_date"),
  monthlyPremium: doublePrecision("monthly_premium").notNull(),
  nextPaymentDate: date("next_payment_date"),
  collectedAmount: doublePrecision("collected_amount").default(0),
  requiredAmount: doublePrecision("required_amount").notNull(),
});

export const insertGroupInsuranceSchema = createInsertSchema(groupInsurance).pick({
  groupId: true,
  planId: true,
  status: true,
  startDate: true,
  endDate: true,
  monthlyPremium: true,
  nextPaymentDate: true,
  collectedAmount: true,
  requiredAmount: true,
});

// Group Activities
export const groupActivities = pgTable("group_activities", {
  id: serial("id").primaryKey(),
  groupId: integer("group_id").notNull(),
  userId: integer("user_id").notNull(),
  activityType: text("activity_type").notNull(), // 'contribution', 'claim', 'member_join', 'status_change'
  description: text("description").notNull(),
  amount: doublePrecision("amount"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertGroupActivitySchema = createInsertSchema(groupActivities).pick({
  groupId: true,
  userId: true,
  activityType: true,
  description: true,
  amount: true,
});

// Export types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type InsurancePlan = typeof insurancePlans.$inferSelect;
export type InsertInsurancePlan = z.infer<typeof insertInsurancePlanSchema>;

export type UserInsurance = typeof userInsurance.$inferSelect;
export type InsertUserInsurance = z.infer<typeof insertUserInsuranceSchema>;

export type Claim = typeof claims.$inferSelect;
export type InsertClaim = z.infer<typeof insertClaimSchema>;

export type Payment = typeof payments.$inferSelect;
export type InsertPayment = z.infer<typeof insertPaymentSchema>;

export type Group = typeof groups.$inferSelect;
export type InsertGroup = z.infer<typeof insertGroupSchema>;

export type GroupMember = typeof groupMembers.$inferSelect;
export type InsertGroupMember = z.infer<typeof insertGroupMemberSchema>;

export type GroupInsurance = typeof groupInsurance.$inferSelect;
export type InsertGroupInsurance = z.infer<typeof insertGroupInsuranceSchema>;

export type GroupActivity = typeof groupActivities.$inferSelect;
export type InsertGroupActivity = z.infer<typeof insertGroupActivitySchema>;
