import { useMemo, useState } from 'react';
import type React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, CheckCircle2, Loader2, RefreshCw, Send, Wallet } from 'lucide-react';
import { createPayout, getLedger, getMerchant, getPayouts } from '../services/api';
import type { LedgerEntry, Payout } from '../types';

const demoMerchants = [
  { id: 1, name: 'PixelCraft Studio' },
  { id: 2, name: 'WordFlow Agency' },
  { id: 3, name: 'DevSprint Labs' },
];

const formatMoney = (paise: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(paise / 100);

const statusClass: Record<Payout['status'], string> = {
  PENDING: 'bg-zinc-100 text-zinc-700',
  PROCESSING: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-emerald-100 text-emerald-700',
  FAILED: 'bg-rose-100 text-rose-700',
};

const entryClass: Record<LedgerEntry['entry_type'], string> = {
  CREDIT: 'bg-emerald-100 text-emerald-700',
  DEBIT: 'bg-rose-100 text-rose-700',
  HOLD: 'bg-amber-100 text-amber-700',
  HOLD_RELEASE: 'bg-sky-100 text-sky-700',
};

export function Dashboard() {
  const [merchantId, setMerchantId] = useState(
    localStorage.getItem('playto_merchant_id') ?? '1',
  );
  const [bankAccountId, setBankAccountId] = useState('');
  const [amountRupees, setAmountRupees] = useState('');
  const [idempotencyKey, setIdempotencyKey] = useState(crypto.randomUUID());
  const [formError, setFormError] = useState('');
  const queryClient = useQueryClient();

  const merchantQuery = useQuery({
    queryKey: ['merchant', merchantId],
    queryFn: getMerchant,
  });

  const ledgerQuery = useQuery({
    queryKey: ['ledger', merchantId],
    queryFn: getLedger,
  });

  const payoutsQuery = useQuery({
    queryKey: ['payouts', merchantId],
    queryFn: getPayouts,
    refetchInterval: (query) => {
      const payouts = query.state.data?.results ?? [];
      return payouts.some((payout) => ['PENDING', 'PROCESSING'].includes(payout.status))
        ? 5000
        : false;
    },
  });

  const merchant = merchantQuery.data;
  const ledger = ledgerQuery.data?.results ?? [];
  const payouts = payoutsQuery.data?.results ?? [];
  const totalCredits = useMemo(
    () =>
      ledger
        .filter((entry) => entry.entry_type === 'CREDIT')
        .reduce((sum, entry) => sum + entry.amount, 0),
    [ledger],
  );

  const mutation = useMutation({
    mutationFn: () => {
      if (!merchant) throw new Error('merchant not loaded');
      const amountPaise = Math.round(Number(amountRupees) * 100);
      if (!bankAccountId) throw new Error('Select a bank account');
      if (!Number.isInteger(amountPaise) || amountPaise <= 0) {
        throw new Error('Enter a positive payout amount');
      }
      if (amountPaise > merchant.available_balance) {
        throw new Error('Amount exceeds available balance');
      }
      return createPayout(amountPaise, Number(bankAccountId), idempotencyKey);
    },
    onSuccess: () => {
      setFormError('');
      setAmountRupees('');
      setIdempotencyKey(crypto.randomUUID());
      queryClient.invalidateQueries({ queryKey: ['merchant', merchantId] });
      queryClient.invalidateQueries({ queryKey: ['ledger', merchantId] });
      queryClient.invalidateQueries({ queryKey: ['payouts', merchantId] });
    },
    onError: (error: any) => {
      setFormError(error.response?.data?.error ?? error.message ?? 'Payout failed');
    },
  });

  const switchMerchant = (id: number) => {
    localStorage.setItem('playto_merchant_id', String(id));
    setMerchantId(String(id));
    setBankAccountId('');
  };

  const loading = merchantQuery.isLoading || ledgerQuery.isLoading || payoutsQuery.isLoading;

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-zinc-950 text-white">
              <Wallet size={20} />
            </span>
            <div>
              <h1 className="text-xl font-semibold">Playto Payouts</h1>
              <p className="text-sm text-zinc-500">Ledger-backed payout operations</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {demoMerchants.map((merchant) => (
              <button
                key={merchant.id}
                className={`rounded-md border px-3 py-2 text-sm ${
                  merchantId === String(merchant.id)
                    ? 'border-zinc-950 bg-zinc-950 text-white'
                    : 'border-zinc-300 bg-white text-zinc-700'
                }`}
                onClick={() => switchMerchant(merchant.id)}
              >
                {merchant.name}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        {loading || !merchant ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="animate-spin text-zinc-500" />
          </div>
        ) : (
          <>
            <section className="grid gap-3 md:grid-cols-3">
              <Stat label="Available Balance" value={formatMoney(merchant.available_balance)} />
              <Stat label="Held Balance" value={formatMoney(merchant.held_balance)} />
              <Stat label="Total Credits" value={formatMoney(totalCredits)} />
            </section>

            <section className="grid gap-6 lg:grid-cols-[380px_1fr]">
              <form
                className="rounded-lg border border-zinc-200 bg-white p-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  mutation.mutate();
                }}
              >
                <h2 className="mb-4 text-base font-semibold">Request payout</h2>
                <label className="mb-3 block">
                  <span className="mb-1 block text-sm text-zinc-600">Bank account</span>
                  <select
                    className="w-full rounded-md border border-zinc-300 px-3 py-2"
                    value={bankAccountId}
                    onChange={(event) => setBankAccountId(event.target.value)}
                  >
                    <option value="">Select account</option>
                    {merchant.bank_accounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.account_holder_name} - {account.account_number.slice(-4)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="mb-3 block">
                  <span className="mb-1 block text-sm text-zinc-600">Amount</span>
                  <input
                    className="w-full rounded-md border border-zinc-300 px-3 py-2"
                    inputMode="decimal"
                    min="0"
                    step="0.01"
                    value={amountRupees}
                    onChange={(event) => setAmountRupees(event.target.value)}
                    placeholder="0.00"
                  />
                </label>
                {formError && (
                  <p className="mb-3 flex items-center gap-2 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
                    <AlertCircle size={16} /> {formError}
                  </p>
                )}
                {mutation.isSuccess && (
                  <p className="mb-3 flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                    <CheckCircle2 size={16} /> Payout requested successfully
                  </p>
                )}
                <button
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-3 py-2 text-white disabled:opacity-50"
                  disabled={mutation.isPending}
                >
                  {mutation.isPending ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                  Request Payout
                </button>
              </form>

              <div className="rounded-lg border border-zinc-200 bg-white p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-base font-semibold">Payout history</h2>
                  {payoutsQuery.isFetching && <RefreshCw className="animate-spin text-zinc-400" size={16} />}
                </div>
                <Table
                  headers={['Date', 'Amount', 'Bank Account', 'Status']}
                  rows={payouts.map((payout) => [
                    new Date(payout.created_at).toLocaleString(),
                    formatMoney(payout.amount_paise),
                    payout.bank_account.account_number.slice(-4),
                    <Badge key={payout.id} className={statusClass[payout.status]}>
                      {payout.status === 'PROCESSING' && <Loader2 className="animate-spin" size={12} />}
                      {payout.status}
                    </Badge>,
                  ])}
                />
              </div>
            </section>

            <section className="rounded-lg border border-zinc-200 bg-white p-4">
              <h2 className="mb-4 text-base font-semibold">Recent ledger entries</h2>
              <Table
                headers={['Date', 'Type', 'Description', 'Amount']}
                rows={ledger.map((entry) => [
                  new Date(entry.created_at).toLocaleString(),
                  <Badge key={entry.id} className={entryClass[entry.entry_type]}>
                    {entry.entry_type}
                  </Badge>,
                  entry.description,
                  entry.amount,
                ])}
              />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <p className="text-sm text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function Badge({ className, children }: { className: string; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium ${className}`}>
      {children}
    </span>
  );
}

function Table({ headers, rows }: { headers: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-zinc-500">
            {headers.map((header) => (
              <th key={header} className="px-3 py-2 font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="px-3 py-6 text-center text-zinc-500" colSpan={headers.length}>
                No records yet
              </td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr key={index} className="border-b border-zinc-100">
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="px-3 py-3 align-middle">
                    {cell}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
