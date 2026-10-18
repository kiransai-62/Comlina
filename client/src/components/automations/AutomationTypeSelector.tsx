// client/src/components/automations/AutomationTypeSelector.tsx
'use client';

import React from 'react';
import { 
  MessageSquare, 
  Repeat, 
  Users, 
  Send, 
  AtSign, 
  Radio, 
  Calendar, 
  Sparkles,
  Bot,
  Lock
} from 'lucide-react';
import { AUTOMATION_TYPE_OPTIONS, AutomationTypeOption, TriggerCategory } from './AutomationTypes';

interface AutomationTypeSelectorProps {
  selectedTypeId: string;
  onSelectType: (option: AutomationTypeOption) => void;
}

const CATEGORY_LABELS: { [key in TriggerCategory]: { title: string; subtitle: string } } = {
  comments: {
    title: 'Comments',
    subtitle: 'Engage followers who comment on your posts & reels',
  },
  messages: {
    title: 'Direct Messages',
    subtitle: 'Automate incoming DMs and customer inquiries',
  },
  stories: {
    title: 'Stories',
    subtitle: 'Turn story mentions and replies into conversations',
  },
  live: {
    title: 'Live Broadcast',
    subtitle: 'Deliver links in real-time during Instagram Live',
  },
  advanced: {
    title: 'Advanced Workflows',
    subtitle: 'Intelligent AI chat and calendar booking outcomes',
  },
};

export function AutomationTypeSelector({
  selectedTypeId,
  onSelectType,
}: AutomationTypeSelectorProps) {
  const renderIcon = (name: string) => {
    switch (name) {
      case 'MessageSquare':
        return <MessageSquare size={20} strokeWidth={2} />;
      case 'Repeat':
        return <Repeat size={20} strokeWidth={2} />;
      case 'Users':
        return <Users size={20} strokeWidth={2} />;
      case 'Send':
        return <Send size={20} strokeWidth={2} />;
      case 'AtSign':
        return <AtSign size={20} strokeWidth={2} />;
      case 'Radio':
        return <Radio size={20} strokeWidth={2} />;
      case 'Calendar':
        return <Calendar size={20} strokeWidth={2} />;
      case 'Sparkles':
        return <Sparkles size={20} strokeWidth={2} />;
      case 'Bot':
        return <Bot size={20} strokeWidth={2} />;
      default:
        return <MessageSquare size={20} strokeWidth={2} />;
    }
  };

  const categories: TriggerCategory[] = ['comments', 'messages', 'stories', 'live', 'advanced'];

  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-6">
      <div>
        <h2 className="text-xl font-black text-[#111110]">
          Choose an automation to get started
        </h2>
      </div>

      <div className="space-y-6">
        {categories.map((catKey) => {
          const categoryOptions = AUTOMATION_TYPE_OPTIONS.filter((opt) => opt.category === catKey);
          if (categoryOptions.length === 0) return null;
          const meta = CATEGORY_LABELS[catKey];

          return (
            <div key={catKey} className="space-y-3">
              <div className="flex items-center justify-between border-b border-[#F4F4F0] pb-2">
                <span className="text-xs font-bold text-[#111110] uppercase tracking-wide">
                  {meta.title}
                </span>
                <span className="text-[11px] text-[#70706B] hidden sm:inline">
                  {meta.subtitle}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
                {categoryOptions.map((opt) => {
                  const isSelected = selectedTypeId === opt.id;
                  const isLocked = Boolean(opt.isLocked);

                  return (
                    <div
                      key={opt.id}
                      onClick={() => onSelectType(opt)}
                      className={`group relative p-5 rounded-2xl cursor-pointer transition-all duration-200 flex flex-col items-center justify-center text-center ${
                        isLocked
                          ? 'bg-[#FCFCFB] border border-[#E5E5DF] hover:border-amber-400 hover:shadow-md hover:bg-white'
                          : isSelected
                          ? 'bg-white shadow-md border-2 border-[#15803D] ring-2 ring-[#15803D]/10 -translate-y-0.5'
                          : 'bg-white border border-[#ECECE8] hover:bg-white hover:shadow-lg hover:shadow-gray-200/50 hover:-translate-y-1 hover:border-gray-300'
                      }`}
                    >
                      {/* Locked or Custom Badge */}
                      {isLocked ? (
                        <span className="absolute top-2.5 right-2.5 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1 shadow-2xs">
                          <Lock size={10} className="text-amber-700" />
                          <span>PRO</span>
                        </span>
                      ) : opt.badge ? (
                        <span className="absolute top-2.5 right-2.5 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#15803D] border border-[#DCFCE7]">
                          {opt.badge}
                        </span>
                      ) : null}

                      {/* Centered Icon with Soft-Blue Badge or Locked Amber Badge */}
                      <div
                        className={`w-11 h-11 rounded-2xl flex items-center justify-center mb-3 transition-all duration-200 ${
                          isLocked
                            ? 'bg-amber-50/70 text-amber-800 group-hover:scale-105 group-hover:bg-amber-100/80 ring-1 ring-amber-200/60'
                            : isSelected
                            ? 'bg-[#EBF5FF] text-[#0066FF] shadow-xs scale-105'
                            : 'bg-[#FBFBFA] text-[#111110] group-hover:bg-[#EBF5FF] group-hover:text-[#0066FF] group-hover:scale-110'
                        }`}
                      >
                        {renderIcon(opt.iconName)}
                      </div>

                      {/* Title */}
                      <div className="flex items-center justify-center gap-1.5 mb-1">
                        <h3 className="text-xs font-bold text-[#111110] transition-colors">
                          {opt.title}
                        </h3>
                        {isLocked && <Lock size={11} className="text-amber-700 shrink-0" />}
                      </div>

                      {/* Description */}
                      <p className="text-[11px] text-[#70706B] leading-relaxed">
                        {opt.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
