// client/src/app/dashboard/contacts/page.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { 
  Users, 
  User, 
  Send, 
  Star, 
  Download, 
  Plus, 
  Search, 
  Filter, 
  MoreVertical, 
  X, 
  MessageSquare, 
  ChevronLeft, 
  ChevronRight,
  ChevronDown,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { contactsApi } from '@/features/contacts/api';

export default function ContactsPage() {
  const router = useRouter();
  const [activeSegment, setActiveSegment] = useState<'ALL' | 'FOLLOWERS' | 'NON_FOLLOWERS' | 'CONVERTED'>('ALL');
  const [search, setSearch] = useState('');
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [selectedRows, setSelectedRows] = useState<Record<string, boolean>>({});

  const { 
    data: contacts, 
    isLoading: loadingContacts, 
    isError: errorContacts, 
    error: contactsError, 
    refetch: refetchContacts 
  } = useQuery({
    queryKey: ['contacts'],
    queryFn: () => contactsApi.list(),
  });

  const contactsList: any[] = Array.isArray(contacts) ? contacts : [];

  // Active contact for inspector drawer
  const activeId = selectedContactId || (contactsList.length > 0 ? contactsList[0].id : null);
  const selectedContact = contactsList.find((c: any) => c.id === activeId) || null;

  // Dynamically computed metrics
  const totalContactsCount = contactsList.length;
  const followersCount = contactsList.filter((c: any) => c.follower_status === 'FOLLOWING').length;
  const nonFollowersCount = contactsList.filter((c: any) => c.follower_status !== 'FOLLOWING').length;
  const convertedCount = contactsList.filter((c: any) => !!c.is_converted).length;

  const handleToggleSelectAll = () => {
    if (Object.keys(selectedRows).length === contactsList.length) {
      setSelectedRows({});
    } else {
      const allSelected: Record<string, boolean> = {};
      contactsList.forEach((c: any) => {
        allSelected[c.id] = true;
      });
      setSelectedRows(allSelected);
    }
  };

  const handleToggleRow = (id: string) => {
    setSelectedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Segment filtering
  const filteredContacts = contactsList.filter((c: any) => {
    const q = search.toLowerCase();
    const handleMatch = (c.username || '').toLowerCase().includes(q);
    const nameMatch = (c.full_name || '').toLowerCase().includes(q);
    const textMatch = handleMatch || nameMatch;

    if (!textMatch) return false;

    if (activeSegment === 'FOLLOWERS') return c.follower_status === 'FOLLOWING';
    if (activeSegment === 'NON_FOLLOWERS') return c.follower_status !== 'FOLLOWING';
    if (activeSegment === 'CONVERTED') return !!c.is_converted;
    return true;
  });

  return (
    <div className="max-w-[1440px] mx-auto space-y-6">
      {/* Page Title & Action Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-extrabold text-[#111110] tracking-tight">Contacts</h1>
          <p className="text-xs text-[#70706B] mt-1">
            All the people who have engaged with your Instagram content.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Export Button */}
          <button
            onClick={() => {
              if (contactsList.length === 0) {
                alert('No contacts available to export.');
              } else {
                alert(`Exporting ${contactsList.length} contacts to CSV...`);
              }
            }}
            className="flex items-center gap-2 px-3.5 py-2 bg-white border border-[#ECECE8] hover:bg-[#FBFBFA] rounded-xl text-xs font-semibold text-[#111110] shadow-2xs transition-colors cursor-pointer"
          >
            <Download size={14} className="text-[#70706B]" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Global Error State */}
      {errorContacts && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center justify-between gap-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600 shrink-0" />
            <div>
              <div className="text-xs font-semibold text-red-900">Failed to load contacts</div>
              <div className="text-xs text-red-700">
                {(contactsError as any)?.message || 'Unable to connect to backend server. Contacts data cannot be retrieved.'}
              </div>
            </div>
          </div>
          <button
            onClick={() => refetchContacts()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all shrink-0 cursor-pointer"
          >
            <RefreshCw size={13} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Top 4 KPI Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* Total Contacts */}
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-[#F4F4F1] flex items-center justify-center text-[#70706B]">
              <Users size={18} />
            </div>
            <span className="text-xs font-semibold text-[#15803D] bg-[#EAF6EE] px-2 py-0.5 rounded-full">
              Live
            </span>
          </div>
          <div>
            <div className="text-xs font-medium text-[#70706B]">Total Contacts</div>
            <div className="text-2xl font-extrabold text-[#111110] mt-0.5">
              {loadingContacts ? '—' : totalContactsCount.toLocaleString()}
            </div>
            <div className="text-[11px] text-[#9E9E96] mt-0.5">Captured via automations</div>
          </div>
        </div>

        {/* Followers */}
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-[#F4F4F1] flex items-center justify-center text-[#70706B]">
              <User size={18} />
            </div>
            <span className="text-xs font-semibold text-[#15803D] bg-[#EAF6EE] px-2 py-0.5 rounded-full">
              Followers
            </span>
          </div>
          <div>
            <div className="text-xs font-medium text-[#70706B]">Following You</div>
            <div className="text-2xl font-extrabold text-[#111110] mt-0.5">
              {loadingContacts ? '—' : followersCount.toLocaleString()}
            </div>
            <div className="text-[11px] text-[#9E9E96] mt-0.5">Verified followers</div>
          </div>
        </div>

        {/* Non-Followers */}
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-[#F4F4F1] flex items-center justify-center text-[#70706B]">
              <Send size={18} />
            </div>
            <span className="text-xs font-semibold text-[#70706B] bg-[#F2F2EE] px-2 py-0.5 rounded-full">
              Audience
            </span>
          </div>
          <div>
            <div className="text-xs font-medium text-[#70706B]">Non-Followers</div>
            <div className="text-2xl font-extrabold text-[#111110] mt-0.5">
              {loadingContacts ? '—' : nonFollowersCount.toLocaleString()}
            </div>
            <div className="text-[11px] text-[#9E9E96] mt-0.5">Potential followers</div>
          </div>
        </div>

        {/* Converted */}
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-[#F4F4F1] flex items-center justify-center text-[#70706B]">
              <Star size={18} />
            </div>
            <span className="text-xs font-semibold text-[#15803D] bg-[#EAF6EE] px-2 py-0.5 rounded-full">
              Leads
            </span>
          </div>
          <div>
            <div className="text-xs font-medium text-[#70706B]">Converted Leads</div>
            <div className="text-2xl font-extrabold text-[#111110] mt-0.5">
              {loadingContacts ? '—' : convertedCount.toLocaleString()}
            </div>
            <div className="text-[11px] text-[#9E9E96] mt-0.5">Completed goal action</div>
          </div>
        </div>
      </div>

      {/* Segment Tabs & Search/Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Filter Segment Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {[
            { id: 'ALL', label: `All (${totalContactsCount})` },
            { id: 'FOLLOWERS', label: `Followers (${followersCount})` },
            { id: 'NON_FOLLOWERS', label: `Non-followers (${nonFollowersCount})` },
            { id: 'CONVERTED', label: `Converted (${convertedCount})` },
          ].map((tab) => {
            const isActive = activeSegment === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSegment(tab.id as any)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#064125] text-white shadow-xs'
                    : 'text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F1]'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Search & Filter */}
        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <div className="relative w-full sm:w-72">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9E9E96]" />
            <input
              type="text"
              placeholder="Search by username or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] placeholder:text-[#9E9E96] outline-none focus:border-[#15803D] shadow-2xs"
            />
          </div>
        </div>
      </div>

      {/* Main Grid: Contacts Table & Selected Contact Profile Card */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* Contacts Table Column */}
        <div className={`${selectedContact ? 'col-span-12 lg:col-span-8' : 'col-span-12'} bg-white border border-[#ECECE8] rounded-2xl shadow-2xs overflow-hidden transition-all`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#ECECE8] text-[#70706B] font-semibold bg-white">
                  <th className="py-3 px-4 w-10">
                    <input
                      type="checkbox"
                      checked={Object.keys(selectedRows).length === contactsList.length && contactsList.length > 0}
                      onChange={handleToggleSelectAll}
                      className="rounded border-gray-300 text-[#064125] focus:ring-0 cursor-pointer"
                    />
                  </th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Interaction</th>
                  <th className="py-3 px-4">Interactions</th>
                  <th className="py-3 px-4">Tags</th>
                  <th className="py-3 px-3 w-8"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#ECECE8]/60">
                {/* Loading State */}
                {loadingContacts && (
                  [1, 2, 3, 4].map((n) => (
                    <tr key={n} className="animate-pulse">
                      <td className="py-4 px-4"><div className="w-4 h-4 bg-gray-200 rounded" /></td>
                      <td className="py-4 px-4"><div className="w-24 h-3 bg-gray-200 rounded" /></td>
                      <td className="py-4 px-4"><div className="w-20 h-3 bg-gray-100 rounded" /></td>
                      <td className="py-4 px-4"><div className="w-16 h-3 bg-gray-100 rounded" /></td>
                      <td className="py-4 px-4"><div className="w-16 h-3 bg-gray-100 rounded" /></td>
                      <td className="py-4 px-4"><div className="w-8 h-3 bg-gray-100 rounded" /></td>
                      <td className="py-4 px-4"><div className="w-16 h-3 bg-gray-100 rounded" /></td>
                      <td className="py-4 px-3" />
                    </tr>
                  ))
                )}

                {/* Empty State */}
                {!loadingContacts && !errorContacts && filteredContacts.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-12 text-center">
                      <div className="w-10 h-10 rounded-full bg-[#FAFAF8] border border-[#ECECE8] flex items-center justify-center mx-auto text-[#70706B] mb-2">
                        <Users size={18} />
                      </div>
                      <div className="text-xs font-bold text-[#111110]">No contacts found</div>
                      <p className="text-[11px] text-[#70706B] max-w-xs mx-auto mt-1">
                        {search ? 'No contacts matched your search query.' : 'Contacts captured through your Instagram automations will appear here.'}
                      </p>
                    </td>
                  </tr>
                )}

                {/* Real Contact Rows */}
                {!loadingContacts && !errorContacts && filteredContacts.map((c: any) => {
                  const isRowSelected = selectedContact?.id === c.id;
                  const isChecked = !!selectedRows[c.id];
                  const rawUsername = c.username || 'User';
                  const handle = rawUsername.startsWith('@') ? rawUsername : `@${rawUsername}`;
                  const isFollowing = c.follower_status === 'FOLLOWING';
                  const initial = rawUsername.replace('@', '').charAt(0).toUpperCase() || 'U';

                  return (
                    <tr
                      key={c.id}
                      onClick={() => setSelectedContactId(c.id)}
                      className={`cursor-pointer transition-colors ${
                        isRowSelected ? 'bg-[#FBFBFA]' : 'hover:bg-[#FDFDFD]'
                      }`}
                    >
                      {/* Checkbox */}
                      <td className="py-3.5 px-4" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleRow(c.id)}
                          className="rounded border-gray-300 text-[#064125] focus:ring-0 cursor-pointer"
                        />
                      </td>

                      {/* User Avatar + Username */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full border border-[#ECECE8] bg-[#EAF6EE] text-[#064125] flex items-center justify-center font-bold text-xs shrink-0">
                            {initial}
                          </div>
                          <span className="font-bold text-xs text-[#111110]">{handle}</span>
                        </div>
                      </td>

                      {/* Name */}
                      <td className="py-3.5 px-4 text-[#70706B] font-medium">
                        {c.full_name || '—'}
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              isFollowing ? 'bg-[#15803D]' : 'bg-[#9E9E96]'
                            }`}
                          />
                          <span
                            className={`text-xs font-semibold ${
                              isFollowing ? 'text-[#15803D]' : 'text-[#70706B]'
                            }`}
                          >
                            {isFollowing ? 'Following' : 'Not following'}
                          </span>
                        </div>
                      </td>

                      {/* Last Interaction */}
                      <td className="py-3.5 px-4 text-[#70706B] font-medium">
                        {c.last_interaction_at || 'Recently'}
                      </td>

                      {/* Interactions Count */}
                      <td className="py-3.5 px-4 font-semibold text-[#111110]">
                        {c.interactions ?? 1}
                      </td>

                      {/* Tags */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1 flex-wrap">
                          {Array.isArray(c.tags) && c.tags.length > 0 ? (
                            c.tags.map((t: string) => (
                              <span
                                key={t}
                                className="bg-[#F2F2EE] text-[#70706B] px-2 py-0.5 rounded-full text-[11px] font-medium"
                              >
                                {t}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-[#9E9E96]">—</span>
                          )}
                        </div>
                      </td>

                      {/* Menu */}
                      <td className="py-3.5 px-3 text-[#9E9E96] hover:text-[#111110]" onClick={(e) => e.stopPropagation()}>
                        <MoreVertical size={15} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="p-4 border-t border-[#ECECE8] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white text-xs text-[#70706B]">
            <div>
              Showing {filteredContacts.length > 0 ? `1-${filteredContacts.length}` : 0} of {filteredContacts.length} contacts
            </div>
          </div>
        </div>

        {/* Selected Contact Profile Drawer */}
        {selectedContact && (
          <div className="col-span-12 lg:col-span-4 bg-white border border-[#ECECE8] rounded-2xl shadow-2xs p-5 space-y-4 relative">
            {/* Close Button */}
            <button
              onClick={() => setSelectedContactId(null)}
              className="absolute top-4 right-4 text-[#9E9E96] hover:text-[#111110] p-1 rounded-lg hover:bg-[#F4F4F1] transition-colors cursor-pointer"
            >
              <X size={16} />
            </button>

            {/* Profile Overview */}
            <div className="flex items-center gap-3 pt-1">
              <div className="w-12 h-12 rounded-full border border-[#ECECE8] bg-[#EAF6EE] text-[#064125] flex items-center justify-center font-bold text-sm shrink-0">
                {(selectedContact.username || 'U').charAt(0).toUpperCase()}
              </div>
              <div>
                <div className="font-extrabold text-sm text-[#111110]">
                  {selectedContact.username?.startsWith('@') ? selectedContact.username : `@${selectedContact.username || 'User'}`}
                </div>
                <div className="text-xs text-[#70706B] font-medium mt-0.5">
                  {selectedContact.full_name || 'Instagram User'}
                </div>
              </div>
            </div>

            {/* Status & Converted Pills */}
            <div className="flex items-center gap-2">
              <span className="bg-[#EAF6EE] text-[#15803D] text-xs font-semibold px-2.5 py-1 rounded-full flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" />
                <span>{selectedContact.follower_status === 'FOLLOWING' ? 'Following' : 'Not following'}</span>
              </span>
              {selectedContact.is_converted && (
                <span className="bg-[#F2F2EE] text-[#15803D] text-xs font-medium px-2.5 py-1 rounded-full flex items-center gap-1">
                  <span>★</span>
                  <span>Converted</span>
                </span>
              )}
            </div>

            {/* 3-Column Stats Row */}
            <div className="grid grid-cols-3 text-center border-y border-[#ECECE8] py-3 my-2">
              <div>
                <div className="font-extrabold text-base text-[#111110]">
                  {selectedContact.interactions ?? 1}
                </div>
                <div className="text-[11px] text-[#70706B] font-medium mt-0.5">Interactions</div>
              </div>
              <div>
                <div className="font-extrabold text-xs text-[#111110] pt-1 truncate">
                  {selectedContact.last_interaction_at || 'Recently'}
                </div>
                <div className="text-[11px] text-[#70706B] font-medium mt-0.5">Last active</div>
              </div>
              <div>
                <div className="font-extrabold text-xs text-[#111110] pt-1 truncate">
                  {selectedContact.first_seen || '—'}
                </div>
                <div className="text-[11px] text-[#70706B] font-medium mt-0.5">First seen</div>
              </div>
            </div>

            {/* Tags Section */}
            <div className="space-y-2">
              <div className="text-xs font-bold text-[#111110]">Tags</div>
              <div className="flex items-center gap-1.5 flex-wrap">
                {Array.isArray(selectedContact.tags) && selectedContact.tags.length > 0 ? (
                  selectedContact.tags.map((t: string) => (
                    <span
                      key={t}
                      className="bg-[#F2F2EE] text-[#70706B] px-3 py-1 rounded-full text-xs font-medium"
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-[#9E9E96]">No tags assigned</span>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 pt-4">
              <Link
                href="/dashboard/inbox"
                className="w-full py-2.5 bg-white border border-[#ECECE8] hover:bg-[#FBFBFA] rounded-xl text-xs font-semibold text-[#111110] flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-2xs"
              >
                <MessageSquare size={14} className="text-[#70706B]" />
                <span>Open Conversation</span>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
