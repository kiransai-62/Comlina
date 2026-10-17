// client/src/components/billing/UpgradeModal.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  X, 
  Check, 
  Sparkles, 
  Crown, 
  ShieldCheck, 
  Lock, 
  ArrowRight, 
  Loader2,
  ExternalLink
} from 'lucide-react';
import { usePlan, usePlanStore } from '@/hooks/usePlan';
import { PlanTier, PLAN_CONFIGS, FEATURE_CATALOG } from '@/lib/plans';
import { PlanBadge } from './PlanBadge';
import { api } from '@/lib/api';

declare global {
  interface Window {
    Razorpay?: any;
  }
}

export function UpgradeModal() {
  const {
    upgradeModalOpen,
    targetTier: initialTargetTier,
    lockedFeatureKey,
    closeUpgradeModal,
    planTier: currentTier,
    fetchUsage,
  } = usePlan();

  const [selectedTier, setSelectedTier] = useState<PlanTier>(
    initialTargetTier === 'PRO' ? 'PRO' : 'PREMIUM'
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (initialTargetTier) {
      setSelectedTier(initialTargetTier === 'PRO' ? 'PRO' : 'PREMIUM');
    }
  }, [initialTargetTier]);

  // Load Razorpay script dynamically
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (document.getElementById('razorpay-checkout-script')) return;

    const script = document.createElement('script');
    script.id = 'razorpay-checkout-script';
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
  }, []);

  if (!upgradeModalOpen) return null;

  const currentPlanConfig = PLAN_CONFIGS[currentTier];
  const targetPlanConfig = PLAN_CONFIGS[selectedTier];
  const lockedFeature = lockedFeatureKey 
    ? FEATURE_CATALOG.find((f) => f.key === lockedFeatureKey) 
    : null;

  const handleCheckout = async () => {
    setIsProcessing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      // 1. Create server-side Razorpay order
      const orderData = await api.post<any>('/payments/razorpay/create-order', {
        plan_tier: selectedTier,
      });

      if (!orderData || !orderData.order_id) {
        throw new Error('Failed to create payment order. Please try again.');
      }

      const { order_id, amount_paise, currency, key_id } = orderData;
      const razorpayKey = key_id || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID;

      // 2. Open Razorpay Checkout modal if loaded
      if (typeof window !== 'undefined' && window.Razorpay && razorpayKey) {
        const rzp = new window.Razorpay({
          key: razorpayKey,
          amount: amount_paise,
          currency: currency || 'INR',
          name: 'Comlina',
          description: `${targetPlanConfig.name} Plan Subscription`,
          order_id: order_id,
          image: '/logo.png',
          handler: async (response: any) => {
            try {
              // 3. Verify payment signature on backend
              const verifyRes = await api.post<any>('/payments/razorpay/verify-payment', {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              });

              if (verifyRes && verifyRes.status === 'SUCCESS') {
                setSuccessMessage(`Congratulations! Upgraded to ${targetPlanConfig.name} plan.`);
                await fetchUsage();
                setTimeout(() => {
                  closeUpgradeModal();
                }, 1500);
              } else {
                throw new Error('Payment signature verification failed.');
              }
            } catch (err: any) {
              setErrorMessage(err.message || 'Payment verification failed.');
            } finally {
              setIsProcessing(false);
            }
          },
          prefill: {
            name: 'Comlina Creator',
            email: 'creator@comlina.com',
          },
          theme: {
            color: '#0066FF',
          },
          modal: {
            ondismiss: () => {
              setIsProcessing(false);
            },
          },
        });
        rzp.open();
      } else {
        // Fallback in dev/sandbox if Razorpay checkout script is offline or in sandbox
        const simulatedPaymentId = `pay_sim_${Date.now()}`;
        const verifyRes = await api.post<any>('/payments/razorpay/verify-payment', {
          razorpay_order_id: order_id,
          razorpay_payment_id: simulatedPaymentId,
          razorpay_signature: `sig_test_${simulatedPaymentId}`,
        });

        if (verifyRes && verifyRes.status === 'SUCCESS') {
          setSuccessMessage(`Simulated payment verified! Upgraded to ${targetPlanConfig.name}.`);
          await fetchUsage();
          setTimeout(() => {
            closeUpgradeModal();
          }, 1500);
        } else {
          throw new Error('Failed to complete simulated payment verification.');
        }
      }
    } catch (err: any) {
      console.error('Upgrade checkout error:', err);
      setErrorMessage(err.message || 'An error occurred while initiating payment.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto animate-in fade-in duration-200"
      onClick={closeUpgradeModal}
    >
      <div 
        className="relative w-full max-w-xl bg-white rounded-3xl shadow-2xl border border-[#ECECE8] p-6 sm:p-8 space-y-6 animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={closeUpgradeModal}
          className="absolute top-5 right-5 p-2 rounded-xl text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] transition-colors cursor-pointer"
          aria-label="Close upgrade modal"
        >
          <X size={20} />
        </button>

        {/* Feature Lock Notice (if triggered by a specific feature) */}
        {lockedFeature && (
          <div className="p-3.5 bg-[#EFF6FF] border border-[#BFDBFE] rounded-2xl flex items-center gap-3">
            <div className="p-2 bg-blue-100 text-[#0066FF] rounded-xl shrink-0">
              <Lock size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-[#1E40AF] flex items-center gap-2">
                <span>Unlock {lockedFeature.name}</span>
                <PlanBadge tier={lockedFeature.requiredTier} size="xs" />
              </div>
              <p className="text-[11px] text-[#1E3A8A] truncate mt-0.5">
                {lockedFeature.description}
              </p>
            </div>
          </div>
        )}

        {/* Header */}
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#EAF6EE] text-[#064125] border border-[#C5E7D1] mb-2">
            <Sparkles size={13} className="text-[#15803D]" />
            <span>Supercharge Your Growth</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#111110] tracking-tight">
            Choose Your Growth Plan
          </h2>
          <p className="text-xs sm:text-sm text-[#70706B] mt-1">
            Turn every Instagram comment into revenue, email leads, and booked calls.
          </p>
        </div>

        {/* Plan Switcher Pills */}
        <div className="grid grid-cols-2 gap-2 p-1.5 bg-[#F4F4F1] rounded-2xl">
          <button
            type="button"
            onClick={() => setSelectedTier('PREMIUM')}
            className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              selectedTier === 'PREMIUM'
                ? 'bg-white text-[#111110] shadow-xs'
                : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            <Crown size={14} className={selectedTier === 'PREMIUM' ? 'text-[#D97706]' : 'text-gray-400'} />
            <span>Premium (₹199/mo)</span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedTier('PRO')}
            className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              selectedTier === 'PRO'
                ? 'bg-white text-[#111110] shadow-xs'
                : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            <Sparkles size={14} className={selectedTier === 'PRO' ? 'text-[#6366F1]' : 'text-gray-400'} />
            <span>Pro (₹399/mo)</span>
          </button>
        </div>

        {/* Target Plan Details Card */}
        <div className="p-5 sm:p-6 bg-[#FAFAFA] border border-[#ECECE8] rounded-2xl space-y-4">
          <div className="flex items-baseline justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-black text-[#111110]">
                  {targetPlanConfig.name}
                </h3>
                <PlanBadge tier={selectedTier} size="xs" />
              </div>
              <p className="text-xs text-[#70706B] mt-0.5">
                {targetPlanConfig.tagline}
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl sm:text-3xl font-black text-[#111110]">
                ₹{targetPlanConfig.priceInr}
              </div>
              <div className="text-[11px] text-[#70706B]">per month</div>
            </div>
          </div>

          <div className="border-t border-[#ECECE8] pt-4">
            <div className="text-xs font-bold text-[#111110] uppercase tracking-wider mb-2.5">
              Included in this plan:
            </div>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {targetPlanConfig.highlights.map((highlight, idx) => (
                <li key={idx} className="flex items-center gap-2 text-xs text-[#333330]">
                  <Check size={14} className="text-[#15803D] shrink-0" />
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Error / Success Alerts */}
        {errorMessage && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
            {errorMessage}
          </div>
        )}

        {successMessage && (
          <div className="p-3 bg-green-50 border border-green-200 text-green-700 text-xs font-semibold rounded-xl flex items-center gap-2">
            <Check size={16} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Checkout CTA */}
        <div className="space-y-3">
          <button
            type="button"
            disabled={isProcessing || currentTier === selectedTier}
            onClick={handleCheckout}
            className={`w-full py-3.5 px-4 rounded-xl text-sm font-bold text-white transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer ${
              currentTier === selectedTier
                ? 'bg-gray-400 cursor-not-allowed'
                : selectedTier === 'PRO'
                ? 'bg-[#4338CA] hover:bg-[#3730A3] active:scale-[0.99]'
                : 'bg-[#0066FF] hover:bg-[#0052CC] active:scale-[0.99]'
            }`}
          >
            {isProcessing ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Processing Order...</span>
              </>
            ) : currentTier === selectedTier ? (
              <span>Your Current Plan</span>
            ) : (
              <>
                <span>Upgrade to {targetPlanConfig.name} — ₹{targetPlanConfig.priceInr}/month</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>

          <div className="flex items-center justify-center gap-2 text-[11px] text-[#70706B]">
            <ShieldCheck size={14} className="text-[#15803D]" />
            <span>256-bit encrypted checkout • Powered by Razorpay • Cancel anytime</span>
          </div>
        </div>
      </div>
    </div>
  );
}
