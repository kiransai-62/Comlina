// client/src/components/automations/TheyWillGetSection.tsx
'use client';

import React, { useState } from 'react';
import { MessageSquare, Send, Plus, X, ArrowDown } from 'lucide-react';

interface TheyWillGetSectionProps {
  publicReplyEnabled: boolean;
  onPublicReplyToggle: (enabled: boolean) => void;
  publicReplyMessages: string[];
  onPublicReplyMessagesChange: (messages: string[]) => void;
  openingDmEnabled: boolean;
  onOpeningDmToggle: (enabled: boolean) => void;
  openingDmText: string;
  onOpeningDmTextChange: (text: string) => void;
  openingDmButtonText: string;
  onOpeningDmButtonTextChange: (text: string) => void;
}

export function TheyWillGetSection({
  publicReplyEnabled,
  onPublicReplyToggle,
  publicReplyMessages,
  onPublicReplyMessagesChange,
  openingDmEnabled,
  onOpeningDmToggle,
  openingDmText,
  onOpeningDmTextChange,
  openingDmButtonText,
  onOpeningDmButtonTextChange,
}: TheyWillGetSectionProps) {
  const [newVariation, setNewVariation] = useState('');
  const [showAddVariation, setShowAddVariation] = useState(false);

  const primaryMessage = publicReplyMessages[0] || "Check your DMs — I've sent you the guide! ✈️";
  const variations = publicReplyMessages.slice(1);

  const handlePrimaryMessageChange = (newText: string) => {
    onPublicReplyMessagesChange([newText, ...variations]);
  };

  const handleAddVariation = () => {
    if (!newVariation.trim()) return;
    onPublicReplyMessagesChange([...publicReplyMessages, newVariation.trim()]);
    setNewVariation('');
    setShowAddVariation(false);
  };

  const handleRemoveVariation = (indexToRemove: number) => {
    const updated = publicReplyMessages.filter((_, idx) => idx !== indexToRemove + 1);
    onPublicReplyMessagesChange(updated);
  };

  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-6">
      <div>
        <div className="flex items-center gap-2 text-xs font-bold text-[#15803D] uppercase tracking-wider">
          <span>Step 4</span>
          <span>•</span>
          <span>They will get</span>
        </div>
        <h2 className="text-xl font-black text-[#111110] mt-1">
          Automated Response & Messages
        </h2>
        <p className="text-xs text-[#70706B] mt-0.5">
          Configure what happens publicly under the post and privately inside direct messages.
        </p>
      </div>

      <div className="space-y-6">
        {/* ACTION A: PUBLIC COMMENT REPLY */}
        <div className="p-5 bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-white border border-[#ECECE8] flex items-center justify-center text-[#111110]">
                <MessageSquare size={16} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#111110]">
                  Public Comment Reply
                </h3>
                <p className="text-[11px] text-[#70706B]">
                  Reply publicly to the comment on Instagram
                </p>
              </div>
            </div>

            {/* Toggle Switch */}
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={publicReplyEnabled}
                onChange={(e) => onPublicReplyToggle(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#15803D]" />
            </label>
          </div>

          {publicReplyEnabled && (
            <div className="space-y-3 pt-2 border-t border-[#ECECE8] animate-in fade-in duration-150">
              <div>
                <label className="block text-xs font-semibold text-[#111110] mb-1">
                  Reply Message
                </label>
                <input
                  type="text"
                  value={primaryMessage}
                  onChange={(e) => handlePrimaryMessageChange(e.target.value)}
                  placeholder="e.g. Check your DMs — I've sent you the guide! ✈️"
                  className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D]"
                />
              </div>

              {/* Reply Variations (Anti-Spam) */}
              {variations.length > 0 && (
                <div className="space-y-2 pt-1">
                  <span className="text-[11px] font-bold text-[#70706B] uppercase tracking-wider">
                    Additional Variations (Randomized to prevent spam flags)
                  </span>
                  {variations.map((vMsg, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between gap-2 px-3 py-1.5 bg-white border border-[#ECECE8] rounded-lg text-xs"
                    >
                      <span className="text-[#111110] truncate">{vMsg}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveVariation(idx)}
                        className="text-[#70706B] hover:text-red-600 p-1 transition-colors"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {showAddVariation ? (
                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={newVariation}
                    onChange={(e) => setNewVariation(e.target.value)}
                    placeholder="Enter alternative reply text..."
                    className="flex-1 px-3 py-1.5 bg-white border border-[#ECECE8] rounded-lg text-xs outline-none focus:border-[#15803D]"
                  />
                  <button
                    type="button"
                    onClick={handleAddVariation}
                    className="px-3 py-1.5 bg-[#062E1A] text-white text-xs font-bold rounded-lg cursor-pointer"
                  >
                    Add
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setNewVariation('');
                      setShowAddVariation(false);
                    }}
                    className="px-2.5 py-1.5 text-xs text-[#70706B] hover:text-[#111110]"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowAddVariation(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#15803D] hover:text-[#062E1A] cursor-pointer pt-1"
                >
                  <Plus size={13} />
                  <span>Add reply variation</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* ACTION B: PRIVATE DM (OPENING MESSAGE) */}
        <div className="p-5 bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-white border border-[#ECECE8] flex items-center justify-center text-[#111110]">
                <Send size={16} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#111110]">
                  Private DM — 1. Opening Message
                </h3>
                <p className="text-[11px] text-[#70706B]">
                  Sent immediately to initiate the DM conversation
                </p>
              </div>
            </div>

            {/* Sequence Badge */}
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#EBF5FF] text-[#0066FF] border border-[#BFDBFE]">
              Step 1 of Conversation
            </span>
          </div>

          <div className="space-y-3 pt-2 border-t border-[#ECECE8]">
            <div>
              <label className="block text-xs font-semibold text-[#111110] mb-1">
                Opening Message Copy
              </label>
              <textarea
                rows={3}
                value={openingDmText}
                onChange={(e) => onOpeningDmTextChange(e.target.value)}
                placeholder="Hey there! Thanks so much for your interest 😊 Click below to get the guide:"
                className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#15803D]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#111110] mb-1">
                Interactive CTA Button Label
              </label>
              <div className="max-w-xs">
                <input
                  type="text"
                  value={openingDmButtonText}
                  onChange={(e) => onOpeningDmButtonTextChange(e.target.value)}
                  placeholder="e.g. Send me the guide"
                  className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] font-semibold outline-none focus:border-[#15803D]"
                />
              </div>
              <p className="text-[11px] text-[#70706B] mt-1">
                When the user taps this button in Instagram DM, the resource is delivered.
              </p>
            </div>

            {/* Visual Sequence Indicator */}
            <div className="mt-3 p-3 bg-white border border-[#ECECE8] rounded-xl flex items-center justify-between text-xs text-[#70706B]">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#111110] text-white text-[10px] font-bold flex items-center justify-center">1</span>
                <span className="font-semibold text-[#111110]">Opening DM</span>
              </div>
              <ArrowDown size={14} className="text-[#9E9E96]" />
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-medium text-[#70706B]">User clicks button</span>
              </div>
              <ArrowDown size={14} className="text-[#9E9E96]" />
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#15803D] text-white text-[10px] font-bold flex items-center justify-center">2</span>
                <span className="font-semibold text-[#15803D]">Resource Delivered (Step 6)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
