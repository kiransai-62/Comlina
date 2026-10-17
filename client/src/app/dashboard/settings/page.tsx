'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { 
  User,
  CreditCard,
  Download,
  Trash2,
  Check,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Instagram,
  Copy,
  Eye,
  RefreshCw,
  Plus,
  ArrowUpRight,
  Sparkles,
  HelpCircle,
  Shield,
  LogOut,
  ChevronRight,
  X,
  Lock,
  Mail,
  Zap,
  Clock,
  MessageSquare,
  FileText
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { authService } from '@/lib/auth';
import { instagramApi } from '@/features/instagram/api';
import { ConnectedInstagramAccount } from '@/features/instagram/types';
import { usePlan } from '@/hooks/usePlan';
import { PlanBadge } from '@/components/billing/PlanBadge';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { triggerPwaPrompt } from '@/features/pwa';

type TabType = 'general' | 'notifications' | 'billing' | 'danger';

export default function SettingsPage() {
  const showToast = useUIStore((s) => s.showToast);
  const [activeTab, setActiveTab] = useState<TabType>('general');
  const [toastAlert, setToastAlert] = useState<string | null>(null);
  const { planTier, planConfig, usage, fetchUsage, openUpgradeModal, switchPlanDev } = usePlan();

  useEffect(() => {
    fetchUsage();
  }, []);

  // Profile Information state
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [workspaceName, setWorkspaceName] = useState('Personal Workspace');
  const [timezone, setTimezone] = useState('(GMT+05:30) India Standard Time');
  const [language, setLanguage] = useState('English');

  // Automation Preferences Toggles
  const [followCheck, setFollowCheck] = useState(true);
  const [publicReply, setPublicReply] = useState(false);
  const [stopDuplicate, setStopDuplicate] = useState(true);

  // Notification Toggles
  const [notifyLead, setNotifyLead] = useState(true);
  const [notifyToken, setNotifyToken] = useState(true);
  const [notifyDigest, setNotifyDigest] = useState(true);
  const [notifyRate, setNotifyRate] = useState(true);

  // Modals & Popups
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const triggerToast = (msg: string) => {
    setToastAlert(msg);
    showToast(msg);
    setTimeout(() => setToastAlert(null), 3000);
  };

  useEffect(() => {
    async function loadUser() {
      const u = await authService.getUser();
      if (u) {
        if (u.fullName) setFullName(u.fullName);
        if (u.email) setEmail(u.email);
      } else {
        setFullName('Creator');
        setEmail('');
      }
    }
    loadUser();
  }, []);

  const { data: connectedAccounts = [] } = useQuery<ConnectedInstagramAccount[]>({
    queryKey: ['instagram-accounts'],
    queryFn: () => instagramApi.listAccounts(),
  });

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    triggerToast(`${label} copied to clipboard!`);
  };

  return (
    <div className="max-w-[1440px] mx-auto space-y-6 pb-16">
      <UpgradeModal />
      
      {/* Floating Toast */}
      {toastAlert && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 bg-[#111110] text-white rounded-xl shadow-xl border border-white/10 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <CheckCircle size={17} className="text-[#22C55E]" />
          <span className="text-xs font-medium">{toastAlert}</span>
          <button onClick={() => setToastAlert(null)} className="text-white/60 hover:text-white ml-2">
            <X size={14} />
          </button>
        </div>
      )}

      {/* ── Top Header Title Section (matching exact Accounts & Analytics breadcrumb style) ── */}
      <div>
        <div className="text-[11px] font-bold text-[#70706B] tracking-wider uppercase mb-1">
          SETTINGS
        </div>
        <h1 className="text-2xl lg:text-[28px] font-extrabold text-[#111110] tracking-tight">
          Settings
        </h1>
        <p className="text-xs lg:text-sm text-[#70706B] mt-1">
          Manage your account, preferences and application settings.
        </p>
      </div>

      {/* ── Clean Horizontal Tabs ── */}
      <div className="flex items-center gap-6 border-b border-[#ECECE8] overflow-x-auto scrollbar-none text-xs font-semibold">
        {[
          { key: 'general', label: 'General' },
          { key: 'notifications', label: 'Notifications' },
          { key: 'billing', label: 'Billing' },
          { key: 'danger', label: 'Danger Zone', danger: true },
        ].map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabType)}
              className={`pb-3 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? tab.danger
                    ? 'border-[#DC2626] text-[#DC2626]'
                    : 'border-[#15803D] text-[#064125]'
                  : 'border-transparent text-[#70706B] hover:text-[#111110]'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ── TAB 1: GENERAL (The Exact 2-Column Redesign Matching User Screenshot) ── */}
      {activeTab === 'general' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column (~65% = 8 cols) */}
          <div className="lg:col-span-8 space-y-6">

            {/* 1. Profile Information */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-2xs">
              <div className="mb-5">
                <h2 className="text-sm font-bold text-[#111110]">Profile Information</h2>
                <p className="text-xs text-[#70706B] mt-0.5">
                  This information will be used across your workspace.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-start gap-6 pb-2">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-[#111110] text-white flex items-center justify-center font-bold text-base shadow-xs shrink-0">
                    KS
                  </div>
                  <button
                    type="button"
                    onClick={() => triggerToast('Avatar change dialog opened')}
                    className="px-3.5 py-1.5 bg-white border border-[#ECECE8] hover:bg-[#F9F9F8] text-[#111110] text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
                  >
                    Change Photo
                  </button>
                </div>

                <div className="w-full sm:flex-1 space-y-3.5">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                    <label className="w-24 text-xs text-[#70706B] font-medium shrink-0">Name</label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full flex-1 px-3.5 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-lg text-xs text-[#111110] font-medium focus:bg-white focus:border-[#15803D] outline-none transition-all shadow-2xs"
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                    <label className="w-24 text-xs text-[#70706B] font-medium shrink-0">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full flex-1 px-3.5 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-lg text-xs text-[#111110] font-medium focus:bg-white focus:border-[#15803D] outline-none transition-all shadow-2xs"
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                    <label className="w-24 text-xs text-[#70706B] font-medium shrink-0">Phone (optional)</label>
                    <input
                      type="text"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="w-full flex-1 px-3.5 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-lg text-xs text-[#111110] font-medium focus:bg-white focus:border-[#15803D] outline-none transition-all shadow-2xs"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-[#ECECE8] mt-4">
                <button
                  type="button"
                  onClick={() => triggerToast('Profile information saved!')}
                  className="px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-xs transition-all cursor-pointer"
                >
                  Save Profile
                </button>
              </div>
            </div>

            {/* 2. Workspace Settings */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-2xs">
              <div className="mb-5">
                <h2 className="text-sm font-bold text-[#111110]">Workspace Settings</h2>
                <p className="text-xs text-[#70706B] mt-0.5">
                  Manage your workspace preferences.
                </p>
              </div>

              <div className="space-y-3.5">
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                  <label className="w-32 text-xs text-[#70706B] font-medium shrink-0">Workspace Name</label>
                  <input
                    type="text"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    className="w-full flex-1 px-3.5 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-lg text-xs text-[#111110] font-medium focus:bg-white focus:border-[#15803D] outline-none transition-all shadow-2xs"
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                  <label className="w-32 text-xs text-[#70706B] font-medium shrink-0">Timezone</label>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full flex-1 px-3.5 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-lg text-xs text-[#111110] font-medium focus:bg-white focus:border-[#15803D] outline-none transition-all cursor-pointer shadow-2xs"
                  >
                    <option value="(GMT+05:30) India Standard Time">(GMT+05:30) India Standard Time</option>
                    <option value="(GMT-08:00) Pacific Time (US & Canada)">(GMT-08:00) Pacific Time (US & Canada)</option>
                    <option value="(GMT-05:00) Eastern Time (US & Canada)">(GMT-05:00) Eastern Time (US & Canada)</option>
                    <option value="(GMT+00:00) London, UTC">(GMT+00:00) London, UTC</option>
                    <option value="(GMT+04:00) Dubai, GST">(GMT+04:00) Dubai, GST</option>
                  </select>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                  <label className="w-32 text-xs text-[#70706B] font-medium shrink-0">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full flex-1 px-3.5 py-2 bg-[#FBFBFA] border border-[#ECECE8] rounded-lg text-xs text-[#111110] font-medium focus:bg-white focus:border-[#15803D] outline-none transition-all cursor-pointer shadow-2xs"
                  >
                    <option value="English">English</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="German">German</option>
                    <option value="Hindi">Hindi</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-[#ECECE8] mt-4">
                <button
                  type="button"
                  onClick={() => triggerToast('Workspace preferences updated!')}
                  className="px-4 py-2 bg-[#062E1A] hover:bg-[#0A4A2A] text-white text-xs font-semibold rounded-lg shadow-xs transition-all cursor-pointer"
                >
                  Update Workspace
                </button>
              </div>
            </div>

            {/* 3. Automation Preferences */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-2xs">
              <div className="mb-5">
                <h2 className="text-sm font-bold text-[#111110]">Automation Preferences</h2>
                <p className="text-xs text-[#70706B] mt-0.5">
                  Set default behavior for your automations.
                </p>
              </div>

              <div className="space-y-4 divide-y divide-[#ECECE8]">
                {/* Toggle 1: Default Follow Check */}
                <div className="flex items-center justify-between pt-3 first:pt-0">
                  <div>
                    <div className="text-xs font-bold text-[#111110]">Default Follow Check</div>
                    <div className="text-xs text-[#70706B] mt-0.5">
                      Check if the user follows before sending DM.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => { setFollowCheck(!followCheck); triggerToast(`Follow check ${!followCheck ? 'enabled' : 'disabled'}`); }}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out outline-none ${
                      followCheck ? 'bg-[#064125]' : 'bg-[#E0E0DA]'
                    }`}
                  >
                    <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      followCheck ? 'translate-x-5' : 'translate-x-0'
                    }`} />
                  </button>
                </div>

                {/* Toggle 2: Default Public Reply */}
                <div className="flex items-center justify-between pt-4">
                  <div>
                    <div className="text-xs font-bold text-[#111110]">Default Public Reply</div>
                    <div className="text-xs text-[#70706B] mt-0.5">
                      Enable public reply by default.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => { setPublicReply(!publicReply); triggerToast(`Public reply ${!publicReply ? 'enabled' : 'disabled'}`); }}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out outline-none ${
                      publicReply ? 'bg-[#064125]' : 'bg-[#E0E0DA]'
                    }`}
                  >
                    <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      publicReply ? 'translate-x-5' : 'translate-x-0'
                    }`} />
                  </button>
                </div>

                {/* Toggle 3: Stop on Duplicate */}
                <div className="flex items-center justify-between pt-4">
                  <div>
                    <div className="text-xs font-bold text-[#111110]">Stop on Duplicate</div>
                    <div className="text-xs text-[#70706B] mt-0.5">
                      Don't respond to the same user multiple times.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => { setStopDuplicate(!stopDuplicate); triggerToast(`Stop on duplicate ${!stopDuplicate ? 'enabled' : 'disabled'}`); }}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out outline-none ${
                      stopDuplicate ? 'bg-[#064125]' : 'bg-[#E0E0DA]'
                    }`}
                  >
                    <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      stopDuplicate ? 'translate-x-5' : 'translate-x-0'
                    }`} />
                  </button>
                </div>
              </div>
            </div>

            {/* 4. Data & Privacy */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-2xs">
              <div className="mb-5">
                <h2 className="text-sm font-bold text-[#111110]">Data & Privacy</h2>
                <p className="text-xs text-[#70706B] mt-0.5">
                  Manage your data and privacy settings.
                </p>
              </div>

              <div className="space-y-4 divide-y divide-[#ECECE8]">
                {/* Export Row */}
                <div className="flex items-center justify-between pt-2 first:pt-0">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#111110]">Export Your Data</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F4F4F1] text-[#70706B]">Coming soon</span>
                    </div>
                    <div className="text-xs text-[#70706B] mt-0.5">
                      Download a copy of your data (contacts, conversations, analytics).
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-[#ECECE8] opacity-50 cursor-not-allowed text-[#70706B] text-xs font-medium rounded-lg shadow-2xs"
                  >
                    <Download size={14} className="text-[#70706B]" />
                    <span>Export</span>
                  </button>
                </div>

                {/* Delete Account Row */}
                <div className="flex items-center justify-between pt-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#111110]">Delete Account</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEE2E2] text-[#DC2626]">Coming soon</span>
                    </div>
                    <div className="text-xs text-[#70706B] mt-0.5">
                      Permanently delete your account and all data.
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-[#ECECE8] text-[#70706B] opacity-50 cursor-not-allowed text-xs font-medium rounded-lg"
                  >
                    <Trash2 size={13} />
                    <span>Delete Account</span>
                  </button>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column (~35% = 4 cols) */}
          <div className="lg:col-span-4 space-y-6">

            {/* 1. Plan & Usage Card */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-2xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-[#111110]">Plan & Usage</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F4F4F1] text-[#70706B]">Coming soon</span>
              </div>
              <div className="text-sm font-bold text-[#111110]">Starter Plan</div>
              <div className="text-xs text-[#70706B] mt-0.5 mb-2">5 / 10 automations</div>
              <div className="w-full bg-[#ECECE8] h-2 rounded-full overflow-hidden mb-4">
                <div className="bg-[#064125] h-full w-1/2 rounded-full" />
              </div>
              <button
                type="button"
                disabled
                className="w-full py-2 bg-white border border-[#ECECE8] text-xs font-semibold text-[#70706B] rounded-lg text-center shadow-2xs flex items-center justify-center gap-1.5 opacity-50 cursor-not-allowed"
              >
                <ArrowUpRight size={14} />
                <span>Upgrade Plan (Coming soon)</span>
              </button>
            </div>

            {/* 2. Connected Integrations Card */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-2xs">
              <div className="text-xs font-bold text-[#111110]">Connected Integrations</div>
              <p className="text-xs text-[#70706B] mt-0.5 mb-3.5">Manage third-party integrations.</p>

              <div className="space-y-3">
                {/* Instagram Row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888] flex items-center justify-center text-white shrink-0 shadow-2xs">
                      <Instagram size={15} />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111110]">Instagram</div>
                      <div className="text-[11px] text-[#70706B]">3 accounts connected</div>
                    </div>
                  </div>
                  <Link
                    href="/dashboard/instagram-accounts"
                    className="px-3 py-1 bg-white border border-[#ECECE8] hover:bg-[#F9F9F8] text-xs font-medium text-[#111110] rounded-lg shadow-2xs"
                  >
                    Manage
                  </Link>
                </div>

                {/* Google Drive Row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-[#4285F4] flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-2xs">
                      G
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#111110]">Google Drive</div>
                      <div className="text-[11px] text-[#70706B]">Not connected</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => triggerToast('Google Drive connector initiated')}
                    className="px-3 py-1 bg-white border border-[#ECECE8] hover:bg-[#F9F9F8] text-xs font-medium text-[#111110] rounded-lg shadow-2xs cursor-pointer"
                  >
                    Connect
                  </button>
                </div>
              </div>
            </div>

            {/* 3. Account Actions Card */}
            <div className="bg-white border border-[#ECECE8] rounded-xl p-5 shadow-2xs">
              <div className="text-xs font-bold text-[#111110] mb-3">Account Actions</div>

              <div className="space-y-1">
                <button
                  type="button"
                  onClick={() => setActiveTab('notifications')}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-[#FBFBFA] transition-colors text-left cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Mail size={16} className="text-[#111110]" />
                    <div>
                      <div className="text-xs font-semibold text-[#111110]">Notifications</div>
                      <div className="text-[11px] text-[#70706B]">Manage email & alert preferences.</div>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-[#9E9E96]" />
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('billing')}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-[#FBFBFA] transition-colors text-left cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <CreditCard size={16} className="text-[#111110]" />
                    <div>
                      <div className="text-xs font-semibold text-[#111110]">Billing & Plan</div>
                      <div className="text-[11px] text-[#70706B]">Manage your subscription and quotas.</div>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-[#9E9E96]" />
                </button>

                <button
                  type="button"
                  onClick={() => triggerPwaPrompt()}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-[#FBFBFA] transition-colors text-left cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Download size={16} className="text-[#15803D]" />
                    <div>
                      <div className="text-xs font-semibold text-[#111110]">Install Comlina App</div>
                      <div className="text-[11px] text-[#70706B]">Add to home screen or desktop.</div>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-[#9E9E96]" />
                </button>

                <button
                  type="button"
                  onClick={() => triggerToast('Activity logs opened')}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-[#FBFBFA] transition-colors text-left cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Clock size={16} className="text-[#111110]" />
                    <div>
                      <div className="text-xs font-semibold text-[#111110]">Activity Logs</div>
                      <div className="text-[11px] text-[#70706B]">View recent account activity.</div>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-[#9E9E96]" />
                </button>

                <button
                  type="button"
                  onClick={() => triggerToast('Signing out...')}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-[#FFF5F5] transition-colors text-left cursor-pointer"
                >
                  <div className="flex items-center gap-3 text-[#111110]">
                    <LogOut size={16} />
                    <div>
                      <div className="text-xs font-semibold text-[#111110]">Log Out</div>
                      <div className="text-[11px] text-[#70706B]">Sign out from your account.</div>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            {/* 4. Need Help? Card */}
            <div className="bg-[#EAF6EE] border border-[#C5E7D1] rounded-xl p-5 shadow-2xs">
              <div className="text-xs font-bold text-[#064125] mb-1">Need Help?</div>
              <p className="text-xs text-[#064125]/80 leading-relaxed mb-3.5">
                Check our <a href="#" onClick={(e) => { e.preventDefault(); triggerToast('Documentation opened'); }} className="text-[#15803D] underline font-semibold">documentation</a> or reach out to support.
              </p>
              <button
                type="button"
                onClick={() => triggerToast('Support modal opened')}
                className="w-full py-2 bg-white border border-[#C5E7D1] hover:bg-white/90 text-[#064125] text-xs font-semibold rounded-lg shadow-2xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <MessageSquare size={14} />
                <span>Contact Support</span>
              </button>
            </div>

          </div>

        </div>
      )}

      {/* ── TAB 2: NOTIFICATIONS ── */}
      {activeTab === 'notifications' && (
        <div className="bg-white border border-[#ECECE8] rounded-xl p-6 shadow-2xs space-y-6 max-w-4xl">
          <div>
            <h2 className="text-sm font-bold text-[#111110]">Notification Settings</h2>
            <p className="text-xs text-[#70706B] mt-0.5">Choose what updates and alerts you receive.</p>
          </div>

          <div className="space-y-4 divide-y divide-[#ECECE8]">
            <div className="flex items-center justify-between pt-3 first:pt-0">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#111110]">High-Intent Lead Alerts</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F4F4F1] text-[#70706B]">Coming soon</span>
                </div>
                <div className="text-xs text-[#70706B] mt-0.5">Get notified immediately when a commenter requests pricing or drops a phone number.</div>
              </div>
              <input
                type="checkbox"
                disabled
                checked={notifyLead}
                onChange={() => {}}
                className="w-4 h-4 accent-[#064125] rounded opacity-50 cursor-not-allowed"
              />
            </div>

            <div className="flex items-center justify-between pt-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#111110]">Meta Token Expiry Alerts</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F4F4F1] text-[#70706B]">Coming soon</span>
                </div>
                <div className="text-xs text-[#70706B] mt-0.5">Receive reminders 7 days and 24 hours before your Meta Graph API token expires.</div>
              </div>
              <input
                type="checkbox"
                disabled
                checked={notifyToken}
                onChange={() => {}}
                className="w-4 h-4 accent-[#064125] rounded opacity-50 cursor-not-allowed"
              />
            </div>

            <div className="flex items-center justify-between pt-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#111110]">Daily Performance Digest</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F4F4F1] text-[#70706B]">Coming soon</span>
                </div>
                <div className="text-xs text-[#70706B] mt-0.5">Summary of DMs dispatched and comments converted each morning.</div>
              </div>
              <input
                type="checkbox"
                disabled
                checked={notifyDigest}
                onChange={() => {}}
                className="w-4 h-4 accent-[#064125] rounded opacity-50 cursor-not-allowed"
              />
            </div>

            <div className="flex items-center justify-between pt-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#111110]">Rate Limit Safeguard</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F4F4F1] text-[#70706B]">Coming soon</span>
                </div>
                <div className="text-xs text-[#70706B] mt-0.5">Alert if comment volume nears Instagram hourly API safety thresholds.</div>
              </div>
              <input
                type="checkbox"
                disabled
                checked={notifyRate}
                onChange={() => {}}
                className="w-4 h-4 accent-[#064125] rounded opacity-50 cursor-not-allowed"
              />
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 4: BILLING & PLAN ── */}
      {activeTab === 'billing' && (
        <div className="space-y-6 max-w-4xl">
          {/* Plan Header Card */}
          <div className="bg-white border border-[#ECECE8] rounded-2xl p-6 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-bold text-[#15803D] uppercase tracking-wider">
                    CURRENT SUBSCRIPTION
                  </span>
                  <PlanBadge tier={planTier} size="xs" />
                </div>
                <h2 className="text-2xl font-black text-[#111110]">
                  {planConfig.name} Plan (₹{planConfig.priceInr}/month)
                </h2>
                <p className="text-xs text-[#70706B] mt-1 max-w-lg">
                  {planConfig.tagline}. Status:{' '}
                  <span className="font-semibold text-emerald-700 capitalize">
                    {usage?.plan_status?.toLowerCase() || 'active'}
                  </span>
                </p>
              </div>

              <div className="flex items-center gap-2.5">
                <Link
                  href="/pricing"
                  className="px-4 py-2.5 bg-white border border-[#DCDCD6] hover:bg-[#FBFBFA] text-[#111110] text-xs font-bold rounded-xl transition-colors shadow-2xs flex items-center gap-1.5 cursor-pointer"
                >
                  <span>Compare Plans</span>
                  <ArrowUpRight size={14} />
                </Link>

                <button
                  type="button"
                  onClick={() => openUpgradeModal(planTier === 'PREMIUM' ? 'PRO' : 'PREMIUM')}
                  className={`px-4 py-2.5 rounded-xl text-xs font-bold text-white shadow-xs transition-transform active:scale-95 flex items-center gap-1.5 cursor-pointer ${
                    planTier === 'PRO'
                      ? 'bg-[#4338CA] hover:bg-[#3730A3]'
                      : 'bg-[#0066FF] hover:bg-[#0052CC]'
                  }`}
                >
                  <Sparkles size={14} />
                  <span>{planTier === 'PRO' ? 'Change Plan' : 'Upgrade Plan'}</span>
                </button>
              </div>
            </div>

            {/* Quota Progress Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-[#ECECE8]">
              {/* Card 1: Automated Posts Quota */}
              <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl space-y-1.5">
                <div className="text-[11px] font-bold text-[#70706B] uppercase tracking-wider">
                  Automated Posts
                </div>
                <div className="text-xl font-extrabold text-[#111110]">
                  {usage?.posts_used ?? 0} /{' '}
                  {usage?.posts_limit === -1 ? 'Unlimited' : (usage?.posts_limit ?? 10)}
                </div>
                <div className="w-full bg-[#ECECE8] h-1.5 rounded-full overflow-hidden mt-2">
                  <div
                    className={`h-full rounded-full transition-all ${
                      usage?.is_post_quota_reached ? 'bg-red-500' : 'bg-[#15803D]'
                    }`}
                    style={{
                      width: `${
                        usage && usage.posts_limit > 0
                          ? Math.min(100, (usage.posts_used / usage.posts_limit) * 100)
                          : 10
                      }%`,
                    }}
                  />
                </div>
                <div className="text-[10.5px] text-[#70706B] pt-0.5">
                  {usage?.is_post_quota_reached
                    ? 'Quota reached — upgrade to add posts'
                    : `${usage?.posts_remaining ?? 10} posts available`}
                </div>
              </div>

              {/* Card 2: Max DMs per Post */}
              <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl space-y-1.5">
                <div className="text-[11px] font-bold text-[#70706B] uppercase tracking-wider">
                  DMs Per Post Limit
                </div>
                <div className="text-xl font-extrabold text-[#111110]">
                  {usage?.max_dms_per_post ?? 99} DMs / post
                </div>
                <div className="text-[11px] text-[#15803D] font-semibold pt-2">
                  {usage?.total_dms_delivered ?? 0} total DMs delivered
                </div>
                <div className="text-[10.5px] text-[#70706B]">
                  Counted server-side only on verified delivery.
                </div>
              </div>

              {/* Card 3: Active Automations */}
              <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl space-y-1.5">
                <div className="text-[11px] font-bold text-[#70706B] uppercase tracking-wider">
                  Active Automations
                </div>
                <div className="text-xl font-extrabold text-[#111110]">
                  {usage?.active_automations ?? 0} / {usage?.max_automations ?? 10}
                </div>
                <div className="w-full bg-[#ECECE8] h-1.5 rounded-full overflow-hidden mt-2">
                  <div
                    className="bg-[#15803D] h-full rounded-full transition-all"
                    style={{
                      width: `${
                        usage && usage.max_automations > 0
                          ? Math.min(100, (usage.active_automations / usage.max_automations) * 100)
                          : 20
                      }%`,
                    }}
                  />
                </div>
                <div className="text-[10.5px] text-[#70706B] pt-0.5">
                  {(usage?.max_automations ?? 10) - (usage?.active_automations ?? 0)} slots open
                </div>
              </div>
            </div>
          </div>

          {/* Dev Test Switcher (Convenient QA/Testing tool) */}
          <div className="p-5 bg-[#FAF9F5] border border-dashed border-[#DCDCD6] rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#111110] flex items-center gap-1.5">
                  <Zap size={14} className="text-amber-600" />
                  <span>Developer / Testing Sandbox Plan Switcher</span>
                </span>
                <p className="text-[11px] text-[#70706B] mt-0.5">
                  Instant backend plan toggle for manual testing and verification of entitlements.
                </p>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-gray-200 text-gray-700 rounded-md">
                DEV ONLY
              </span>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={async () => {
                  await switchPlanDev('FREE');
                  triggerToast('Switched to FREE tier');
                }}
                className={`px-3 py-1.5 text-xs font-bold rounded-xl border transition-all cursor-pointer ${
                  planTier === 'FREE'
                    ? 'bg-[#111110] text-white border-[#111110]'
                    : 'bg-white text-[#70706B] border-[#ECECE8] hover:bg-gray-50'
                }`}
              >
                Free Tier
              </button>

              <button
                type="button"
                onClick={async () => {
                  await switchPlanDev('PREMIUM');
                  triggerToast('Switched to PREMIUM tier');
                }}
                className={`px-3 py-1.5 text-xs font-bold rounded-xl border transition-all cursor-pointer ${
                  planTier === 'PREMIUM'
                    ? 'bg-amber-600 text-white border-amber-600'
                    : 'bg-white text-amber-800 border-amber-200 hover:bg-amber-50'
                }`}
              >
                Premium Tier (₹199/mo)
              </button>

              <button
                type="button"
                onClick={async () => {
                  await switchPlanDev('PRO');
                  triggerToast('Switched to PRO tier');
                }}
                className={`px-3 py-1.5 text-xs font-bold rounded-xl border transition-all cursor-pointer ${
                  planTier === 'PRO'
                    ? 'bg-[#4338CA] text-white border-[#4338CA]'
                    : 'bg-white text-indigo-800 border-indigo-200 hover:bg-indigo-50'
                }`}
              >
                Pro Tier (₹399/mo)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 6: DANGER ZONE ── */}
      {activeTab === 'danger' && (
        <div className="bg-white border-2 border-[#FEE2E2] rounded-xl p-6 shadow-2xs space-y-4 max-w-4xl">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-[#DC2626]">Danger Zone</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEE2E2] text-[#DC2626]">Coming soon</span>
          </div>
          <p className="text-xs text-[#70706B] leading-relaxed">
            Deleting your workspace will permanently purge all automations, contact history, and disconnect your Instagram accounts. This action is irreversible.
          </p>
          <div className="pt-2">
            <button
              type="button"
              disabled
              className="px-4 py-2 bg-[#DC2626] opacity-50 cursor-not-allowed text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-2"
            >
              <Trash2 size={14} />
              <span>Delete Workspace & Account (Coming soon)</span>
            </button>
          </div>
        </div>
      )}

      {/* ── MODAL: UPGRADE TO PRO ── */}
      {isUpgradeModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-[#ECECE8] shadow-2xl w-full max-w-xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <span className="text-[10px] font-bold text-[#15803D] uppercase tracking-wider">UPGRADE PLAN</span>
                <h3 className="text-lg font-bold text-[#111110] mt-0.5">Scale Your Automations</h3>
              </div>
              <button onClick={() => setIsUpgradeModalOpen(false)} className="text-[#70706B] hover:text-[#111110]">
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
              <div className="border-2 border-[#15803D] bg-[#F4FBF6] rounded-xl p-4.5 relative shadow-2xs">
                <span className="absolute -top-2.5 right-3 px-2 py-0.2 bg-[#15803D] text-white rounded-full text-[9px] font-bold">
                  POPULAR
                </span>
                <div className="font-bold text-sm text-[#064125]">Pro Plan</div>
                <div className="text-xl font-extrabold text-[#111110] mt-1">$29<span className="text-xs font-normal text-[#70706B]">/mo</span></div>
                <ul className="mt-3 space-y-1.5 text-xs text-[#064125]">
                  <li className="flex items-center gap-1.5"><Check size={13} className="text-[#15803D]" /> Unlimited Automations</li>
                  <li className="flex items-center gap-1.5"><Check size={13} className="text-[#15803D]" /> 10,000 monthly DMs</li>
                  <li className="flex items-center gap-1.5"><Check size={13} className="text-[#15803D]" /> 3 Instagram Accounts</li>
                </ul>
                <button
                  type="button"
                  disabled
                  className="w-full mt-4 py-2 bg-[#15803D] opacity-50 cursor-not-allowed text-white text-xs font-bold rounded-lg"
                >
                  Coming soon
                </button>
              </div>

              <div className="border border-[#ECECE8] bg-white rounded-xl p-4.5">
                <div className="font-bold text-sm text-[#111110]">Agency Plan</div>
                <div className="text-xl font-extrabold text-[#111110] mt-1">$79<span className="text-xs font-normal text-[#70706B]">/mo</span></div>
                <ul className="mt-3 space-y-1.5 text-xs text-[#70706B]">
                  <li className="flex items-center gap-1.5"><Check size={13} className="text-[#15803D]" /> Unlimited Everything</li>
                  <li className="flex items-center gap-1.5"><Check size={13} className="text-[#15803D]" /> 10 Accounts</li>
                  <li className="flex items-center gap-1.5"><Check size={13} className="text-[#15803D]" /> Priority Webhook Queue</li>
                </ul>
                <button
                  type="button"
                  disabled
                  className="w-full mt-4 py-2 bg-white border border-[#ECECE8] opacity-50 cursor-not-allowed text-xs font-bold text-[#70706B] rounded-lg"
                >
                  Coming soon
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL: DELETE CONFIRMATION ── */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border-2 border-[#FEE2E2] shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center gap-2.5 text-[#DC2626] mb-2">
              <AlertCircle size={20} />
              <h3 className="text-base font-bold">Delete Workspace</h3>
            </div>
            <p className="text-xs text-[#70706B] leading-relaxed mb-4">
              Type <strong className="text-[#111110] font-mono">DELETE</strong> below to permanently confirm:
            </p>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="DELETE"
              className="w-full px-3 py-2 border border-[#ECECE8] rounded-lg text-xs font-mono mb-4 outline-none focus:border-[#DC2626]"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setIsDeleteModalOpen(false); setDeleteConfirmText(''); }}
                className="px-3.5 py-1.5 border border-[#ECECE8] text-xs font-medium rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled
                className="px-3.5 py-1.5 bg-[#DC2626] opacity-50 cursor-not-allowed text-white text-xs font-bold rounded-lg"
              >
                Delete Permanently (Coming soon)
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
