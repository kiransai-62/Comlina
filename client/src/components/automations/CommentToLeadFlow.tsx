// client/src/components/automations/CommentToLeadFlow.tsx
'use client';

import React, { useState, useRef } from 'react';
import { 
  ArrowLeft, 
  Sparkles, 
  Save, 
  Plus, 
  Trash2, 
  Check, 
  Bell,
  Clock,
  GripVertical,
  Image as ImageIcon,
  Edit3,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import { FlowActionButtons } from './FlowActionButtons';

interface ReminderItem {
  id: string;
  message: string;
  delay: number;
  unit: 'hours' | 'minutes' | 'days';
}

interface CommentToLeadFlowProps {
  onBack: () => void;
  onSave: (flowData: any) => Promise<void>;
  accountName?: string;
  isSaving?: boolean;
  onPreviewChange?: (previewData: any) => void;
}

// Sample posts styled like the user screenshot
const LEAD_FLOW_SAMPLE_POSTS = [
  {
    id: 'lead_post_1',
    title: 'Without the right system, leads slip away...',
    imageUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=80',
    color: 'from-blue-600 to-indigo-900',
  },
  {
    id: 'lead_post_2',
    title: 'If AI writes the code, what does the developer do?',
    imageUrl: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400&auto=format&fit=crop&q=80',
    color: 'from-cyan-600 to-blue-800',
  },
  {
    id: 'lead_post_3',
    title: 'How we 10x\'d qualified inbound calls in 30 days',
    imageUrl: 'https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=400&auto=format&fit=crop&q=80',
    color: 'from-emerald-600 to-teal-900',
  },
  {
    id: 'lead_post_4',
    title: 'AI READS THE EMAIL BEFORE YOU DO.',
    imageUrl: 'https://images.unsplash.com/photo-1579389083078-4e7018379f7e?w=400&auto=format&fit=crop&q=80',
    color: 'from-orange-500 to-amber-700',
  },
  {
    id: 'lead_post_5',
    title: 'Stop losing high-intent prospects in comments',
    imageUrl: 'https://images.unsplash.com/photo-1542744094-3a31f272c490?w=400&auto=format&fit=crop&q=80',
    color: 'from-violet-600 to-purple-900',
  },
  {
    id: 'lead_post_6',
    title: '3 AI MODELS, 1 REAL TASK: Automating DMs',
    imageUrl: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&auto=format&fit=crop&q=80',
    color: 'from-sky-600 to-indigo-800',
  },
  {
    id: 'lead_post_7',
    title: 'Behind our real-time webhook infrastructure',
    imageUrl: 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400&auto=format&fit=crop&q=80',
    color: 'from-slate-800 to-neutral-900',
  },
  {
    id: 'lead_post_8',
    title: 'THE ONLY 3 THINGS YOU NEED TO SCALE REVENUE',
    imageUrl: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=400&auto=format&fit=crop&q=80',
    color: 'from-rose-600 to-pink-900',
  },
];

export function CommentToLeadFlow({
  onBack,
  onSave,
  accountName = 'yourbrand',
  isSaving = false,
  onPreviewChange,
}: CommentToLeadFlowProps) {
  // 1. Flow Name
  const [flowName, setFlowName] = useState('');

  // 2. Post Selection State
  const [selectedPostId, setSelectedPostId] = useState<string>('all');
  const postScrollRef = useRef<HTMLDivElement>(null);

  // 3. Trigger State
  const [replyToAll, setReplyToAll] = useState(false);
  const [triggerKeyword, setTriggerKeyword] = useState('');

  // 4. Welcome DM Message
  const [welcomeMessage, setWelcomeMessage] = useState(
    "Hey! 👋 Thanks for your interest! I'd love to get to know you better. I'll ask you a few quick questions! 😊"
  );

  // 5. Questions State
  const [questions, setQuestions] = useState<string[]>([
    'What is your name?',
    'What is your email address?',
  ]);

  // 6. Completion Message
  const [completionMessage, setCompletionMessage] = useState(
    "Thanks so much! 🙏 We'll be in touch soon! 💌"
  );

  // 7. Unfinished Form Follow-ups State
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
      keywords: replyToAll ? ['ANY COMMENT'] : [triggerKeyword || 'LEAD'],
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
      defaultTab: 'comments',
      isStoryFlow: false,
    });
  }, [
    replyToAll,
    triggerKeyword,
    welcomeMessage,
    questions,
    completionMessage,
    unfinishedFollowUpEnabled,
    reminders,
    onPreviewChange,
  ]);

  // Handlers
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

  const handleScrollPosts = (direction: 'up' | 'down') => {
    if (postScrollRef.current) {
      const scrollAmount = direction === 'up' ? -120 : 120;
      postScrollRef.current.scrollBy({ top: scrollAmount, behavior: 'smooth' });
    }
  };

  const handleSaveClick = async (status: 'DRAFT' | 'ACTIVE' = 'ACTIVE') => {
    const payload = {
      type: 'COMMENT_TO_LEAD',
      status,
      flowName: flowName.trim() || 'Free Guide Lead Collection',
      selectedPostId,
      trigger: {
        replyToAll,
        keyword: replyToAll ? '' : triggerKeyword,
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

  const isFormValid = (replyToAll || !!triggerKeyword.trim()) && questions.length > 0;

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
              Comment → DM Welcome → Questions → Collect Info
            </p>
          </div>
        </div>

        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
        />
      </div>

      {/* 2. VISUAL FLOW SEQUENCE BAR */}
      <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-2xl p-3 flex flex-wrap items-center justify-center gap-2 text-xs font-semibold">
        <span className="px-3 py-1 bg-[#DBEAFE] text-[#1D4ED8] rounded-xl border border-[#BFDBFE]">
          💬 Comment
        </span>
        <span className="text-[#93C5FD]">→</span>
        <span className="px-3 py-1 bg-[#DBEAFE] text-[#1D4ED8] rounded-xl border border-[#BFDBFE]">
          📩 Welcome DM
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

      {/* 4. SELECT POST (OPTIONAL) CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[#0066FF]"><ImageIcon size={17} /></span>
            <h2 className="text-sm font-bold text-[#111110]">Select Post (Optional)</h2>
          </div>
          <p className="text-xs text-[#70706B] mt-0.5">
            Apply to a specific post or all posts
          </p>
        </div>

        {/* 2-Row Grid with Up/Down Scroll Controls on the right */}
        <div className="flex items-center gap-3">
          {/* Scrollable Container with 2 rows */}
          <div 
            ref={postScrollRef}
            className="flex-1 overflow-y-auto max-h-[180px] pr-1 scrollbar-thin"
          >
            <div className="grid grid-cols-4 gap-2.5">
              {/* All Posts Card */}
              <div
                onClick={() => setSelectedPostId('all')}
                className={`h-20 rounded-xl border-2 flex flex-col items-center justify-center p-2 text-center cursor-pointer transition-all ${
                  selectedPostId === 'all'
                    ? 'border-[#0066FF] bg-[#EFF6FF]'
                    : 'border-[#ECECE8] bg-[#FBFBFA] hover:border-gray-300'
                }`}
              >
                <div className="w-6 h-6 rounded-full bg-[#DBEAFE] text-[#0066FF] flex items-center justify-center mb-1">
                  <Sparkles size={13} />
                </div>
                <span className="text-[11px] font-bold text-[#111110]">All Posts</span>
                {selectedPostId === 'all' && (
                  <span className="text-[10px] text-[#0066FF] font-black">✓</span>
                )}
              </div>

              {/* Sample Post Cards */}
              {LEAD_FLOW_SAMPLE_POSTS.map((post) => {
                const isSelected = selectedPostId === post.id;
                return (
                  <div
                    key={post.id}
                    onClick={() => setSelectedPostId(post.id)}
                    className={`h-20 rounded-xl border-2 overflow-hidden relative cursor-pointer group transition-all ${
                      isSelected
                        ? 'border-[#0066FF] ring-2 ring-[#0066FF]/20 shadow-xs'
                        : 'border-[#ECECE8] hover:border-gray-400'
                    }`}
                  >
                    <img
                      src={post.imageUrl}
                      alt={post.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent p-1.5 flex flex-col justify-end text-white">
                      <span className="text-[9px] font-medium line-clamp-2 leading-tight">
                        {post.title}
                      </span>
                    </div>
                    {isSelected && (
                      <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[#0066FF] text-white flex items-center justify-center shadow">
                        <Check size={10} strokeWidth={3} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Scroll Indicator Controls (matches screenshot) */}
          <div className="flex flex-col items-center justify-center gap-1.5 text-[#9E9E96] shrink-0">
            <button
              type="button"
              onClick={() => handleScrollPosts('up')}
              className="p-1 hover:text-[#111110] transition-colors"
            >
              <ChevronUp size={16} />
            </button>
            <div className="w-2 h-7 bg-[#9E9E96] rounded-full opacity-60" />
            <button
              type="button"
              onClick={() => handleScrollPosts('down')}
              className="p-1 hover:text-[#111110] transition-colors"
            >
              <ChevronDown size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* 5. TRIGGER CARD */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-bold text-[#111110]">Trigger</h2>

        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-xs font-bold text-[#111110]">Reply to All Comments</div>
            <p className="text-xs text-[#70706B] mt-0.5">Trigger for every comment, no keyword needed</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={replyToAll}
              onChange={(e) => setReplyToAll(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
          </label>
        </div>

        {!replyToAll && (
          <div className="space-y-1.5 pt-2">
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
              Commenter must include this word to trigger the flow
            </p>
          </div>
        )}
      </div>

      {/* 6. WELCOME DM MESSAGE CARD */}
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

      {/* 7. QUESTIONS CARD */}
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

      {/* 8. COMPLETION MESSAGE CARD */}
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
          Sent after all questions are answered.
        </p>
      </div>

      {/* 9. UNFINISHED FORM FOLLOW-UPS CARD */}
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
                    Reminder {idx + 1}
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

      {/* 10. BOTTOM ACTION BUTTONS */}
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
