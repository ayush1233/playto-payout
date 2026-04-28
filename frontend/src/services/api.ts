import axios from 'axios';
import type { LedgerEntry, Merchant, Paginated, Payout } from '../types';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const merchantId = localStorage.getItem('playto_merchant_id') ?? '1';
  config.headers['X-Merchant-ID'] = merchantId;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('playto_merchant_id');
    }
    return Promise.reject(error);
  },
);

export const getMerchant = async (): Promise<Merchant> => {
  const response = await api.get('/merchants/me/');
  return response.data;
};

export const getLedger = async (): Promise<Paginated<LedgerEntry>> => {
  const response = await api.get('/merchants/me/ledger/?page_size=20');
  return response.data;
};

export const getPayouts = async (): Promise<Paginated<Payout>> => {
  const response = await api.get('/payouts/');
  return response.data;
};

export const createPayout = async (
  amountPaise: number,
  bankAccountId: number,
  idempotencyKey: string,
): Promise<Payout> => {
  const response = await api.post(
    '/payouts/',
    { amount_paise: amountPaise, bank_account_id: bankAccountId },
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return response.data;
};
