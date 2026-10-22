// client/src/app/dashboard/automations/create/page.tsx
'use client';

import React, { useState, useEffect, useMemo, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { useUIStore } from '@/stores/uiStore';
import { useAutomations } from '@/features/automations/hooks';
import { automationsApi } from '@/features/automations/api';
import { instagramApi } from '@/features/instagram/api';
import { ConnectedInstagramAccount } from '@/features/instagram/types';

import {
  AutomationDraft,
  DEFAULT_AUTOMATION_DRAFT,
  validateAutomationDraft,
  AutomationTypeOption,
} from '@/components/automations/AutomationTypes';

import { AutomationTypeSelector } from '@/components/automations/AutomationTypeSelector';
import { CommentToDmFlow } from '@/components/automations/CommentToDmFlow';
import { CommentReplyFlow } from '@/components/automations/CommentReplyFlow';
import { CommentToLeadFlow } from '@/components/automations/CommentToLeadFlow';
import { DmReplyFlow } from '@/components/automations/DmReplyFlow';
import { DmToLeadFlow } from '@/components/automations/DmToLeadFlow';
import { StoryReplyFlow } from '@/components/automations/StoryReplyFlow';
import { StoryMentionFlow } from '@/components/automations/StoryMentionFlow';
import { TriggerSection } from '@/components/automations/TriggerSection';
import { ConditionsSection } from '@/components/automations/ConditionsSection';
import { TheyWillGetSection } from '@/components/automations/TheyWillGetSection';
import { OptionalActionsSection } from '@/components/automations/OptionalActionsSection';
import { ResourceSection } from '@/components/automations/ResourceSection';
import { FollowUpSection } from '@/components/automations/FollowUpSection';
import { ValidationBar } from '@/components/automations/ValidationBar';
import { PublishModal } from '@/components/automations/PublishModal';
import { InstagramPhonePreview } from '@/components/automations/InstagramPhonePreview';
import { InstagramMediaItem } from '@/components/automations/PostSelector';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { usePlan } from '@/hooks/usePlan';

export default function CreateAutomationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get('edit');
  const showToast = useUIStore((s) => s.showToast);
  const { createAutomation, updateAutomation, publishAutomation } = useAutomations();
  const { openUpgradeModal } = usePlan();

  // Active Flow View: 'comment_to_dm' | 'comment_reply' | 'comment_to_lead' | 'dm_reply' | 'dm_to_lead' | 'story_reply' | 'story_mention' | 'picker' | 'custom'
  const [activeFlowView, setActiveFlowView] = useState<'comment_to_dm' | 'comment_reply' | 'comment_to_lead' | 'dm_reply' | 'dm_to_lead' | 'story_reply' | 'story_mention' | 'picker' | 'custom'>('comment_to_dm');

  // Single Source of Truth: Automation Draft State
  const [draft, setDraft] = useState<AutomationDraft>(DEFAULT_AUTOMATION_DRAFT);
  
  // Instagram Accounts
  const [accounts, setAccounts] = useState<ConnectedInstagramAccount[]>([]);
  
  // Modals & UI States
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isPublishSuccess, setIsPublishSuccess] = useState(false);
  const [createdAutomationId, setCreatedAutomationId] = useState<string | undefined>();
  const [mobileStudioTab, setMobileStudioTab] = useState<'editor' | 'preview'>('editor');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [editingAutomation, setEditingAutomation] = useState<any>(null);

  // Dynamic live preview state synced from whichever automation flow is active
  const [livePreviewData, setLivePreviewData] = useState<any>({});

  const handlePreviewChange = React.useCallback((data: any) => {
    setLivePreviewData((prev: any) => ({
      ...prev,
      ...data,
    }));
  }, []);

  // Restore automation if edit param is provided
  useEffect(() => {
    if (editId) {
      automationsApi.get(editId).then((res: any) => {
        if (res) {
          setEditingAutomation(res);
          const flow = res.flow_definition;
          const flowType = (flow?.type || '').toUpperCase();
          if (flowType === 'COMMENT_TO_DM' || flow?.trigger?.type === 'COMMENT' || res.trigger_type === 'COMMENT') {
            if (flowType === 'COMMENT_REPLY') {
              setActiveFlowView('comment_reply');
            } else if (flowType === 'COMMENT_TO_LEAD') {
              setActiveFlowView('comment_to_lead');
            } else {
              setActiveFlowView('comment_to_dm');
            }
          } else if (flowType === 'DM_REPLY') {
            setActiveFlowView('dm_reply');
          } else if (flowType === 'DM_TO_LEAD') {
            setActiveFlowView('dm_to_lead');
          } else if (flowType === 'STORY_REPLY') {
            setActiveFlowView('story_reply');
          } else if (flowType === 'STORY_MENTION') {
            setActiveFlowView('story_mention');
          }

          if (res.name || res.instagram_account_id || flow) {
            setDraft((prev) => ({
              ...prev,
              name: res.name || prev.name,
              instagramAccountId: res.instagram_account_id || prev.instagramAccountId,
              ...(flow && typeof flow === 'object' ? flow : {}),
            }));
          }
        }
      }).catch((e: any) => {
        console.warn('Could not fetch automation for editing:', e);
      });
    }
  }, [editId]);

  // Load connected Instagram accounts
  useEffect(() => {
    async function loadAccounts() {
      try {
        const accs = await instagramApi.listAccounts();
        setAccounts(accs || []);
        if (accs && accs.length > 0) {
          setDraft((prev) => ({
            ...prev,
            instagramAccountId: prev.instagramAccountId || accs[0].id,
          }));
        }
      } catch (e) {
        console.warn('Could not load Instagram accounts:', e);
      }
    }
    loadAccounts();
  }, []);

  const mediaQuery = useQuery({
    queryKey: ['instagram-media', draft.instagramAccountId],
    queryFn: () => instagramApi.getMedia(draft.instagramAccountId || undefined),
    enabled: !!draft.instagramAccountId,
    staleTime: 60_000,
  });
  const realPosts: InstagramMediaItem[] = useMemo(() => {
    if (mediaQuery.data) {
      return mediaQuery.data as InstagramMediaItem[];
    }
    return [];
  }, [mediaQuery.data]);
  const selectedPost: InstagramMediaItem | undefined = useMemo(
    () => realPosts.find((p) => p.id === draft.trigger.postId), [realPosts, draft.trigger.postId]);

  // Active connected account info
  const activeAccount = accounts.find((a) => a.id === draft.instagramAccountId);
  const accountHandle = activeAccount?.username || 'yourbrand';

  // Dynamic Validation Result
  const validation = useMemo(() => {
    return validateAutomationDraft(draft);
  }, [draft]);

  // Handlers for updating Draft sections
  const updateDraft = (updater: (prev: AutomationDraft) => AutomationDraft) => {
    setDraft(updater);
  };

  const handleSelectType = (opt: AutomationTypeOption) => {
    if (opt.isLocked) {
      showToast(`${opt.title} is a PRO feature. Upgrade your plan to unlock. 🔒`);
      openUpgradeModal('PRO', opt.id);
      return;
    }

    updateDraft((prev) => ({
      ...prev,
      typeId: opt.id,
      category: opt.category,
      trigger: {
        ...prev.trigger,
        type: opt.category === 'messages' ? 'DM' : opt.category === 'stories' ? 'STORY' : 'COMMENT',
      },
      name: `${opt.title} Playbook`,
    }));

    // Pre-seed live preview defaults
    setLivePreviewData({
      defaultTab: opt.category === 'stories' ? 'story' : opt.id === 'comment_reply' ? 'comments' : 'dm',
      isStoryFlow: opt.category === 'stories',
    });

    if (opt.id === 'comment_to_dm') {
      setActiveFlowView('comment_to_dm');
    } else if (opt.id === 'comment_reply') {
      setActiveFlowView('comment_reply');
    } else if (opt.id === 'comment_to_lead') {
      setActiveFlowView('comment_to_lead');
    } else if (opt.id === 'dm_reply') {
      setActiveFlowView('dm_reply');
    } else if (opt.id === 'dm_to_lead') {
      setActiveFlowView('dm_to_lead');
    } else if (opt.id === 'story_reply') {
      setActiveFlowView('story_reply');
    } else if (opt.id === 'story_mention') {
      setActiveFlowView('story_mention');
    } else {
      setActiveFlowView('custom');
    }
  };

  // Dedicated Save handler for StoryMentionFlow
  const handleSaveStoryMention = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'STORY_MENTION',
        trigger: {
          type: 'STORY_MENTION',
          replyToAll: flowData?.replyToAll,
          keywords: flowData?.keywords || [],
        },
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: flowData.name || draft.name || 'Story Mention Flow',
            description: 'Automated Direct Message Replies to Story Mentions',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'Story Mention Flow draft saved! 📁' : 'Story Mention Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: flowData.name || draft.name || 'Story Mention Flow',
          description: 'Automated Direct Message Replies to Story Mentions',
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'STORY',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'Story Mention Flow saved as draft! 📁' : 'Story Mention Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save story mention flow.');
      setIsPublishing(false);
    }
  };

  // Dedicated Save handler for StoryReplyFlow
  const handleSaveStoryReply = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'STORY_REPLY',
        trigger: {
          type: 'STORY',
          replyToAll: flowData?.replyToAll,
          keywords: flowData?.keywords || [],
        },
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: flowData.name || draft.name || 'Story Reply Flow',
            description: 'Automated Direct Message Replies to Story Interactions',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'Story Reply Flow draft saved! 📁' : 'Story Reply Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: flowData.name || draft.name || 'Story Reply Flow',
          description: 'Automated Direct Message Replies to Story Interactions',
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'STORY',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'Story Reply Flow saved as draft! 📁' : 'Story Reply Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save story reply flow.');
      setIsPublishing(false);
    }
  };

  // Dedicated Save handler for DmToLeadFlow
  const handleSaveDmToLead = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'DM_TO_LEAD',
        trigger: {
          type: 'DM',
          replyToAll: flowData?.replyToAll,
          keywords: flowData?.keywords || [],
        },
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: flowData.flowName || draft.name || 'DM to Lead Collection',
            description: 'Automated Lead Qualification & Collection from DMs',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'DM Lead Flow draft saved! 📁' : 'DM Lead Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: flowData.flowName || draft.name || 'DM to Lead Collection',
          description: 'Automated Lead Qualification & Collection from DMs',
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'DM',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'DM Lead Flow saved as draft! 📁' : 'DM Lead Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save lead flow.');
      setIsPublishing(false);
    }
  };

  // Dedicated Save handler for DmReplyFlow
  const handleSaveDmReply = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'DM_REPLY',
        trigger: {
          type: 'DM',
          replyToAll: flowData?.replyToAll,
          keywords: flowData?.keywords || [],
        },
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: flowData.name || draft.name || 'DM Reply Flow',
            description: 'Automated Direct Message Replies for Keywords',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'DM Reply Flow draft saved! 📁' : 'DM Reply Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: flowData.name || draft.name || 'DM Reply Flow',
          description: 'Automated Direct Message Replies for Keywords',
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'DM',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'DM Reply Flow saved as draft! 📁' : 'DM Reply Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save DM reply automation.');
      setIsPublishing(false);
    }
  };

  // Dedicated Save handler for CommentToLeadFlow
  const handleSaveCommentToLead = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'COMMENT_TO_LEAD',
        trigger: {
          type: 'COMMENT',
          selectedPostId: flowData?.selectedPostId,
          replyToAll: flowData?.trigger?.replyToAll ?? flowData?.replyToAll,
          keyword: flowData?.trigger?.keyword ?? flowData?.triggerKeyword,
        },
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: flowData.flowName || draft.name || 'Comment to Lead Collection',
            description: 'Automated Lead Qualification & Collection from Comments',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'Comment Lead Flow draft saved! 📁' : 'Lead Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: flowData.flowName || draft.name || 'Comment to Lead Collection',
          description: 'Automated Lead Qualification & Collection from Comments',
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'COMMENT',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'Comment Lead Flow saved as draft! 📁' : 'Lead Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save lead flow.');
      setIsPublishing(false);
    }
  };

  // Dedicated Save handler for CommentReplyFlow
  const handleSaveCommentReply = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'COMMENT_REPLY',
        trigger: {
          type: 'COMMENT',
          selectedPostId: flowData?.selectedPostId,
          replyToAll: flowData?.replyToAll,
          keywords: flowData?.keywords || [],
        },
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: draft.name || 'Comment Reply Flow',
            description: 'Automated Comment Reply public responses',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'Comment Reply Flow draft saved! 📁' : 'Comment Reply Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: draft.name || 'Comment Reply Flow',
          description: 'Automated Comment Reply public responses',
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'COMMENT',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'Comment Reply Flow saved as draft! 📁' : 'Comment Reply Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save automation.');
      setIsPublishing(false);
    }
  };

  // Dedicated Save handler for CommentToDmFlow
  const handleSaveCommentToDm = async (flowData: any) => {
    setIsPublishing(true);
    setErrorMessage(null);
    const isDraft = flowData?.status === 'DRAFT';
    try {
      const flowDef = {
        version: 2,
        type: 'COMMENT_TO_DM',
        ...flowData,
        status: isDraft ? 'DRAFT' : 'ACTIVE',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: flowData?.name || draft.name || 'Comment to DM Flow',
            description: 'Automated Comment to DM Instagram responses',
            status: isDraft ? 'DRAFT' : 'ACTIVE',
            flow_definition: flowDef,
          },
        });
        if (!isDraft) {
          await publishAutomation(editId);
        }
        showToast(isDraft ? 'Comment to DM Flow draft saved! 📁' : 'Comment to DM Flow updated & active! 🚀');
      } else {
        const created = await createAutomation({
          name: flowData?.name || draft.name || 'Comment to DM Flow',
          description: 'Automated Comment to DM Instagram responses',
          instagram_account_id: flowData?.instagram_account_id || draft.instagramAccountId || accounts[0]?.id,
          trigger_type: 'COMMENT',
          flow_definition: flowDef,
        });

        if (!isDraft && created?.id) {
          await publishAutomation(created.id);
        }

        showToast(isDraft ? 'Comment to DM Flow saved as draft! 📁' : 'Comment to DM Flow published & active! 🚀');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save automation.');
      setIsPublishing(false);
    }
  };

  const handleSaveDraft = async () => {
    setIsPublishing(true);
    setErrorMessage(null);
    try {
      const flowDef = {
        version: 2,
        ...draft,
        status: 'DRAFT',
      };

      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: draft.name || 'Untitled Draft Automation',
            description: `Draft playbook for ${draft.typeId}`,
            status: 'DRAFT',
            flow_definition: flowDef,
          },
        });
        showToast('Automation draft updated! 📁');
      } else {
        await createAutomation({
          name: draft.name || 'Untitled Draft Automation',
          description: `Draft playbook for ${draft.typeId}`,
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: draft.trigger.type,
          flow_definition: flowDef,
        });
        showToast('Automation saved as draft! 📁');
      }

      router.push('/dashboard/automations');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save draft.');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleConfirmPublish = async () => {
    setIsPublishing(true);
    setErrorMessage(null);

    const flowDefinition = {
      version: 2,
      ...draft,
      status: 'ACTIVE',
      actions: [
        draft.publicReply.enabled && {
          type: 'PUBLIC_REPLY',
          messages: draft.publicReply.messages,
        },
        draft.privateDm.enabled && {
          type: 'PRIVATE_DM',
          text: draft.privateDm.openingMessage,
          button_text: draft.privateDm.buttonText,
        },
        draft.optionalActions.followerGate && {
          type: 'FOLLOWER_GATE',
          message: draft.optionalActions.followerGateMessage,
        },
        draft.optionalActions.emailCapture && {
          type: 'EMAIL_CAPTURE',
          message: draft.optionalActions.emailCaptureMessage,
        },
        {
          type: 'RESOURCE_DELIVERY',
          text: draft.resource.message,
          url: draft.resource.url,
          button_text: draft.resource.buttonText,
        },
        draft.followUp.enabled && {
          type: 'FOLLOWUP_REMINDER',
          delay_minutes: draft.followUp.delayMinutes,
          message: draft.followUp.message,
        },
      ].filter(Boolean),
    };

    try {
      if (editId) {
        await updateAutomation({
          id: editId,
          data: {
            name: draft.name || 'Instagram Automation',
            description: `Active ${draft.typeId} automation`,
            status: 'ACTIVE',
            flow_definition: flowDefinition,
          },
        });
        setCreatedAutomationId(editId);
        await publishAutomation(editId);
      } else {
        const created = await createAutomation({
          name: draft.name || 'Instagram Automation',
          description: `Active ${draft.typeId} automation`,
          instagram_account_id: draft.instagramAccountId || accounts[0]?.id,
          trigger_type: draft.trigger.type,
          flow_definition: flowDefinition,
        });

        if (created?.id) {
          setCreatedAutomationId(created.id);
          await publishAutomation(created.id);
        }
      }

      setIsPublishSuccess(true);
      showToast('Automation published and activated! 🚀');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to publish automation.');
      setIsPublishing(false);
    }
  };

  const handleResetForAnother = () => {
    setDraft(DEFAULT_AUTOMATION_DRAFT);
    setIsPublishSuccess(false);
    setPublishModalOpen(false);
    setCreatedAutomationId(undefined);
    setActiveFlowView('picker');
  };

  // Helper layout that wraps any automation flow in a coordinated 2-column studio on desktop and seamless tabbed studio on tablet & mobile
  const renderFlowWithPreview = (
    flowBadge: string,
    flowContent: React.ReactNode
  ) => {
    return (
      <div className="w-full max-w-[1600px] mx-auto pb-16 text-[#111110] px-3 sm:px-6 lg:px-8 py-4">
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 text-xs rounded-2xl flex items-center justify-between animate-in fade-in">
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-red-700 hover:text-red-900 font-bold ml-2 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* TABLET & MOBILE (< 1200px): SLEEK SEGMENTED VIEW SWITCHER */}
        <div className="xl:hidden flex items-center justify-center p-1 bg-[#F4F4F0] border border-[#ECECE8] rounded-2xl mb-5 max-w-sm mx-auto shadow-2xs">
          <button
            type="button"
            onClick={() => setMobileStudioTab('editor')}
            className={`flex-1 py-2 px-3 text-xs font-bold rounded-xl transition-all cursor-pointer ${
              mobileStudioTab === 'editor'
                ? 'bg-white text-[#111110] shadow-xs'
                : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            ✏️ Configure Flow
          </button>
          <button
            type="button"
            onClick={() => setMobileStudioTab('preview')}
            className={`flex-1 py-2 px-3 text-xs font-bold rounded-xl transition-all cursor-pointer ${
              mobileStudioTab === 'preview'
                ? 'bg-white text-[#064125] shadow-xs'
                : 'text-[#70706B] hover:text-[#111110]'
            }`}
          >
            📱 Live Preview ({flowBadge})
          </button>
        </div>

        {/* MAIN STUDIO GRID */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
          {/* FLOW STUDIO: Always visible on desktop, or when mobileStudioTab is 'editor' */}
          <div
            className={`min-w-0 xl:col-span-7 2xl:col-span-8 ${
              mobileStudioTab === 'preview' ? 'hidden xl:block' : 'block'
            }`}
          >
            {flowContent}
          </div>

          {/* RIGHT COLUMN: STICKY LIVE INSTAGRAM SIMULATOR (>= 1200px) OR CENTERED PREVIEW (< 1200px) */}
          <aside
            className={`xl:col-span-5 2xl:col-span-4 xl:sticky xl:top-6 ${
              mobileStudioTab === 'editor' ? 'hidden xl:block' : 'block'
            }`}
          >
            <div className="bg-white border border-[#ECECE8] rounded-3xl p-5 shadow-xs space-y-4 max-w-md mx-auto">
              <div className="flex items-center justify-between border-b border-[#F4F4F0] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse" />
                  <span className="text-xs font-bold text-[#111110]">Live Instagram Simulator</span>
                </div>
                <span className="text-[10px] font-semibold text-[#15803D] bg-[#F0FDF4] px-2.5 py-0.5 rounded-full uppercase tracking-wide">
                  {flowBadge}
                </span>
              </div>

              {/* Reactive Simulator consuming the exact live flow state */}
              <div className="flex justify-center">
                <InstagramPhonePreview
                  accountName={accountHandle}
                  avatarUrl={activeAccount?.profile_pic_url || null}
                  selectedPost={livePreviewData.selectedPost || selectedPost}
                  keywords={livePreviewData.keywords || draft.conditions.keywords}
                  triggerMode={livePreviewData.triggerMode}
                  publicReplyEnabled={livePreviewData.publicReplyEnabled ?? draft.publicReply.enabled}
                  publicReplyText={livePreviewData.publicReplyText ?? draft.publicReply.messages[0] ?? ''}
                  openingDmEnabled={livePreviewData.openingDmEnabled ?? draft.privateDm.enabled}
                  openingDmText={livePreviewData.openingDmText ?? draft.privateDm.openingMessage}
                  openingDmButtonText={livePreviewData.openingDmButtonText ?? draft.privateDm.buttonText}
                  askFollowEnabled={livePreviewData.askFollowEnabled ?? draft.optionalActions.followerGate}
                  askFollowText={livePreviewData.askFollowText ?? draft.optionalActions.followerGateMessage}
                  askEmailEnabled={livePreviewData.askEmailEnabled ?? draft.optionalActions.emailCapture}
                  askEmailText={livePreviewData.askEmailText ?? draft.optionalActions.emailCaptureMessage}
                  deliveryText={livePreviewData.deliveryText ?? draft.resource.message}
                  deliveryLinkUrl={livePreviewData.deliveryLinkUrl ?? draft.resource.url}
                  deliveryLinkButtonText={livePreviewData.deliveryLinkButtonText ?? draft.resource.buttonText}
                  followupEnabled={livePreviewData.followupEnabled ?? draft.followUp.enabled}
                  followupHours={livePreviewData.followupHours ?? Math.round(draft.followUp.delayMinutes / 60)}
                  followupText={livePreviewData.followupText ?? draft.followUp.message}
                  defaultTab={livePreviewData.defaultTab}
                  isStoryFlow={livePreviewData.isStoryFlow}
                  storyImageUrl={livePreviewData.storyImageUrl}
                />
              </div>

              {/* Mobile Return to Editor Button */}
              <div className="xl:hidden pt-2 border-t border-[#ECECE8]">
                <button
                  type="button"
                  onClick={() => setMobileStudioTab('editor')}
                  className="w-full py-2.5 bg-[#F4F4F0] hover:bg-[#ECECE8] text-[#111110] font-bold text-xs rounded-xl transition-colors cursor-pointer"
                >
                  ← Return to Flow Editor
                </button>
              </div>
            </div>
          </aside>
        </div>

        {/* CONFIRMATION & SUCCESS MODAL */}
        <PublishModal
          isOpen={publishModalOpen}
          onClose={() => setPublishModalOpen(false)}
          onConfirmPublish={handleConfirmPublish}
          isPublishing={isPublishing}
          draft={draft}
          isSuccess={isPublishSuccess}
          createdId={createdAutomationId}
          onResetForAnother={handleResetForAnother}
        />
      </div>
    );
  };

  // VIEW 1: Clean, Full-Width Playbook Picker (NO Preview Simulator here)
  if (activeFlowView === 'picker') {
    return (
      <div className="max-w-5xl mx-auto pb-28 text-[#111110] px-4 sm:px-6 py-6">
        {/* Global Error Notice */}
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 text-xs rounded-2xl flex items-center justify-between animate-in fade-in">
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-red-700 hover:text-red-900 font-bold ml-2 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Section 1: Choose Playbook */}
        <div>
          <AutomationTypeSelector
            selectedTypeId={draft.typeId}
            onSelectType={handleSelectType}
          />
        </div>

        {/* Confirmation & Success Modal */}
        <PublishModal
          isOpen={publishModalOpen}
          onClose={() => setPublishModalOpen(false)}
          onConfirmPublish={handleConfirmPublish}
          isPublishing={isPublishing}
          draft={draft}
          isSuccess={isPublishSuccess}
          createdId={createdAutomationId}
          onResetForAnother={handleResetForAnother}
        />

        {/* Upgrade Modal for Locked Pro Features */}
        <UpgradeModal />
      </div>
    );
  }

  // VIEW 2: Dedicated "Comment to DM Flow" Studio matching Reference Image 1
  if (activeFlowView === 'comment_to_dm') {
    return (
      <div className="w-full text-[#111110]">
        <CommentToDmFlow
          onBack={() => setActiveFlowView('picker')}
          onSave={handleSaveCommentToDm}
          accountName={accountHandle}
          accountId={draft.instagramAccountId}
          accounts={accounts}
          onSelectAccount={(acc) => {
            setDraft((prev) => ({ ...prev, instagramAccountId: acc.id }));
          }}
          isSaving={isPublishing}
          onPreviewChange={handlePreviewChange}
          initialData={editingAutomation?.flow_definition || editingAutomation}
        />
        <PublishModal
          isOpen={publishModalOpen}
          onClose={() => setPublishModalOpen(false)}
          onConfirmPublish={handleConfirmPublish}
          isPublishing={isPublishing}
          draft={draft}
          isSuccess={isPublishSuccess}
          createdId={createdAutomationId}
          onResetForAnother={handleResetForAnother}
        />
        <UpgradeModal />
      </div>
    );
  }

  // VIEW 3: Dedicated "Comment Reply Flow" Studio with Live Preview Setup
  if (activeFlowView === 'comment_reply') {
    return renderFlowWithPreview(
      'Comment Reply',
      <CommentReplyFlow
        onBack={() => setActiveFlowView('picker')}
        onSave={handleSaveCommentReply}
        accountName={accountHandle}
        isSaving={isPublishing}
        onPreviewChange={handlePreviewChange}
        initialData={editingAutomation?.flow_definition || editingAutomation}
      />
    );
  }

  // VIEW 4: Dedicated "Comment to Lead Collection" Studio with Live Preview Setup
  if (activeFlowView === 'comment_to_lead') {
    return renderFlowWithPreview(
      'Comment to Lead',
      <CommentToLeadFlow
        onBack={() => setActiveFlowView('picker')}
        onSave={handleSaveCommentToLead}
        accountName={accountHandle}
        isSaving={isPublishing}
        onPreviewChange={handlePreviewChange}
        initialData={editingAutomation?.flow_definition || editingAutomation}
      />
    );
  }

  // VIEW 5: Dedicated "DM Reply Flow" Studio with Live Preview Setup
  if (activeFlowView === 'dm_reply') {
    return renderFlowWithPreview(
      'DM Reply',
      <DmReplyFlow
        onBack={() => setActiveFlowView('picker')}
        onSave={handleSaveDmReply}
        accountName={accountHandle}
        isSaving={isPublishing}
        onPreviewChange={handlePreviewChange}
      />
    );
  }

  // VIEW 6: Dedicated "DM to Lead Collection" Studio with Live Preview Setup
  if (activeFlowView === 'dm_to_lead') {
    return renderFlowWithPreview(
      'DM to Lead',
      <DmToLeadFlow
        onBack={() => setActiveFlowView('picker')}
        onSave={handleSaveDmToLead}
        accountName={accountHandle}
        isSaving={isPublishing}
        onPreviewChange={handlePreviewChange}
      />
    );
  }

  // VIEW 7: Dedicated "Story Reply Flow" Studio with Live Preview Setup
  if (activeFlowView === 'story_reply') {
    return renderFlowWithPreview(
      'Story Reply',
      <StoryReplyFlow
        onBack={() => setActiveFlowView('picker')}
        onSave={handleSaveStoryReply}
        accountName={accountHandle}
        isSaving={isPublishing}
        onPreviewChange={handlePreviewChange}
      />
    );
  }

  // VIEW 8: Dedicated "Story Mention Flow" Studio with Live Preview Setup
  if (activeFlowView === 'story_mention') {
    return renderFlowWithPreview(
      'Story Mention',
      <StoryMentionFlow
        onBack={() => setActiveFlowView('picker')}
        onSave={handleSaveStoryMention}
        accountName={accountHandle}
        isSaving={isPublishing}
        onPreviewChange={handlePreviewChange}
      />
    );
  }

  // VIEW 9: Custom Flow Studio with Live Preview Setup
  return renderFlowWithPreview(
    'Custom Builder',
    <div className="space-y-6">
      <div className="flex items-center justify-between pb-2">
        <button
          type="button"
          onClick={() => setActiveFlowView('picker')}
          className="text-xs font-semibold text-[#70706B] hover:text-[#111110] flex items-center gap-1.5 cursor-pointer"
        >
          <span>← Back to Playbook Picker</span>
        </button>
      </div>

      {/* Section 2: When this happens */}
      <TriggerSection
        scope={draft.trigger.scope}
        onScopeChange={(scope) =>
          updateDraft((prev) => ({
            ...prev,
            trigger: { ...prev.trigger, scope },
          }))
        }
        selectedPostId={draft.trigger.postId}
        onSelectPost={(post) =>
          updateDraft((prev) => ({
            ...prev,
            trigger: {
              ...prev.trigger,
              postId: post.id,
              reelId: post.type === 'REEL' ? post.id : undefined,
            },
          }))
        }
        posts={realPosts}
        postsLoading={mediaQuery.isLoading}
        postsError={mediaQuery.isError ? (mediaQuery.error as Error).message : null}
      />

      {/* Section 3: And these conditions */}
      <ConditionsSection
        matchMode={draft.conditions.matchMode}
        onMatchModeChange={(matchMode) =>
          updateDraft((prev) => ({
            ...prev,
            conditions: { ...prev.conditions, matchMode },
          }))
        }
        keywords={draft.conditions.keywords}
        onKeywordsChange={(keywords) =>
          updateDraft((prev) => ({
            ...prev,
            conditions: { ...prev.conditions, keywords },
          }))
        }
      />

      {/* Section 4: They will get */}
      <TheyWillGetSection
        publicReplyEnabled={draft.publicReply.enabled}
        onPublicReplyToggle={(enabled) =>
          updateDraft((prev) => ({
            ...prev,
            publicReply: { ...prev.publicReply, enabled },
          }))
        }
        publicReplyMessages={draft.publicReply.messages}
        onPublicReplyMessagesChange={(messages) =>
          updateDraft((prev) => ({
            ...prev,
            publicReply: { ...prev.publicReply, messages },
          }))
        }
        openingDmEnabled={draft.privateDm.enabled}
        onOpeningDmToggle={(enabled) =>
          updateDraft((prev) => ({
            ...prev,
            privateDm: { ...prev.privateDm, enabled },
          }))
        }
        openingDmText={draft.privateDm.openingMessage}
        onOpeningDmTextChange={(openingMessage) =>
          updateDraft((prev) => ({
            ...prev,
            privateDm: { ...prev.privateDm, openingMessage },
          }))
        }
        openingDmButtonText={draft.privateDm.buttonText}
        onOpeningDmButtonTextChange={(buttonText) =>
          updateDraft((prev) => ({
            ...prev,
            privateDm: { ...prev.privateDm, buttonText },
          }))
        }
      />

      {/* Section 5: Optional actions */}
      <OptionalActionsSection
        followerGate={draft.optionalActions.followerGate}
        onFollowerGateToggle={(followerGate) =>
          updateDraft((prev) => ({
            ...prev,
            optionalActions: { ...prev.optionalActions, followerGate },
          }))
        }
        followerGateMessage={draft.optionalActions.followerGateMessage}
        onFollowerGateMessageChange={(followerGateMessage) =>
          updateDraft((prev) => ({
            ...prev,
            optionalActions: { ...prev.optionalActions, followerGateMessage },
          }))
        }
        emailCapture={draft.optionalActions.emailCapture}
        onEmailCaptureToggle={(emailCapture) =>
          updateDraft((prev) => ({
            ...prev,
            optionalActions: { ...prev.optionalActions, emailCapture },
          }))
        }
        emailCaptureMessage={draft.optionalActions.emailCaptureMessage}
        onEmailCaptureMessageChange={(emailCaptureMessage) =>
          updateDraft((prev) => ({
            ...prev,
            optionalActions: { ...prev.optionalActions, emailCaptureMessage },
          }))
        }
        tagContact={draft.optionalActions.tagContact}
        onTagContactToggle={(tagContact) =>
          updateDraft((prev) => ({
            ...prev,
            optionalActions: { ...prev.optionalActions, tagContact },
          }))
        }
        tagName={draft.optionalActions.tagName}
        onTagNameChange={(tagName) =>
          updateDraft((prev) => ({
            ...prev,
            optionalActions: { ...prev.optionalActions, tagName },
          }))
        }
      />

      {/* Section 6: Deliver resource */}
      <ResourceSection
        message={draft.resource.message}
        onMessageChange={(message) =>
          updateDraft((prev) => ({
            ...prev,
            resource: { ...prev.resource, message },
          }))
        }
        url={draft.resource.url}
        onUrlChange={(url) =>
          updateDraft((prev) => ({
            ...prev,
            resource: { ...prev.resource, url },
          }))
        }
        buttonText={draft.resource.buttonText}
        onButtonTextChange={(buttonText) =>
          updateDraft((prev) => ({
            ...prev,
            resource: { ...prev.resource, buttonText },
          }))
        }
        customTitle={draft.resource.customTitle}
        onCustomTitleChange={(customTitle) =>
          updateDraft((prev) => ({
            ...prev,
            resource: { ...prev.resource, customTitle },
          }))
        }
      />

      {/* Section 7: Follow-up */}
      <FollowUpSection
        enabled={draft.followUp.enabled}
        onToggle={(enabled) =>
          updateDraft((prev) => ({
            ...prev,
            followUp: { ...prev.followUp, enabled },
          }))
        }
        delayMinutes={draft.followUp.delayMinutes}
        onDelayMinutesChange={(delayMinutes) =>
          updateDraft((prev) => ({
            ...prev,
            followUp: { ...prev.followUp, delayMinutes },
          }))
        }
        message={draft.followUp.message}
        onMessageChange={(message) =>
          updateDraft((prev) => ({
            ...prev,
            followUp: { ...prev.followUp, message },
          }))
        }
      />

      {/* Section 8: Validation */}
      <ValidationBar
        isValid={validation.isValid}
        items={validation.items}
        onPublishClick={() => setPublishModalOpen(true)}
        isSaving={isPublishing}
      />
    </div>
  );
}
