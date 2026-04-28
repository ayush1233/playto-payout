export interface BankAccount {
  id: number;
  account_holder_name: string;
  account_number: string;
  ifsc_code: string;
  is_primary: boolean;
  created_at: string;
}

export interface Merchant {
  id: number;
  name: string;
  email: string;
  available_balance: number;
  held_balance: number;
  bank_accounts: BankAccount[];
  created_at: string;
}

export interface Payout {
  id: number;
  merchant_id: number;
  amount_paise: number;
  bank_account_id: number;
  bank_account: BankAccount;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  updated_at: string;
  attempt_count: number;
  idempotency_key: string;
}

export interface LedgerEntry {
  id: number;
  amount: number;
  entry_type: 'CREDIT' | 'DEBIT' | 'HOLD' | 'HOLD_RELEASE';
  description: string;
  created_at: string;
  payout_id?: number;
  payout_status?: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
