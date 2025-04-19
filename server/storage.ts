import {
  User, InsertUser, 
  InsurancePlan, InsertInsurancePlan,
  UserInsurance, InsertUserInsurance,
  Claim, InsertClaim,
  Payment, InsertPayment,
  Group, InsertGroup,
  GroupMember, InsertGroupMember,
  GroupInsurance, InsertGroupInsurance,
  GroupActivity, InsertGroupActivity
} from "@shared/schema";

// Interface for storage operations
export interface IStorage {
  // User operations
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  updateUser(id: number, userData: Partial<User>): Promise<User | undefined>;

  // Insurance plan operations
  getInsurancePlan(id: number): Promise<InsurancePlan | undefined>;
  getAllInsurancePlans(planType?: string): Promise<InsurancePlan[]>;
  createInsurancePlan(plan: InsertInsurancePlan): Promise<InsurancePlan>;

  // User insurance operations
  getUserInsurance(id: number): Promise<UserInsurance | undefined>;
  getUserInsuranceByUserId(userId: number): Promise<UserInsurance[]>;
  createUserInsurance(userInsurance: InsertUserInsurance): Promise<UserInsurance>;
  updateUserInsurance(id: number, data: Partial<UserInsurance>): Promise<UserInsurance | undefined>;

  // Claim operations
  getClaim(id: number): Promise<Claim | undefined>;
  getClaimsByUserId(userId: number): Promise<Claim[]>;
  createClaim(claim: InsertClaim): Promise<Claim>;
  updateClaim(id: number, claimData: Partial<Claim>): Promise<Claim | undefined>;

  // Payment operations
  getPayment(id: number): Promise<Payment | undefined>;
  getPaymentsByUserId(userId: number): Promise<Payment[]>;
  createPayment(payment: InsertPayment): Promise<Payment>;
  updatePayment(id: number, paymentData: Partial<Payment>): Promise<Payment | undefined>;

  // Group operations
  getGroup(id: number): Promise<Group | undefined>;
  getGroupsByUserId(userId: number): Promise<Group[]>;
  createGroup(group: InsertGroup): Promise<Group>;
  updateGroup(id: number, groupData: Partial<Group>): Promise<Group | undefined>;

  // Group member operations
  getGroupMember(id: number): Promise<GroupMember | undefined>;
  getGroupMembersByGroupId(groupId: number): Promise<GroupMember[]>;
  getGroupMembersByUserId(userId: number): Promise<GroupMember[]>;
  createGroupMember(groupMember: InsertGroupMember): Promise<GroupMember>;
  deleteGroupMember(id: number): Promise<boolean>;

  // Group insurance operations
  getGroupInsurance(id: number): Promise<GroupInsurance | undefined>;
  getGroupInsuranceByGroupId(groupId: number): Promise<GroupInsurance | undefined>;
  createGroupInsurance(groupInsurance: InsertGroupInsurance): Promise<GroupInsurance>;
  updateGroupInsurance(id: number, data: Partial<GroupInsurance>): Promise<GroupInsurance | undefined>;

  // Group activity operations
  getGroupActivitiesByGroupId(groupId: number): Promise<GroupActivity[]>;
  createGroupActivity(activity: InsertGroupActivity): Promise<GroupActivity>;
}

// Memory storage implementation
export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private insurancePlans: Map<number, InsurancePlan>;
  private userInsurances: Map<number, UserInsurance>;
  private claims: Map<number, Claim>;
  private payments: Map<number, Payment>;
  private groups: Map<number, Group>;
  private groupMembers: Map<number, GroupMember>;
  private groupInsurances: Map<number, GroupInsurance>;
  private groupActivities: Map<number, GroupActivity>;

  private userIdCounter: number;
  private planIdCounter: number;
  private userInsuranceIdCounter: number;
  private claimIdCounter: number;
  private paymentIdCounter: number;
  private groupIdCounter: number;
  private groupMemberIdCounter: number;
  private groupInsuranceIdCounter: number;
  private groupActivityIdCounter: number;

  constructor() {
    this.users = new Map();
    this.insurancePlans = new Map();
    this.userInsurances = new Map();
    this.claims = new Map();
    this.payments = new Map();
    this.groups = new Map();
    this.groupMembers = new Map();
    this.groupInsurances = new Map();
    this.groupActivities = new Map();

    this.userIdCounter = 2; // Start from 2 since we're adding a user with ID 1
    this.planIdCounter = 1;
    this.userInsuranceIdCounter = 1;
    this.claimIdCounter = 1;
    this.paymentIdCounter = 1;
    this.groupIdCounter = 1;
    this.groupMemberIdCounter = 1;
    this.groupInsuranceIdCounter = 1;
    this.groupActivityIdCounter = 1;

    // Initialize with default insurance plans
    this.createDefaultInsurancePlans();
    
    // Create default test user matching client mock data
    this.createDefaultTestUser();
  }
  
  private createDefaultTestUser(): void {
    // Create a test user with ID 1 to match the client mock
    const testUser: User = {
      id: 1,
      username: "johndoe",
      password: "password", 
      fullName: "John Doe",
      email: "johndoe@example.com",
      phoneNumber: "0712345678",
      idNumber: "12345678",
      dateOfBirth: "1990-01-15", 
      address: "123 Moi Avenue, Nairobi",
      notificationPreferences: {
        paymentReminders: true,
        claimUpdates: true,
        newPlans: true
      },
      createdAt: new Date()
    };
    
    this.users.set(testUser.id, testUser);
    
    // Create a user insurance record for the test user
    const userInsurance: UserInsurance = {
      id: 1,
      userId: 1,
      planId: 3, // Health + Dental Combo
      status: "active",
      startDate: new Date().toISOString().split('T')[0],
      endDate: null,
      paymentFrequency: "monthly",
      nextPaymentDate: null,
      nextPaymentAmount: null
    };
    
    this.userInsurances.set(userInsurance.id, userInsurance);
    this.userInsuranceIdCounter++;
  }

  private createDefaultInsurancePlans(): void {
    // Dental-Only Plan
    const dentalOnlyPlan: InsertInsurancePlan = {
      name: "Dental-Only Cover",
      description: "Basic dental care including checkups, cleanings, and minor procedures.",
      coverageAmount: 10000,
      dailyPremium: 15,
      weeklyPremium: 105,
      monthlyPremium: 450,
      yearlyPremium: 4800,
      benefits: [
        "Dental checkups & cleanings",
        "Basic dental procedures",
        "Up to KSh 10,000 annual coverage"
      ],
      planType: "dental",
      isPopular: false,
      tag: "Most Affordable"
    };

    // Health-Only Plan
    const healthOnlyPlan: InsertInsurancePlan = {
      name: "Health-Only Cover",
      description: "Essential health coverage for outpatient care and medications.",
      coverageAmount: 20000,
      dailyPremium: 30,
      weeklyPremium: 210,
      monthlyPremium: 900,
      yearlyPremium: 9800,
      benefits: [
        "Outpatient consultations",
        "Prescription medications",
        "Basic diagnostics",
        "Up to KSh 20,000 annual coverage"
      ],
      planType: "health",
      isPopular: false,
      tag: "Essential Care"
    };

    // Health + Dental Combo Plan
    const healthDentalPlan: InsertInsurancePlan = {
      name: "Health + Dental Combo",
      description: "Comprehensive coverage for both medical and dental needs.",
      coverageAmount: 25000,
      dailyPremium: 40,
      weeklyPremium: 280,
      monthlyPremium: 1200,
      yearlyPremium: 13000,
      benefits: [
        "All dental benefits",
        "Outpatient care & consultations",
        "Prescription medications",
        "Up to KSh 25,000 annual coverage"
      ],
      planType: "health_dental",
      isPopular: true,
      tag: "Best Value"
    };

    // Family Health Plan
    const familyHealthPlan: InsertInsurancePlan = {
      name: "Family Health Cover",
      description: "Health protection for you and up to 4 dependents.",
      coverageAmount: 40000,
      dailyPremium: 80,
      weeklyPremium: 560,
      monthlyPremium: 2400,
      yearlyPremium: 26000,
      benefits: [
        "Outpatient care for all family members",
        "Maternity benefits",
        "Children's vaccinations",
        "Up to KSh 40,000 annual coverage"
      ],
      planType: "family",
      isPopular: false,
      tag: null
    };

    // Complete Family Plan
    const completeFamilyPlan: InsertInsurancePlan = {
      name: "Complete Family Cover",
      description: "Full health and dental protection for you and up to 4 dependents.",
      coverageAmount: 50000,
      dailyPremium: 100,
      weeklyPremium: 700,
      monthlyPremium: 3000,
      yearlyPremium: 32000,
      benefits: [
        "All health benefits for the entire family",
        "Dental care for all family members",
        "Maternity benefits",
        "Children's vaccinations",
        "Up to KSh 50,000 annual coverage"
      ],
      planType: "family",
      isPopular: false,
      tag: "Comprehensive"
    };

    this.createInsurancePlan(dentalOnlyPlan);
    this.createInsurancePlan(healthOnlyPlan);
    this.createInsurancePlan(healthDentalPlan);
    this.createInsurancePlan(familyHealthPlan);
    this.createInsurancePlan(completeFamilyPlan);
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userIdCounter++;
    const now = new Date();
    const user: User = { ...insertUser, id, createdAt: now };
    this.users.set(id, user);
    return user;
  }

  async updateUser(id: number, userData: Partial<User>): Promise<User | undefined> {
    const existingUser = this.users.get(id);
    if (!existingUser) return undefined;

    const updatedUser = { ...existingUser, ...userData };
    this.users.set(id, updatedUser);
    return updatedUser;
  }

  // Insurance plan methods
  async getInsurancePlan(id: number): Promise<InsurancePlan | undefined> {
    return this.insurancePlans.get(id);
  }

  async getAllInsurancePlans(planType?: string): Promise<InsurancePlan[]> {
    const plans = Array.from(this.insurancePlans.values());
    if (planType) {
      return plans.filter(plan => plan.planType === planType);
    }
    return plans;
  }

  async createInsurancePlan(plan: InsertInsurancePlan): Promise<InsurancePlan> {
    const id = this.planIdCounter++;
    const newPlan: InsurancePlan = { ...plan, id };
    this.insurancePlans.set(id, newPlan);
    return newPlan;
  }

  // User insurance methods
  async getUserInsurance(id: number): Promise<UserInsurance | undefined> {
    return this.userInsurances.get(id);
  }

  async getUserInsuranceByUserId(userId: number): Promise<UserInsurance[]> {
    return Array.from(this.userInsurances.values()).filter(
      insurance => insurance.userId === userId
    );
  }

  async createUserInsurance(userInsurance: InsertUserInsurance): Promise<UserInsurance> {
    const id = this.userInsuranceIdCounter++;
    const newUserInsurance: UserInsurance = { ...userInsurance, id };
    this.userInsurances.set(id, newUserInsurance);
    return newUserInsurance;
  }

  async updateUserInsurance(id: number, data: Partial<UserInsurance>): Promise<UserInsurance | undefined> {
    const existingUserInsurance = this.userInsurances.get(id);
    if (!existingUserInsurance) return undefined;

    const updatedUserInsurance = { ...existingUserInsurance, ...data };
    this.userInsurances.set(id, updatedUserInsurance);
    return updatedUserInsurance;
  }

  // Claim methods
  async getClaim(id: number): Promise<Claim | undefined> {
    return this.claims.get(id);
  }

  async getClaimsByUserId(userId: number): Promise<Claim[]> {
    return Array.from(this.claims.values()).filter(
      claim => claim.userId === userId
    );
  }

  async createClaim(claim: InsertClaim): Promise<Claim> {
    const id = this.claimIdCounter++;
    const now = new Date();
    const newClaim: Claim = { 
      ...claim, 
      id, 
      submissionDate: now, 
      approvalDate: undefined, 
      rejectionReason: undefined 
    };
    this.claims.set(id, newClaim);
    return newClaim;
  }

  async updateClaim(id: number, claimData: Partial<Claim>): Promise<Claim | undefined> {
    const existingClaim = this.claims.get(id);
    if (!existingClaim) return undefined;

    const updatedClaim = { ...existingClaim, ...claimData };
    this.claims.set(id, updatedClaim);
    return updatedClaim;
  }

  // Payment methods
  async getPayment(id: number): Promise<Payment | undefined> {
    return this.payments.get(id);
  }

  async getPaymentsByUserId(userId: number): Promise<Payment[]> {
    return Array.from(this.payments.values()).filter(
      payment => payment.userId === userId
    );
  }

  async createPayment(payment: InsertPayment): Promise<Payment> {
    const id = this.paymentIdCounter++;
    const now = new Date();
    const newPayment: Payment = { ...payment, id, paymentDate: now };
    this.payments.set(id, newPayment);
    return newPayment;
  }

  async updatePayment(id: number, paymentData: Partial<Payment>): Promise<Payment | undefined> {
    const existingPayment = this.payments.get(id);
    if (!existingPayment) return undefined;

    const updatedPayment = { ...existingPayment, ...paymentData };
    this.payments.set(id, updatedPayment);
    return updatedPayment;
  }

  // Group methods
  async getGroup(id: number): Promise<Group | undefined> {
    return this.groups.get(id);
  }

  async getGroupsByUserId(userId: number): Promise<Group[]> {
    const userGroupMemberships = await this.getGroupMembersByUserId(userId);
    const groupIds = userGroupMemberships.map(member => member.groupId);
    return Array.from(this.groups.values()).filter(
      group => groupIds.includes(group.id) || group.adminUserId === userId
    );
  }

  async createGroup(group: InsertGroup): Promise<Group> {
    const id = this.groupIdCounter++;
    const now = new Date();
    const newGroup: Group = { ...group, id, createdAt: now };
    this.groups.set(id, newGroup);
    return newGroup;
  }

  async updateGroup(id: number, groupData: Partial<Group>): Promise<Group | undefined> {
    const existingGroup = this.groups.get(id);
    if (!existingGroup) return undefined;

    const updatedGroup = { ...existingGroup, ...groupData };
    this.groups.set(id, updatedGroup);
    return updatedGroup;
  }

  // Group member methods
  async getGroupMember(id: number): Promise<GroupMember | undefined> {
    return this.groupMembers.get(id);
  }

  async getGroupMembersByGroupId(groupId: number): Promise<GroupMember[]> {
    return Array.from(this.groupMembers.values()).filter(
      member => member.groupId === groupId
    );
  }

  async getGroupMembersByUserId(userId: number): Promise<GroupMember[]> {
    return Array.from(this.groupMembers.values()).filter(
      member => member.userId === userId
    );
  }

  async createGroupMember(groupMember: InsertGroupMember): Promise<GroupMember> {
    const id = this.groupMemberIdCounter++;
    const now = new Date();
    const newGroupMember: GroupMember = { ...groupMember, id, joinedAt: now };
    this.groupMembers.set(id, newGroupMember);
    return newGroupMember;
  }

  async deleteGroupMember(id: number): Promise<boolean> {
    return this.groupMembers.delete(id);
  }

  // Group insurance methods
  async getGroupInsurance(id: number): Promise<GroupInsurance | undefined> {
    return this.groupInsurances.get(id);
  }

  async getGroupInsuranceByGroupId(groupId: number): Promise<GroupInsurance | undefined> {
    return Array.from(this.groupInsurances.values()).find(
      insurance => insurance.groupId === groupId
    );
  }

  async createGroupInsurance(groupInsurance: InsertGroupInsurance): Promise<GroupInsurance> {
    const id = this.groupInsuranceIdCounter++;
    const newGroupInsurance: GroupInsurance = { ...groupInsurance, id };
    this.groupInsurances.set(id, newGroupInsurance);
    return newGroupInsurance;
  }

  async updateGroupInsurance(id: number, data: Partial<GroupInsurance>): Promise<GroupInsurance | undefined> {
    const existingGroupInsurance = this.groupInsurances.get(id);
    if (!existingGroupInsurance) return undefined;

    const updatedGroupInsurance = { ...existingGroupInsurance, ...data };
    this.groupInsurances.set(id, updatedGroupInsurance);
    return updatedGroupInsurance;
  }

  // Group activity methods
  async getGroupActivitiesByGroupId(groupId: number): Promise<GroupActivity[]> {
    return Array.from(this.groupActivities.values())
      .filter(activity => activity.groupId === groupId)
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  async createGroupActivity(activity: InsertGroupActivity): Promise<GroupActivity> {
    const id = this.groupActivityIdCounter++;
    const now = new Date();
    const newActivity: GroupActivity = { ...activity, id, createdAt: now };
    this.groupActivities.set(id, newActivity);
    return newActivity;
  }
}

export const storage = new MemStorage();
