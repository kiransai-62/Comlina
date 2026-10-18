'use client';

import React, { useEffect, useState, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, AlertCircle, Loader2, ShieldCheck } from 'lucide-react';
import { instagramApi } from '@/features/instagram/api';
import { ComlinaLoadingOverlay } from '@/components/ComlinaLoadingOverlay';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [isRetrying, setIsRetrying] = useState<boolean>(false);
  const [isConnectingDev, setIsConnectingDev] = useState<boolean>(false);
  const exchangeAttemptedRef = useRef<boolean>(false);

  useEffect(() => {
    const errorParam = searchParams.get('error') || searchParams.get('error_message') || searchParams.get('message');
    const errorReason = searchParams.get('error_description') || searchParams.get('error_reason');
    if (errorParam) {
      setStatus('error');
      setErrorMessage(errorReason || errorParam || 'Meta OAuth access was denied or cancelled.');
      return;
    }

    let code = searchParams.get('code');
    const state = searchParams.get('state');
    if (!code) {
      setStatus('error');
      setErrorMessage('No valid authorization code was returned from Meta.');
      return;
    }

    // Prevent double execution in React 18 Strict Mode
    if (exchangeAttemptedRef.current) return;
    exchangeAttemptedRef.current = true;

    // Instagram often appends #_ to the redirect URI
    if (code.endsWith('#_')) {
      code = code.slice(0, -2);
    }

    const redirectUri = window.location.origin + '/connect/instagram';

    instagramApi.callback(code, state || undefined, redirectUri)
      .then(() => {
        setStatus('success');
        setTimeout(() => router.push('/dashboard/instagram-accounts'), 1500);
      })
      .catch((err) => {
        console.error('OAuth exchange error:', err);
        setStatus('error');
        setErrorMessage(err.message || 'Failed to exchange authorization code with Meta.');
      });
  }, [searchParams, router]);

  return (
    <div className="bg-white border border-[#ECECE8] rounded-2xl p-8 max-w-md w-full text-center shadow-lg">
      {status === 'loading' && (
        <ComlinaLoadingOverlay isLoading={true} />
      )}

      {status === 'success' && (
        <div className="space-y-4">
          <CheckCircle className="w-10 h-10 text-[#15803D] mx-auto" />
          <h2 className="font-bold text-base text-[#111110]">Account Successfully Connected!</h2>
          <p className="text-xs text-[#70706B]">Redirecting to your dashboard...</p>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-4">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" strokeWidth={1.75} />
          <h2 className="font-bold text-base text-[#111110]">
            {errorMessage.toLowerCase().includes('already') ? 'Instagram Account Already Registered' : 'Connection Failed'}
          </h2>
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 leading-relaxed font-medium text-left break-words">
            {errorMessage || 'Failed to exchange authorization code with Meta.'}
          </div>
          <p className="text-xs text-[#70706B] leading-relaxed">
            {errorMessage.toLowerCase().includes('already') 
              ? 'To protect account integrity, each Instagram account can only be linked to the initial Google or email account used for registration. Please sign in with your original account.'
              : 'A Business or Creator Instagram account is required.'}
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-2">
            {errorMessage.toLowerCase().includes('already') ? (
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="w-full sm:w-auto px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
              >
                Sign In with Original Account
              </button>
            ) : (
              <button
                type="button"
                disabled={isRetrying}
                onClick={async () => {
                  setIsRetrying(true);
                  try {
                    const redirectUri = window.location.origin + '/connect/instagram';
                    const resp = await instagramApi.getConnectUrl(redirectUri);
                    if (resp?.authorization_url) {
                      window.location.href = resp.authorization_url;
                    } else {
                      router.push('/dashboard/instagram-accounts');
                    }
                  } catch {
                    router.push('/dashboard/instagram-accounts');
                  }
                }}
                className="w-full sm:w-auto px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-75 flex items-center justify-center gap-1.5"
              >
                {isRetrying && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Try again</span>
              </button>
            )}

            {process.env.NODE_ENV === 'development' && !errorMessage.toLowerCase().includes('already') && (
              <button
                type="button"
                disabled={isConnectingDev}
                onClick={async () => {
                  try {
                    setIsConnectingDev(true);
                    await instagramApi.connectDevAccount();
                    setStatus('success');
                    setTimeout(() => router.push('/dashboard/instagram-accounts'), 1200);
                  } catch (devErr: any) {
                    setIsConnectingDev(false);
                    setErrorMessage(devErr.message || 'Failed to connect dev account.');
                  }
                }}
                className="w-full sm:w-auto px-4 py-2 bg-[#15803D] hover:bg-[#166534] text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-75 flex items-center justify-center gap-1.5"
              >
                {isConnectingDev ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
                <span>Dev Account</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => router.push('/dashboard/instagram-accounts')}
              className="w-full sm:w-auto px-4 py-2 bg-white border border-[#ECECE8] hover:bg-[#F9F9F8] text-[#111110] text-xs font-semibold rounded-lg shadow-2xs transition-all cursor-pointer"
            >
              Back to Accounts
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ConnectInstagramCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FBFBFA] p-6">
      <Suspense fallback={
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-8 max-w-md w-full text-center shadow-lg">
          <Loader2 className="w-10 h-10 text-[#15803D] animate-spin mx-auto" />
          <h2 className="font-bold text-base text-[#111110]">Loading...</h2>
        </div>
      }>
        <CallbackContent />
      </Suspense>
    </div>
  );
}
