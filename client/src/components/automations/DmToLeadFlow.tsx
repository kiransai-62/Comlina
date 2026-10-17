// client/src/components/automations/DmToLeadFlow.tsx
'use client';

import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Save, 
  Plus, 
  Trash2, 
  Bell,
  Clock,
  GripVertical,
  Edit3
} from 'lucide-react';
import { FlowActionButtons } from './FlowActionButtons';

interface ReminderItem {
  id: string;
  message: string;
  delay: number;
  unit: 'hours' | 'minutes' | 'days';
}

interface DmToLeadFlowProps {
  onBack: () => void;
  onSave: (flowData: any) => Promise<void>;
  accountName?: string;
  isSaving?: boolean;
  onPreviewChange?: (previewData: any) => void;
}

export function DmToLeadFlow({
  onBack,
  onSave,
  accountName = 'yourbrand',
  isSaving = false,
  onPreviewChange,
}: DmToLeadFlowProps) {
  // 1. Flow Name
  const [flowName, setFlowName] = useState('');

  // 2. DM Trigger Keyword
  const [triggerKeyword, setTriggerKeyword] = useState('');

  // 3. Welcome DM Message
  const [welcomeMessage, setWelcomeMessage] = useState(
    "Hey! 👋 Thanks for your interest! I'd love to get to know you better. I'll ask you a few quick questions! 😊"
  );

  // 4. Questions State
  const [questions, setQuestions] = useState<string[]>([
    'What is your name?',
    'What is your email address?',
  ]);

  // 5. Completion Message
  const [completionMessage, setCompletionMessage] = useState(
    "Thanks so much! 🙏 We'll be in touch soon! 💌"
  );

  // 6. Unfinished Form Follow-ups State
  const [unfinishedFollowUpEnabled, setUnfinishedFollowUpEnabled] = useState(true);
  const [reminders, setReminders] = useState<ReminderItem[]>([
    {
      id: 'rem_1',
      message: 'Hi {name}, you haven\'t filled your form fully — do you want to continue it?',
      delay: 1,
      unit: 'hours',
    },
  ]);

  // Synchronize Live Preview Setup
  React.useEffect(() => {
    onPreviewChange?.({
      keywords: [triggerKeyword || 'START'],
      publicReplyEnabled: false,
      openingDmEnabled: true,
      openingDmText: welcomeMessage,
      openingDmButtonText: 'Start',
      askEmailEnabled: true,
      askEmailText: questions[0] || 'What is your email address?',
      deliveryText: completionMessage,
      followupEnabled: unfinishedFollowUpEnabled && reminders.length > 0,
      followupHours: reminders[0]?.delay || 1,
      followupText: reminders[0]?.message || '',
      defaultTab: 'dm',
      isStoryFlow: false,
    });
  }, [
    triggerKeyword,
    welcomeMessage,
    questions,
    completionMessage,
    unfinishedFollowUpEnabled,
    reminders,
    onPreviewChange,
  ]);

  // Handlers for Questions
  const handleAddQuestion = () => {
    setQuestions([...questions, '']);
  };

  const handleUpdateQuestion = (index: number, val: string) => {
    const updated = [...questions];
    updated[index] = val;
    setQuestions(updated);
  };

  const handleRemoveQuestion = (index: number) => {
    if (questions.length > 1) {
      setQuestions(questions.filter((_, idx) => idx !== index));
    }
  };

  // Handlers for Reminders
  const handleAddReminder = () => {
    setReminders([
      ...reminders,
      {
        id: `rem_${Date.now()}`,
        message: 'Hi {name}, just checking in to see if you would like to complete your response? 😊',
        delay: 24,
        unit: 'hours',
      },
    ]);
  };

  const handleUpdateReminder = (id: string, updates: Partial<ReminderItem>) => {
    setReminders(reminders.map((r) => (r.id === id ? { ...r, ...updates } : r)));
  };

  const handleRemoveReminder = (id: string) => {
    if (reminders.length > 1) {
      setReminders(reminders.filter((r) => r.id !== id));
    }
  };

  const handleSaveClick = async (status: 'DRAFT' | 'ACTIVE' = 'ACTIVE') => {
    const payload = {
      type: 'DM_TO_LEAD',
      status,
      flowName: flowName.trim() || 'Free Guide Lead Collection',
      trigger: {
        type: 'DM',
        keyword: triggerKeyword.trim() || 'GUIDE, INFO, FREE',
      },
      welcomeMessage,
      questions: questions.filter((q) => q.trim().length > 0),
      completionMessage,
      unfinishedFollowUp: {
        enabled: unfinishedFollowUpEnabled,
        reminders,
      },
    };

    await onSave(payload);
  };

  const isFormValid = !!triggerKeyword.trim() && questions.length > 0;

  return (
    <div className="max-w-2xl mx-auto pb-24 text-[#111110] space-y-6">
      
      {/* 1. TOP HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-1 border-b border-[#ECECE8]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="p-1 text-[#70706B] hover:text-[#111110] transition-colors cursor-pointer"
            title="Back to Automation Selection"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-[#111110] tracking-tight">
              Create Lead Flow
            </h1>
            <p className="text-xs text-[#70706B] font-normal">
              DM keyword → Welcome → Questions → Collect Info
            </p>
          </div>
        </div>

        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
          publishLabel="Publish Lead Flow"
        />
      </div>

      {/* 2. VISUAL FLOW SEQUENCE BAR (3 Steps for DM) */}
      <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-2xl p-3 flex flex-wrap items-center justify-center gap-2 text-xs font-semibold">
        <span className="px-3 py-1 bg-[#DBEAFE] text-[#1D4ED8] rounded-xl border border-[#BFDBFE]">
          📩 DM Keyword
        </span>
        <span className="text-[#93C5FD]">→</span>
        <span className="px-3 py-1 bg-[#DCFCE7] text-[#15803D] rounded-xl border border-[#BBF7D0]">
          ❓ Questions
        </span>
        <span className="text-[#93C5FD]">→</span>
        <span className="px-3 py-1 bg-[#DCFCE7] text-[#15803D] rounded-xl border border-[#BBF7D0]">
          ✅ Lead Saved
        </span>
      </div>

      {/* 3. FLOW NAME CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-2">
        <label className="block text-xs font-bold text-[#111110]">
          Flow Name
        </label>
        <input
          type="text"
          value={flowName}
          onChange={(e) => setFlowName(e.target.value)}
          placeholder="e.g., Free Guide Lead Collection"
          className="w-full px-4 py-3 bg-white border border-[#ECECE8] rounded-xl text-xs font-normal text-[#111110] outline-none focus:border-[#0066FF] placeholder:text-[#9E9E96]"
        />
      </div>

      {/* 4. DM TRIGGER KEYWORD CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-2">
        <h2 className="text-sm font-bold text-[#111110]">DM Trigger Keyword</h2>
        
        <div className="space-y-1.5 pt-1">
          <label className="block text-xs font-bold text-[#111110]">
            Trigger Keyword
          </label>
          <input
            type="text"
            value={triggerKeyword}
            onChange={(e) => setTriggerKeyword(e.target.value)}
            placeholder="e.g., GUIDE, INFO, FREE"
            className="w-full px-4 py-3 bg-white border border-[#ECECE8] rounded-xl text-xs font-normal text-[#111110] outline-none focus:border-[#0066FF] placeholder:text-[#9E9E96]"
          />
          <p className="text-[11px] text-[#70706B]">
            When someone DMs you this exact keyword, the lead flow starts immediately.
          </p>
        </div>
      </div>

      {/* 5. WELCOME DM MESSAGE CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-2">
        <div className="flex items-center gap-2">
          <span>📩</span>
          <h2 className="text-sm font-bold text-[#111110]">Welcome DM Message</h2>
        </div>

        <div className="relative">
          <textarea
            rows={3}
            value={welcomeMessage}
            onChange={(e) => setWelcomeMessage(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#0066FF] resize-none pr-8"
          />
          <div className="absolute bottom-3 right-3 text-[#9E9E96] pointer-events-none">
            <Edit3 size={15} />
          </div>
        </div>
        <p className="text-[11px] text-[#70706B]">
          This message is sent immediately when someone triggers the flow. The first question follows automatically.
        </p>
      </div>

      {/* 6. QUESTIONS CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>❓</span>
            <h2 className="text-sm font-bold text-[#111110]">Questions</h2>
          </div>
          <button
            type="button"
            onClick={handleAddQuestion}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 border border-[#ECECE8] rounded-xl text-xs font-bold text-[#111110] hover:bg-[#FBFBFA] transition-colors cursor-pointer"
          >
            <Plus size={14} />
            <span>Add Question</span>
          </button>
        </div>

        {/* Question Items */}
        <div className="space-y-3">
          {questions.map((q, idx) => (
            <div
              key={idx}
              className="p-4 bg-white border border-[#ECECE8] rounded-xl space-y-1.5"
            >
              <div className="text-[11px] font-bold text-[#70706B] uppercase ml-7">
                Q{idx + 1}
              </div>
              <div className="flex items-center gap-2.5">
                <GripVertical size={16} className="text-[#9E9E96] shrink-0 cursor-grab" />
                <input
                  type="text"
                  value={q}
                  onChange={(e) => handleUpdateQuestion(idx, e.target.value)}
                  placeholder={`Question ${idx + 1}...`}
                  className="flex-1 px-4 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveQuestion(idx)}
                  className="p-1.5 text-red-400 hover:text-red-600 rounded-lg transition-colors cursor-pointer"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 7. COMPLETION MESSAGE CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-2">
        <div className="flex items-center gap-2">
          <span>✅</span>
          <h2 className="text-sm font-bold text-[#111110]">Completion Message</h2>
        </div>

        <div className="relative">
          <textarea
            rows={3}
            value={completionMessage}
            onChange={(e) => setCompletionMessage(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#0066FF] resize-none pr-8"
          />
          <div className="absolute bottom-3 right-3 text-[#9E9E96] pointer-events-none">
            <Edit3 size={15} />
          </div>
        </div>
        <p className="text-[11px] text-[#70706B]">
          Sent after all questions are answered
        </p>
      </div>

      {/* 8. UNFINISHED FORM FOLLOW-UPS CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-[#0066FF] text-white flex items-center justify-center shrink-0 mt-0.5">
              <Bell size={16} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#111110]">Unfinished form follow-ups</h2>
              <p className="text-xs text-[#70706B] leading-relaxed mt-0.5">
                If someone stops answering mid-way, we nudge them with a "Yes" button. Tapping it resumes the form from the exact question they left. All nudges stay inside the 24-hour messaging window.
              </p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={unfinishedFollowUpEnabled}
              onChange={(e) => setUnfinishedFollowUpEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
          </label>
        </div>

        {unfinishedFollowUpEnabled && (
          <div className="space-y-4 pt-3 border-t border-[#ECECE8] animate-in fade-in duration-150">
            {reminders.map((rem, idx) => (
              <div
                key={rem.id}
                className="p-4 bg-white border border-[#ECECE8] rounded-xl space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-[#70706B] uppercase tracking-wider bg-[#F5F5F3] px-2 py-0.5 rounded">
                    Reminder 1
                  </span>
                  {reminders.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveReminder(rem.id)}
                      className="text-[#70706B] hover:text-red-600 p-1"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>

                <div className="relative">
                  <textarea
                    rows={2}
                    value={rem.message}
                    onChange={(e) => handleUpdateReminder(rem.id, { message: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-lg text-xs text-[#111110] outline-none focus:border-[#0066FF] resize-none pr-8"
                  />
                  <div className="absolute bottom-2.5 right-2.5 text-[#9E9E96] pointer-events-none">
                    <Edit3 size={14} />
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs text-[#70706B]">
                  <Clock size={14} className="text-[#70706B]" />
                  <input
                    type="number"
                    min="1"
                    value={rem.delay}
                    onChange={(e) => handleUpdateReminder(rem.id, { delay: Number(e.target.value) })}
                    className="w-16 px-2 py-1 bg-white border border-[#ECECE8] rounded-lg text-xs text-center font-bold text-[#111110]"
                  />
                  <select
                    value={rem.unit}
                    onChange={(e) => handleUpdateReminder(rem.id, { unit: e.target.value as any })}
                    className="px-2.5 py-1 bg-white border border-[#ECECE8] rounded-lg text-xs font-semibold text-[#111110] cursor-pointer"
                  >
                    <option value="minutes">minutes</option>
                    <option value="hours">hours</option>
                    <option value="days">days</option>
                  </select>
                  <span>after their last message</span>
                </div>
              </div>
            ))}

            <button
              type="button"
              onClick={handleAddReminder}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#ECECE8] bg-white rounded-lg text-xs font-semibold text-[#111110] hover:bg-[#FBFBFA] transition-colors cursor-pointer"
            >
              <Plus size={14} />
              <span>Add reminder</span>
            </button>

            <p className="text-[11px] text-[#70706B]">
              Use {'{name}'} to insert the person's name.
            </p>
          </div>
        )}
      </div>

      {/* 9. BOTTOM ACTION BUTTONS */}
      <div className="pt-4 pb-2 flex items-center justify-end gap-3 border-t border-[#ECECE8]">
        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
          publishLabel="Publish Lead Flow"
        />
      </div>

    </div>
  );
}
