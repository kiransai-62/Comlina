'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { 
  Plus, 
  Search, 
  ChevronDown,
  MoreVertical,
  BookOpen,
  Percent,
  Calendar,
  HelpCircle,
  Gift,
  Zap,
  Edit2,
  Trash2,
  Copy,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Eye,
  X
} from 'lucide-react';
import { useAutomations } from '@/features/automations/hooks';
import { AutomationItem } from '@/features/automations/types';
import { InstagramPhonePreview } from '@/components/automations/InstagramPhonePreview';
import { authService } from '@/lib/auth';

export default function AutomationsPage() {
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'running' | 'paused' | 'drafts'>('all');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [previewItem, setPreviewItem] = useState<AutomationItem | null>(null);

  const { automations: initialAutomations, isLoading, isError, error, refetch, deleteAutomation } = useAutomations();

  // Local state to allow instant interactive toggle switching
  const [localOverrides, setLocalOverrides] = useState<Record<string, 'ACTIVE' | 'PAUSED'>>({});

  const automations = useMemo(() => {
    return (initialAutomations || []).map((item) => {
      if (localOverrides[item.id]) {
        return { ...item, status: localOverrides[item.id] };
      }
      return item;
    });
  }, [initialAutomations, localOverrides]);

  const toggleStatus = (id: string, currentStatus: string) => {
    const newStatus = currentStatus === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    setLocalOverrides((prev) => ({ ...prev, [id]: newStatus }));
  };

  const counts = useMemo(() => {
    const list = automations || [];
    return {
      all: list.length,
      running: list.filter((i) => i.status === 'ACTIVE').length,
      paused: list.filter((i) => i.status === 'PAUSED').length,
      drafts: list.filter((i) => i.status === 'DRAFT').length,
    };
  }, [automations]);

  const filteredItems = useMemo(() => {
    return automations.filter((item) => {
      // Tab filter
      if (activeTab === 'running' && item.status !== 'ACTIVE') return false;
      if (activeTab === 'paused' && item.status !== 'PAUSED') return false;
      if (activeTab === 'drafts' && item.status !== 'DRAFT') return false;

      // Search filter
      const query = search.toLowerCase();
      if (!query) return true;
      const nameMatch = item.name?.toLowerCase().includes(query);
      const trigMatch = (item.trigger_text || item.trigger_type || '').toLowerCase().includes(query);
      const actionMatch = (item.action_text || item.description || '').toLowerCase().includes(query);
      const tagsMatch = item.tags?.some((t) => t.toLowerCase().includes(query));
      return nameMatch || trigMatch || actionMatch || tagsMatch;
    });
  }, [automations, activeTab, search]);

  const renderIcon = (type?: string, name?: string) => {
    const t = (type || '').toLowerCase();
    const n = (name || '').toLowerCase();
    if (t === 'guide' || n.includes('guide')) {
      return <BookOpen size={20} className="text-[#111110]" />;
    }
    if (t === 'percent' || n.includes('price') || n.includes('discount')) {
      return <Percent size={20} className="text-[#111110]" />;
    }
    if (t === 'calendar' || n.includes('event') || n.includes('webinar')) {
      return <Calendar size={20} className="text-[#111110]" />;
    }
    if (t === 'support' || n.includes('support') || n.includes('help')) {
      return <HelpCircle size={20} className="text-[#111110]" />;
    }
    if (t === 'gift' || n.includes('giveaway') || n.includes('join')) {
      return <Gift size={20} className="text-[#111110]" />;
    }
    return <Zap size={20} className="text-[#111110]" />;
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
      try {
        await deleteAutomation(id);
      } catch (err: any) {
        alert(`Failed to delete: ${err.message || err}`);
      }
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 select-none" onClick={() => openMenuId && setOpenMenuId(null)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-[#111110] tracking-tight">Automations</h1>
          <p className="text-sm text-[#70706B] mt-1">
            Create and manage your Instagram automations.
          </p>
        </div>
        <Link
          href="/dashboard/automations/create"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#064125] hover:bg-[#08522F] text-white text-xs font-semibold rounded-xl shadow-xs transition-all"
        >
          <Plus size={16} />
          <span>Create Automation</span>
        </Link>
      </div>

      {/* Filter Tabs & Search Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
        {/* Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === 'all'
                ? 'bg-[#064125] text-white shadow-xs'
                : 'bg-white border border-[#ECECE8] text-[#111110] hover:bg-[#FBFBFA]'
            }`}
          >
            All ({counts.all})
          </button>

          <button
            onClick={() => setActiveTab('running')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === 'running'
                ? 'bg-[#064125] text-white shadow-xs'
                : 'bg-white border border-[#ECECE8] text-[#111110] hover:bg-[#FBFBFA]'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-[#15803D]" />
            <span>Running ({counts.running})</span>
          </button>

          <button
            onClick={() => setActiveTab('paused')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === 'paused'
                ? 'bg-[#064125] text-white shadow-xs'
                : 'bg-white border border-[#ECECE8] text-[#111110] hover:bg-[#FBFBFA]'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-[#9E9E96]" />
            <span>Paused ({counts.paused})</span>
          </button>

          <button
            onClick={() => setActiveTab('drafts')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === 'drafts'
                ? 'bg-[#064125] text-white shadow-xs'
                : 'bg-white border border-[#ECECE8] text-[#111110] hover:bg-[#FBFBFA]'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-[#9E9E96]" />
            <span>Drafts ({counts.drafts})</span>
          </button>
        </div>

        {/* Right Tools: Search & Sort */}
        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#70706B]" />
            <input
              type="text"
              placeholder="Search automations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3.5 py-1.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] placeholder-[#9E9E96] outline-none focus:border-[#15803D] transition-colors shadow-2xs"
            />
          </div>

          <div className="flex items-center gap-1 px-3 py-1.5 rounded-xl border border-[#ECECE8] bg-white text-xs font-medium text-[#111110] shadow-2xs cursor-pointer hover:bg-[#FBFBFA]">
            <span>Last updated</span>
            <ChevronDown size={13} className="text-[#70706B] ml-1" />
          </div>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-white border border-[#ECECE8] rounded-2xl p-5 shadow-2xs animate-pulse flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gray-100" />
                <div className="space-y-2">
                  <div className="h-4 w-36 bg-gray-200 rounded" />
                  <div className="h-3 w-56 bg-gray-100 rounded" />
                </div>
              </div>
              <div className="h-6 w-24 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center text-red-800 space-y-3">
          <AlertCircle size={28} className="mx-auto text-red-600" />
          <div className="font-semibold text-sm">Failed to load automations</div>
          <p className="text-xs text-red-600 max-w-md mx-auto">
            {(error as any)?.message || 'Unable to connect to backend server. Please verify your connection.'}
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

      {/* Empty State */}
      {!isLoading && !isError && filteredItems.length === 0 && (
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-12 text-center shadow-2xs space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-[#EAF6EE] text-[#15803D] flex items-center justify-center mx-auto">
            <Sparkles size={24} />
          </div>
          <h3 className="font-bold text-base text-[#111110]">
            {search ? 'No matching automations found' : 'No automations created yet'}
          </h3>
          <p className="text-xs text-[#70706B] max-w-sm mx-auto">
            {search
              ? 'Try adjusting your search query to find your workflows.'
              : 'Create your first Trigger → Condition → Action workflow to automatically reply to comments and send private DMs.'}
          </p>
          {!search && (
            <Link
              href="/dashboard/automations/create"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#064125] hover:bg-[#08522F] text-white text-xs font-semibold rounded-xl shadow-xs transition-all"
            >
              <Plus size={15} />
              <span>Create Your First Automation</span>
            </Link>
          )}
        </div>
      )}

      {/* Stacked Automation Rows */}
      {!isLoading && !isError && filteredItems.length > 0 && (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const isRunning = item.status === 'ACTIVE';
            const commentsCount = item.stats_comments ?? item.stats?.comments ?? 0;
            const dmsCount = item.stats_dms_sent ?? item.stats?.dmsSent ?? 0;
            const clicksPct = item.stats_clicks_pct || (item.stats_clicks ? `${item.stats_clicks}%` : '42%');
            const triggerText = item.trigger_text || `When someone comments "${item.name.toUpperCase()}"`;
            const actionText = item.action_text || item.description || 'Send auto reply + deliver guide';
            const tags = item.tags && item.tags.length > 0 ? item.tags : ['Keyword', 'Follow Gate'];

            return (
              <div 
                key={item.id} 
                className="bg-white border border-[#ECECE8] hover:border-[#D5D5CE] rounded-2xl p-5 shadow-2xs flex items-center justify-between gap-6 transition-all"
              >
                {/* Left: Icon & Info */}
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  {/* Icon Box */}
                  <div className="w-12 h-12 rounded-2xl border border-[#ECECE8] bg-[#FBFBFA] flex items-center justify-center shrink-0">
                    {renderIcon(item.icon_type, item.name)}
                  </div>

                  {/* Title, Trigger, Action, Badges */}
                  <div className="min-w-0 flex-1">
                    <div className="font-bold text-[15px] text-[#111110] leading-snug truncate">
                      {item.name}
                    </div>
                    <div className="text-xs text-[#70706B] mt-0.5 truncate">
                      {triggerText}
                    </div>
                    <div className="text-xs text-[#70706B] truncate">
                      {actionText}
                    </div>

                    {/* Tag Badges */}
                    <div className="flex items-center gap-1.5 mt-2.5">
                      {tags.map((tag, idx) => (
                        <span 
                          key={idx}
                          className="inline-block text-[11px] font-medium bg-[#F4F4F1] text-[#70706B] px-2 py-0.5 rounded-md"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Status Column (Desktop & Tablet) */}
                <div className="hidden sm:flex items-center gap-2 shrink-0 w-24">
                  <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-[#15803D]' : 'bg-[#9E9E96]'}`} />
                  <span className="text-xs font-semibold text-[#111110]">
                    {isRunning ? 'Running' : 'Paused'}
                  </span>
                </div>

                {/* 3 Stats Columns (Desktop & large tablet) */}
                <div className="hidden md:flex items-center gap-6 lg:gap-8 shrink-0 text-center">
                  <div className="w-16 lg:w-18 text-left">
                    <div className="text-sm font-bold text-[#111110]">{commentsCount}</div>
                    <div className="text-[11px] text-[#70706B] font-medium">Comments</div>
                  </div>

                  <div className="w-16 lg:w-18 text-left">
                    <div className="text-sm font-bold text-[#111110]">{dmsCount}</div>
                    <div className="text-[11px] text-[#70706B] font-medium">DMs Sent</div>
                  </div>

                  <div className="w-16 lg:w-18 text-left">
                    <div className="text-sm font-bold text-[#111110]">{clicksPct}</div>
                    <div className="text-[11px] text-[#70706B] font-medium">Link Clicks</div>
                  </div>
                </div>

                {/* Right: Interactive Toggle, Preview & Menu */}
                <div className="flex items-center gap-3 shrink-0 pl-2">
                  {/* Quick Preview Button */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setPreviewItem(item);
                    }}
                    className="p-1.5 rounded-lg text-[#70706B] hover:text-[#15803D] hover:bg-[#F0FDF4] transition-colors cursor-pointer"
                    title="Live Instagram Preview"
                  >
                    <Eye size={16} />
                  </button>

                  {/* Toggle Switch */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleStatus(item.id, item.status);
                    }}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      isRunning ? 'bg-[#15803D]' : 'bg-[#CBD5E1]'
                    }`}
                    title={isRunning ? 'Click to pause automation' : 'Click to activate automation'}
                  >
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        isRunning ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>

                  {/* Context Menu Button */}
                  <div className="relative">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenMenuId(openMenuId === item.id ? null : item.id);
                      }}
                      className="p-1.5 rounded-lg text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F1] transition-colors cursor-pointer"
                      title="More options"
                    >
                      <MoreVertical size={16} />
                    </button>

                    {openMenuId === item.id && (
                      <div 
                        className="absolute right-0 mt-1 w-44 bg-white rounded-xl border border-[#ECECE8] shadow-lg py-1.5 z-30 animate-in fade-in slide-in-from-top-1 duration-150"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setOpenMenuId(null);
                            setPreviewItem(item);
                          }}
                          className="flex items-center gap-2 px-3.5 py-2 text-xs text-[#111110] hover:bg-[#F4F4F1] font-medium w-full text-left cursor-pointer"
                        >
                          <Eye size={13} className="text-[#15803D]" />
                          <span>Preview Live</span>
                        </button>
                        <Link
                          href={`/dashboard/automations/create?edit=${item.id}`}
                          className="flex items-center gap-2 px-3.5 py-2 text-xs text-[#111110] hover:bg-[#F4F4F1] font-medium"
                        >
                          <Edit2 size={13} className="text-[#70706B]" />
                          <span>Edit Flow</span>
                        </Link>
                        <button
                          onClick={() => {
                            setOpenMenuId(null);
                            alert(`Duplicated "${item.name}"`);
                          }}
                          className="flex items-center gap-2 px-3.5 py-2 text-xs text-[#111110] hover:bg-[#F4F4F1] font-medium w-full text-left"
                        >
                          <Copy size={13} className="text-[#70706B]" />
                          <span>Duplicate</span>
                        </button>
                        <div className="border-t border-[#ECECE8] my-1" />
                        <button
                          onClick={() => {
                            setOpenMenuId(null);
                            handleDelete(item.id, item.name);
                          }}
                          className="flex items-center gap-2 px-3.5 py-2 text-xs text-red-600 hover:bg-red-50 font-medium w-full text-left"
                        >
                          <Trash2 size={13} />
                          <span>Delete</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Live Instagram Preview Modal */}
      {previewItem && (
        <div 
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setPreviewItem(null)}
        >
          <div 
            className="bg-white rounded-3xl p-6 shadow-2xl max-w-md w-full relative flex flex-col items-center max-h-[94vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-full flex items-center justify-between border-b border-[#ECECE8] pb-3 mb-4">
              <div>
                <div className="text-xs font-bold text-[#111110] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse" />
                  <span>Live Simulator Preview</span>
                </div>
                <div className="text-[11px] text-[#70706B] truncate max-w-[280px]">
                  {previewItem.name}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setPreviewItem(null)}
                className="p-1.5 rounded-full text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F1] cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <InstagramPhonePreview
              accountName="yourbrand"
              keywords={previewItem.tags || ['VIP']}
              publicReplyEnabled={true}
              publicReplyText={previewItem.trigger_text ? `Thanks! Replying to your comment!` : 'Thanks for checking in!'}
              openingDmEnabled={true}
              openingDmText={previewItem.action_text || previewItem.description || `Hey there! Here is the info you requested:`}
              openingDmButtonText="Open Resource"
              deliveryText={previewItem.action_text || previewItem.description || `Here's your access link!`}
              deliveryLinkUrl="https://comlina.com"
              deliveryLinkButtonText="View Link"
              defaultTab="dm"
            />
          </div>
        </div>
      )}
    </div>
  );
}
