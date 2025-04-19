import { log } from './vite';
import axios from 'axios';
import * as crypto from 'crypto';

// Check if all required env variables are available
if (!process.env.MPESA_SHORTCODE) {
  throw new Error("MPESA_SHORTCODE environment variable must be set");
}
if (!process.env.MPESA_PASSKEY) {
  throw new Error("MPESA_PASSKEY environment variable must be set");
}
if (!process.env.MPESA_CONSUMER_KEY) {
  throw new Error("MPESA_CONSUMER_KEY environment variable must be set");
}
if (!process.env.MPESA_CONSUMER_SECRET) {
  throw new Error("MPESA_CONSUMER_SECRET environment variable must be set");
}

// M-Pesa API URLs
const MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke';
const OAUTH_TOKEN_URL = `${MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials`;
const STK_PUSH_URL = `${MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest`;
const CALLBACK_URL = 'https://webhook.site/your-webhook-id'; // This needs to be updated in production

// Mpesa class with all required methods
export class MpesaService {
  private shortcode = process.env.MPESA_SHORTCODE;
  private passkey = process.env.MPESA_PASSKEY;
  private consumerKey = process.env.MPESA_CONSUMER_KEY;
  private consumerSecret = process.env.MPESA_CONSUMER_SECRET;

  constructor() {
    log('M-Pesa service initialized with shortcode: ' + this.shortcode, 'mpesa');
  }

  /**
   * Generates the auth token required for M-Pesa API requests
   */
  async getAuthToken(): Promise<string> {
    try {
      const auth = Buffer.from(`${this.consumerKey}:${this.consumerSecret}`).toString('base64');
      
      const response = await axios.get(OAUTH_TOKEN_URL, {
        headers: {
          'Authorization': `Basic ${auth}`
        }
      });

      const token = response.data.access_token;
      log('Retrieved M-Pesa auth token successfully', 'mpesa');
      return token;
    } catch (error) {
      log(`Error getting auth token: ${error}`, 'mpesa');
      throw new Error('Failed to get M-Pesa auth token');
    }
  }

  /**
   * Generate password for STK Push
   * Format: Base64(Shortcode+Passkey+Timestamp)
   */
  generatePassword(timestamp: string): string {
    const password = `${this.shortcode}${this.passkey}${timestamp}`;
    return Buffer.from(password).toString('base64');
  }

  /**
   * Initiate STK Push request to customer's phone
   */
  async initiateSTKPush(
    phoneNumber: string, 
    amount: number, 
    accountReference: string,
    transactionDesc: string
  ): Promise<any> {
    try {
      const token = await this.getAuthToken();
      const timestamp = this.getTimestamp();
      const password = this.generatePassword(timestamp);
      
      // Format phone number
      let formattedPhone = phoneNumber.replace(/\D/g, ''); // Remove all non-digit characters
      
      // Check if number starts with 0, convert to 254 format
      if (formattedPhone.startsWith('0')) {
        formattedPhone = `254${formattedPhone.substring(1)}`;
      } 
      // Ensure it starts with 254 for Kenya
      else if (!formattedPhone.startsWith('254')) {
        formattedPhone = `254${formattedPhone}`;
      }
      
      log(`Formatted phone number: ${formattedPhone}`, 'mpesa');
      
      const requestBody = {
        BusinessShortCode: this.shortcode,
        Password: password,
        Timestamp: timestamp,
        TransactionType: 'CustomerPayBillOnline',
        Amount: Math.round(amount),
        PartyA: formattedPhone,
        PartyB: this.shortcode,
        PhoneNumber: formattedPhone,
        CallBackURL: CALLBACK_URL,
        AccountReference: accountReference || 'BimaBora Insurance',
        TransactionDesc: transactionDesc || 'Insurance Premium Payment'
      };

      log(`Initiating STK Push to ${formattedPhone} for KES ${amount}`, 'mpesa');
      
      const response = await axios.post(STK_PUSH_URL, requestBody, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      log(`STK Push response: ${JSON.stringify(response.data)}`, 'mpesa');
      return response.data;
    } catch (error) {
      log(`STK Push error: ${error}`, 'mpesa');
      throw new Error('Failed to initiate M-Pesa payment');
    }
  }

  /**
   * Get timestamp in the format YYYYMMDDHHmmss
   */
  getTimestamp(): string {
    const date = new Date();
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}${month}${day}${hours}${minutes}${seconds}`;
  }
}

// Export a singleton instance
export const mpesaService = new MpesaService();