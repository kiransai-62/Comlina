'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Instagram, 
  Plus, 
  Check, 
  RefreshCw, 
  Lock, 
  ArrowRight, 
  Zap,
  BarChart2,
  X,
  ShieldCheck,
  AlertCircle,
  Copy
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { instagramApi } from '@/features/instagram/api';
import { ConnectedInstagramAccount } from '@/features/instagram/types';
import { BrandLogo } from '@/components/BrandLogo';
import { MovingArrowConnector } from '@/components/MovingArrowConnector';
import { authService } from '@/lib/auth';

function BookIcon({ size = 18, className = '' }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  );
}

function InfoIcon({ size = 15, className = '' }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}

export default function InstagramAccountsPage() {
  const showToast = useUIStore((s) => s.showToast);

  const { data: accounts = [], isLoading, isError, error, refetch } = useQuery<ConnectedInstagramAccount[]>({
    queryKey: ['instagram-accounts'],
    queryFn: () => instagramApi.listAccounts(),
  });

  // Connect Instagram Modal
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);
  const [connectStep, setConnectStep] = useState(1);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [copiedRedirect, setCopiedRedirect] = useState(false);

  // Guide Modal
  const [isGuideModalOpen, setIsGuideModalOpen] = useState(false);

  const handleDisconnect = async (id: string) => {
    if (confirm('Are you sure you want to disconnect this Instagram account? Active automations on this account will stop running.')) {
      try {
        await instagramApi.disconnect(id);
        showToast('Instagram account disconnected.');
        refetch();
      } catch (err: any) {
        showToast(`Failed to disconnect: ${err.message || err}`);
      }
    }
  };

  const handleStartConnect = () => {
    setConnectStep(1);
    setIsAuthorizing(false);
    setIsConnectModalOpen(true);
  };

  const handleAuthorizeMeta = async () => {
    setIsAuthorizing(true);
    try {
      const redirectUri = typeof window !== 'undefined' ? `${window.location.origin}/connect/instagram` : undefined;
      const resp = await instagramApi.getConnectUrl(redirectUri);
      if (resp?.authorization_url) {
        window.location.href = resp.authorization_url;
      } else {
        throw new Error('No authorization URL returned from backend');
      }
    } catch (err: any) {
      showToast(`Failed to initialize Meta OAuth: ${err.message || err}`);
      setIsAuthorizing(false);
    }
  };

  const [syncingId, setSyncingId] = useState<string | null>(null);

  const handleSync = async (id: string) => {
    setSyncingId(id);
    try {
      await instagramApi.syncAccount(id);
      showToast('Real-time profile and follower data successfully synced from Meta.');
      refetch();
    } catch (err: any) {
      showToast(`Failed to sync account: ${err.message || err}`);
    } finally {
      setSyncingId(null);
    }
  };

  const hasAccounts = accounts.length > 0;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* ── Page Header ── */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#111110] tracking-tight">Instagram Accounts</h1>
          <p className="text-sm text-[#70706B] mt-1">
            Connect and manage your Instagram accounts via official Meta Graph API.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsGuideModalOpen(true)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#70706B] hover:text-[#111110] cursor-pointer"
          >
            <InfoIcon size={15} />
            <span>Learn more</span>
          </button>

          {hasAccounts && (
            <button
              onClick={handleStartConnect}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
            >
              <Plus size={15} />
              <span>Connect Another Account</span>
            </button>
          )}
        </div>
      </div>

      {/* ── Loading state ── */}
      {isLoading && (
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-8 shadow-sm animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-100 rounded w-2/3" />
        </div>
      )}

      {/* ── Error state ── */}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center text-red-900 space-y-3">
          <AlertCircle size={28} className="mx-auto text-red-600" />
          <div className="text-sm font-semibold">Failed to connect to backend service</div>
          <p className="text-xs text-red-700 max-w-sm mx-auto">
            {(error as any)?.message || 'Unable to retrieve connected Instagram accounts. Please verify backend server status.'}
          </p>
          <button
            onClick={async () => {
              await authService.refreshToken();
              refetch();
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all cursor-pointer mx-auto"
          >
            <RefreshCw size={14} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {/* ── EMPTY STATE ── */}
      {!isLoading && !isError && !hasAccounts && (
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-16 text-center shadow-sm">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888] text-white flex items-center justify-center shadow-lg shadow-pink-500/20">
              <Instagram size={40} strokeWidth={2.1} />
            </div>
          </div>

          <h2 className="text-xl font-bold text-[#111110]">No Instagram accounts connected</h2>
          <p className="text-sm text-[#70706B] max-w-md mx-auto mt-2 mb-7 leading-relaxed">
            Connect your Instagram Business or Creator account to start automating comment responses and sending private DMs.
          </p>

          <div className="flex items-center justify-center">
            <button
              onClick={handleStartConnect}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-sm font-semibold rounded-lg shadow-md transition-all cursor-pointer"
            >
              <Plus size={16} />
              <span>Connect Instagram</span>
            </button>
          </div>
        </div>
      )}

      {/* ── CONNECTED STATE ── */}
      {!isLoading && !isError && hasAccounts && (
        <div className="space-y-4">
          {accounts.map((acc: any) => {
            const handle = acc.username?.startsWith('@') ? acc.username : `@${acc.username || 'creator'}`;
            const initials = (acc.username || 'IG').slice(0, 2).toUpperCase();
            const followers = acc.follower_count ?? acc.followers ?? 0;
            const connectedDate = acc.connected_at
              ? new Date(acc.connected_at).toLocaleDateString()
              : 'Recently connected';
            const isActive = acc.is_active ?? acc.isActive ?? true;
            const tokenExpiry = acc.token_expires_at
              ? new Date(acc.token_expires_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'Long-lived';

            return (
              <div key={acc.id} className="bg-white border border-[#ECECE8] rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      {acc.profile_pic_url ? (
                        <img
                          src={acc.profile_pic_url}
                          alt={handle}
                          className="w-13 h-13 rounded-full object-cover border border-[#ECECE8]"
                        />
                      ) : (
                        <div className="w-13 h-13 rounded-full bg-[#111110] text-white flex items-center justify-center font-bold text-base">
                          {initials}
                        </div>
                      )}
                      <div className="absolute -bottom-0.5 -right-0.5 w-5 h-5 rounded-full bg-gradient-to-tr from-[#f09433] to-[#bc1888] flex items-center justify-center border-2 border-white">
                        <Instagram size={10} className="text-white" strokeWidth={2.5} />
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="font-bold text-base text-[#111110]">{handle}</span>
                        {isActive ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-[#EAF6EE] text-[#15803D] rounded-full text-xs font-semibold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" />
                            Connected
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-[#FEF2F2] text-[#DC2626] border border-[#FEE2E2] rounded-full text-xs font-semibold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626]" />
                            Reconnect
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-[#70706B] mt-1 flex items-center gap-2 flex-wrap">
                        <span>{acc.account_type || 'Business Account'}</span>
                        <span>•</span>
                        <span>{typeof followers === 'number' ? followers.toLocaleString() : followers} followers</span>
                        <span>•</span>
                        <span>Connected: {connectedDate}</span>
                        <span>•</span>
                        <span>Token expires: {tokenExpiry}</span>
                        <span>•</span>
                        {isActive ? (
                          <span className="text-[#15803D] font-medium">Active (Meta Graph v21.0)</span>
                        ) : (
                          <span className="text-[#DC2626] font-medium">Inactive (Reconnect required)</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 flex-wrap">
                    <button
                      type="button"
                      disabled={syncingId === acc.id}
                      onClick={() => handleSync(acc.id)}
                      className="inline-flex items-center gap-1.5 text-xs text-[#064125] bg-[#EAF6EE] hover:bg-[#D4EDDA] font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                    >
                      <RefreshCw size={12} className={syncingId === acc.id ? 'animate-spin' : ''} />
                      <span>{syncingId === acc.id ? 'Syncing...' : 'Sync Real-Time Data'}</span>
                    </button>
                    {!isActive && (
                      <button
                        type="button"
                        onClick={handleStartConnect}
                        className="text-xs bg-[#062E1A] hover:bg-[#0A4A2A] text-white font-semibold px-3.5 py-1.5 rounded-lg shadow-2xs transition-colors cursor-pointer"
                      >
                        Reconnect
                      </button>
                    )}
                    <button
                      onClick={() => handleDisconnect(acc.id)}
                      className="text-xs text-[#DC2626] hover:bg-[#FEF2F2] border border-[#FEE2E2] font-medium px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Bottom Callout Banner ── */}
      <div className="bg-white border border-[#E0E7FF] rounded-xl p-4.5 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-9 h-9 rounded-lg bg-[#EEF2FF] flex items-center justify-center text-[#4F46E5] shrink-0">
            <BookIcon size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold text-[#111110]">
              Don't have a Business or Creator account?
            </div>
            <div className="text-xs text-[#70706B] mt-0.5">
              It's free and only takes a few minutes to switch from a personal account.
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsGuideModalOpen(true)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#4F46E5] hover:underline cursor-pointer"
        >
          <span>Learn how</span>
          <ArrowRight size={13} />
        </button>
      </div>

      {/* ── Screen 3: CONNECT INSTAGRAM MODAL ── */}
      {isConnectModalOpen && (
        <div className="fixed inset-0 bg-[#111110]/55 backdrop-blur-xs flex items-center justify-center p-5 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-[#ECECE8] shadow-2xl w-full max-w-3xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-7 py-5 border-b border-[#ECECE8] bg-[#FAFAF8]">
              <div>
                <h2 className="text-lg font-bold text-[#111110]">Connect Instagram</h2>
                <p className="text-xs text-[#70706B] mt-0.5">
                  Follow the steps to securely connect your Instagram account.
                </p>
              </div>
              <button
                onClick={() => !isAuthorizing && setIsConnectModalOpen(false)}
                disabled={isAuthorizing}
                className="text-[#9E9E96] hover:text-[#111110] p-1 cursor-pointer disabled:opacity-50"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] min-h-[380px]">
              {/* Stepper (Desktop/Tablet) */}
              <div className="hidden md:block bg-[#FAFAF8] border-r border-[#ECECE8] p-7 space-y-8">
                <div className="flex gap-3.5 items-start">
                  <div className="w-7 h-7 rounded-full bg-[#062E1A] text-white flex items-center justify-center text-xs font-bold shrink-0">
                    1
                  </div>
                  <div>
                    <div className="text-sm font-bold text-[#111110]">Login with Meta</div>
                    <div className="text-xs text-[#70706B] mt-0.5 leading-snug">
                      Redirect to Meta's official OAuth dialog.
                    </div>
                  </div>
                </div>

                <div className="flex gap-3.5 items-start">
                  <div className="w-7 h-7 rounded-full bg-gray-200 text-gray-500 flex items-center justify-center text-xs font-bold shrink-0">
                    2
                  </div>
                  <div>
                    <div className="text-sm font-bold text-[#111110]">Grant Permissions</div>
                    <div className="text-xs text-[#70706B] mt-0.5 leading-snug">
                      Select your Instagram Professional page.
                    </div>
                  </div>
                </div>

                <div className="flex gap-3.5 items-start">
                  <div className="w-7 h-7 rounded-full bg-gray-200 text-gray-500 flex items-center justify-center text-xs font-bold shrink-0">
                    3
                  </div>
                  <div>
                    <div className="text-sm font-bold text-[#111110]">Connected</div>
                    <div className="text-xs text-[#70706B] mt-0.5 leading-snug">
                      Start building automations right away.
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Side: Meta Auth Card */}
              <div className="p-8 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-3.5 mb-5">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-[#f09433] to-[#bc1888] flex items-center justify-center shadow-md shadow-pink-500/20">
                      <Instagram size={22} className="text-white" strokeWidth={2.2} />
                    </div>
                    <MovingArrowConnector />
                    <div className="w-11 h-11 rounded-xl bg-white border border-[#ECECE8] flex items-center justify-center shadow-md p-1">
                      <BrandLogo variant="mark" height={34} />
                    </div>
                  </div>

                  <h3 className="text-lg font-bold text-[#111110]">Connect with Instagram</h3>
                  <p className="text-xs text-[#70706B] mt-1 leading-relaxed mb-6">
                    Securely connect your Instagram Business or Creator account using Meta OAuth. We only request the permissions needed for your automations.
                  </p>

                  <div className="space-y-3.5 mb-6">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shrink-0">
                        <Zap size={14} />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-[#111110]">Safe & Secure OAuth</div>
                        <div className="text-[11.5px] text-[#70706B]">Tokens are encrypted with AES-256 in PostgreSQL.</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg bg-[#EEF2FF] text-[#4F46E5] flex items-center justify-center shrink-0">
                        <BarChart2 size={14} />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-[#111110]">Read & Respond</div>
                        <div className="text-[11.5px] text-[#70706B]">Manage comment replies and DM automation flows.</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2.5">
                  <button
                    onClick={handleAuthorizeMeta}
                    disabled={isAuthorizing}
                    className="w-full py-3 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-sm flex items-center justify-center gap-2 cursor-pointer transition-all disabled:opacity-80"
                  >
                    {isAuthorizing ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        <span>Redirecting to Meta OAuth...</span>
                      </>
                    ) : (
                      <>
                        <Instagram size={15} />
                        <span>Continue to Meta Login →</span>
                      </>
                    )}
                  </button>



                  <div className="bg-[#F8F9FA] border border-[#ECECE8] rounded-xl p-3 text-left space-y-2 mt-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-[#111110]">Meta Redirect URI</span>
                      <button
                        type="button"
                        onClick={() => {
                          const url = `${window.location.origin}/connect/instagram`;
                          navigator.clipboard.writeText(url);
                          setCopiedRedirect(true);
                          setTimeout(() => setCopiedRedirect(false), 2000);
                        }}
                        className="inline-flex items-center gap-1 text-[11px] text-[#062E1A] font-medium hover:underline cursor-pointer"
                      >
                        {copiedRedirect ? (
                          <>
                            <Check size={11} className="text-[#15803D]" />
                            <span className="text-[#15803D]">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={11} />
                            <span>Copy URI</span>
                          </>
                        )}
                      </button>
                    </div>
                    <code className="block text-[11px] bg-white border border-[#E5E5E0] px-2 py-1 rounded text-[#555] font-mono select-all truncate">
                      {typeof window !== 'undefined' ? `${window.location.origin}/connect/instagram` : 'http://localhost:3000/connect/instagram'}
                    </code>
                    <p className="text-[10.5px] text-[#70706B] leading-tight">
                      Must be whitelisted in <b>Meta Developer Dashboard &gt; Instagram &gt; Valid OAuth Redirect URIs</b> to authorize real Instagram accounts.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Switch to Creator / Business Guide Modal ── */}
      {isGuideModalOpen && (
        <div className="fixed inset-0 bg-[#111110]/55 backdrop-blur-xs flex items-center justify-center p-5 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-md w-full p-7 shadow-2xl border border-[#ECECE8]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#EEF2FF] text-[#4F46E5] flex items-center justify-center">
                  <BookIcon size={16} />
                </div>
                <h3 className="text-base font-bold text-[#111110]">How to Switch to a Professional Account</h3>
              </div>
              <button
                onClick={() => setIsGuideModalOpen(false)}
                className="text-[#9E9E96] hover:text-[#111110] cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-[#70706B] leading-relaxed mb-5">
              Meta requires accounts to be a <strong>Creator</strong> or <strong>Business</strong> account to send automated DMs and reply to comments. It is 100% free and takes under a minute.
            </p>

            <div className="space-y-3 mb-6 text-xs">
              <div className="flex gap-2.5">
                <span className="font-bold text-[#15803D]">1.</span>
                <span className="text-[#333330]">Open Instagram App → Go to your Profile → Tap Menu (☰) → <strong>Settings and privacy</strong>.</span>
              </div>
              <div className="flex gap-2.5">
                <span className="font-bold text-[#15803D]">2.</span>
                <span className="text-[#333330]">Scroll down to <strong>For professionals</strong> and tap <strong>Account type and tools</strong>.</span>
              </div>
              <div className="flex gap-2.5">
                <span className="font-bold text-[#15803D]">3.</span>
                <span className="text-[#333330]">Tap <strong>Switch to professional account</strong> and choose <strong>Creator</strong> or <strong>Business</strong>.</span>
              </div>
              <div className="flex gap-2.5">
                <span className="font-bold text-[#15803D]">4.</span>
                <span className="text-[#333330]">Return here to Comlina and click <strong>Connect Instagram</strong>!</span>
              </div>
            </div>

            <button
              onClick={() => {
                setIsGuideModalOpen(false);
                handleStartConnect();
              }}
              className="w-full py-2.5 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg cursor-pointer transition-all"
            >
              Got it, Connect Instagram
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
