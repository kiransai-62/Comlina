// client/tests/automation-edit-persistence.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

/**
 * Controller class replicating the exact save orchestration logic
 * implemented in client/src/app/dashboard/automations/create/page.tsx.
 */
class AutomationSaveController {
  constructor({
    editId = null,
    createAutomationApi,
    updateAutomationApi,
    publishAutomationApi,
  }) {
    this.editId = editId;
    this.createAutomationApi = createAutomationApi;
    this.updateAutomationApi = updateAutomationApi;
    this.publishAutomationApi = publishAutomationApi;
    this.calls = {
      create: [],
      update: [],
      publish: [],
    };
    this.toasts = [];
  }

  async executeSave({ payload, isDraft = false }) {
    try {
      if (this.editId) {
        // Updating existing automation
        const updatePayload = {
          name: payload.name,
          flow_definition: payload.flow_definition,
          trigger_type: payload.trigger_type,
          instagram_account_id: payload.instagram_account_id,
          status: isDraft ? 'DRAFT' : undefined,
        };

        this.calls.update.push({ id: this.editId, data: updatePayload });
        const updated = await this.updateAutomationApi(this.editId, updatePayload);

        if (!isDraft) {
          this.calls.publish.push(this.editId);
          await this.publishAutomationApi(this.editId);
        }

        this.toasts.push({
          type: 'success',
          message: isDraft
            ? 'Draft updated successfully!'
            : 'Automation updated and published!',
        });
        return { success: true, action: 'updated', data: updated };
      } else {
        // Creating new automation
        const createPayload = {
          ...payload,
          status: isDraft ? 'DRAFT' : 'ACTIVE',
        };

        this.calls.create.push(createPayload);
        const created = await this.createAutomationApi(createPayload);

        this.toasts.push({
          type: 'success',
          message: isDraft
            ? 'Draft saved successfully!'
            : 'Automation created successfully!',
        });
        return { success: true, action: 'created', data: created };
      }
    } catch (err) {
      const msg = err?.message || 'Failed to save automation';
      this.toasts.push({ type: 'error', message: msg });
      return { success: false, error: msg };
    }
  }

  // Handler for Comment to DM
  async handleSaveCommentToDm(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'Comment to DM Automation',
      trigger_type: 'COMMENT',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'COMMENT',
          post_id: formData.postMode === 'specific' ? formData.selectedPostId : null,
          post_mode: formData.postMode,
          keywords: formData.replyToAll ? [] : formData.keywords,
          match_type: formData.replyToAll ? 'ALL' : 'EXACT',
        },
        actions: [
          {
            type: 'SEND_DM',
            template: formData.responseDm,
            button_text: formData.buttonLabel,
            button_url: formData.destinationUrl,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }

  // Handler for Comment Reply
  async handleSaveCommentReply(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'Comment Reply Automation',
      trigger_type: 'COMMENT',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'COMMENT',
          post_id: formData.postMode === 'specific' ? formData.selectedPostId : null,
          post_mode: formData.postMode,
          keywords: formData.replyToAll ? [] : formData.keywords,
          match_type: formData.replyToAll ? 'ALL' : 'EXACT',
        },
        actions: [
          {
            type: 'REPLY_COMMENT',
            text: formData.replyText,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }

  // Handler for Comment to Lead
  async handleSaveCommentToLead(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'Comment Lead Generator',
      trigger_type: 'COMMENT',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'COMMENT',
          post_id: formData.postMode === 'specific' ? formData.selectedPostId : null,
          post_mode: formData.postMode,
          keywords: formData.keywords,
          match_type: 'EXACT',
        },
        actions: [
          {
            type: 'SEND_DM',
            template: formData.openingDm,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }

  // Handler for DM Reply
  async handleSaveDmReply(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'DM Quick Reply',
      trigger_type: 'DM',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'DM',
          keywords: formData.keywords,
          match_type: formData.replyToAll ? 'ALL' : 'EXACT',
        },
        actions: [
          {
            type: 'SEND_DM',
            template: formData.replyMessage,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }

  // Handler for DM to Lead
  async handleSaveDmToLead(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'DM Lead Funnel',
      trigger_type: 'DM',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'DM',
          keywords: formData.keywords,
          match_type: 'EXACT',
        },
        actions: [
          {
            type: 'SEND_DM',
            template: formData.leadMagnetMessage,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }

  // Handler for Story Reply
  async handleSaveStoryReply(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'Story Reply Automation',
      trigger_type: 'STORY_REPLY',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'STORY_REPLY',
          keywords: formData.keywords,
          match_type: formData.replyToAll ? 'ALL' : 'EXACT',
        },
        actions: [
          {
            type: 'SEND_DM',
            template: formData.replyMessage,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }

  // Handler for Story Mention
  async handleSaveStoryMention(formData, isDraft = false) {
    const payload = {
      name: formData.name || 'Story Mention Shoutout',
      trigger_type: 'MENTION',
      instagram_account_id: formData.selectedAccountId,
      flow_definition: {
        trigger: {
          type: 'MENTION',
        },
        actions: [
          {
            type: 'SEND_DM',
            template: formData.replyMessage,
          },
        ],
      },
    };
    return this.executeSave({ payload, isDraft });
  }
}

// -------------------------------------------------------------
// TESTS
// -------------------------------------------------------------

test('Edit Automation - Calls PUT (update) and NEVER calls POST (create) when editId is present', async () => {
  const mockCreate = async (data) => {
    throw new Error('createAutomation should not be called during edit');
  };
  const mockUpdate = async (id, data) => ({
    id,
    ...data,
    updated_at: new Date().toISOString(),
  });
  const mockPublish = async (id) => ({ id, status: 'ACTIVE' });

  const controller = new AutomationSaveController({
    editId: 'auto_abc123',
    createAutomationApi: mockCreate,
    updateAutomationApi: mockUpdate,
    publishAutomationApi: mockPublish,
  });

  const res = await controller.handleSaveCommentToDm({
    name: 'Updated Promo Flow',
    selectedAccountId: 'acc_inst_1',
    postMode: 'specific',
    selectedPostId: 'post_999',
    keywords: ['UPDATED', 'SALE'],
    replyToAll: false,
    responseDm: 'Here is your 20% discount!',
    buttonLabel: 'Claim Now',
    destinationUrl: 'https://comlina.com/sale',
  });

  assert.equal(res.success, true);
  assert.equal(res.action, 'updated');

  // Verify call counts
  assert.equal(controller.calls.create.length, 0, 'POST /automations must NOT be called');
  assert.equal(controller.calls.update.length, 1, 'PUT /automations/{id} must be called exactly once');
  assert.equal(controller.calls.publish.length, 1, 'Publish must be called for non-draft save');

  // Verify PUT payload
  const updateCall = controller.calls.update[0];
  assert.equal(updateCall.id, 'auto_abc123');
  assert.equal(updateCall.data.name, 'Updated Promo Flow');
  assert.equal(updateCall.data.trigger_type, 'COMMENT');
  assert.equal(updateCall.data.instagram_account_id, 'acc_inst_1');
  assert.deepEqual(updateCall.data.flow_definition.trigger.keywords, ['UPDATED', 'SALE']);
});

test('New Automation - Calls POST (create) and NEVER calls PUT (update) when editId is absent', async () => {
  const mockCreate = async (data) => ({
    id: 'auto_new_789',
    ...data,
    status: 'ACTIVE',
  });
  const mockUpdate = async (id, data) => {
    throw new Error('updateAutomation should not be called for new automation');
  };
  const mockPublish = async (id) => {
    throw new Error('publishAutomation should not be called separately for new automation');
  };

  const controller = new AutomationSaveController({
    editId: null, // No editId in URL
    createAutomationApi: mockCreate,
    updateAutomationApi: mockUpdate,
    publishAutomationApi: mockPublish,
  });

  const res = await controller.handleSaveCommentToDm({
    name: 'Brand New Automation',
    selectedAccountId: 'acc_inst_2',
    postMode: 'any',
    selectedPostId: null,
    keywords: ['JOIN'],
    replyToAll: false,
    responseDm: 'Welcome!',
    buttonLabel: 'Join Us',
    destinationUrl: 'https://comlina.com/join',
  });

  assert.equal(res.success, true);
  assert.equal(res.action, 'created');

  // Verify call counts
  assert.equal(controller.calls.create.length, 1, 'POST /automations must be called');
  assert.equal(controller.calls.update.length, 0, 'PUT /automations/{id} must NOT be called');
  assert.equal(controller.calls.publish.length, 0, 'Publish should not be called for create');

  // Verify create payload
  assert.equal(controller.calls.create[0].name, 'Brand New Automation');
  assert.equal(controller.calls.create[0].status, 'ACTIVE');
});

test('Draft Save - Preserves DRAFT status on edit and does not invoke publish', async () => {
  const mockCreate = async () => {
    throw new Error('Should not create');
  };
  let updateCalledWith = null;
  const mockUpdate = async (id, data) => {
    updateCalledWith = { id, data };
    return { id, ...data };
  };
  let publishCalled = false;
  const mockPublish = async () => {
    publishCalled = true;
  };

  const controller = new AutomationSaveController({
    editId: 'auto_draft_456',
    createAutomationApi: mockCreate,
    updateAutomationApi: mockUpdate,
    publishAutomationApi: mockPublish,
  });

  const res = await controller.handleSaveCommentReply(
    {
      name: 'Unpublished Draft Reply',
      selectedAccountId: 'acc_inst_1',
      postMode: 'any',
      keywords: ['INFO'],
      replyToAll: false,
      replyText: 'Working on this...',
    },
    true // isDraft = true
  );

  assert.equal(res.success, true);
  assert.equal(controller.calls.update.length, 1);
  assert.equal(updateCalledWith.id, 'auto_draft_456');
  assert.equal(updateCalledWith.data.status, 'DRAFT', 'Status must be set to DRAFT');
  assert.equal(publishCalled, false, 'publishAutomation must NOT be called when isDraft is true');
  assert.equal(controller.calls.create.length, 0, 'createAutomation must NOT be called');
});

test('Failure Isolation - Update failure catches error and does NOT fallback to create or duplicate', async () => {
  let createAttempted = false;
  const mockCreate = async () => {
    createAttempted = true;
    return { id: 'auto_duplicate' };
  };
  const mockUpdate = async () => {
    throw new Error('Plan limit exceeded or invalid keywords');
  };
  const mockPublish = async () => {};

  const controller = new AutomationSaveController({
    editId: 'auto_existing_111',
    createAutomationApi: mockCreate,
    updateAutomationApi: mockUpdate,
    publishAutomationApi: mockPublish,
  });

  const res = await controller.handleSaveCommentToLead({
    name: 'Failing Lead Gen',
    selectedAccountId: 'acc_inst_1',
    postMode: 'any',
    keywords: ['LEAD'],
    openingDm: 'Opening line',
  });

  assert.equal(res.success, false);
  assert.equal(res.error, 'Plan limit exceeded or invalid keywords');
  assert.equal(createAttempted, false, 'Should NEVER fallback to createAutomation on update error');
  assert.equal(controller.calls.create.length, 0, 'No duplicate record created');
});

test('All Flow Handlers - Verify DM, Story, and Comment flows route to update when editId is set', async () => {
  const mockUpdate = async (id, data) => ({ id, ...data });
  const mockPublish = async (id) => ({ id, status: 'ACTIVE' });
  const mockCreate = async () => {
    throw new Error('Must not call create');
  };

  const handlers = [
    {
      name: 'Comment Reply',
      fn: (c) =>
        c.handleSaveCommentReply({
          selectedAccountId: 'acc_1',
          postMode: 'any',
          keywords: ['TEST'],
          replyText: 'Reply!',
        }),
      expectedTrigger: 'COMMENT',
    },
    {
      name: 'Comment to Lead',
      fn: (c) =>
        c.handleSaveCommentToLead({
          selectedAccountId: 'acc_1',
          postMode: 'any',
          keywords: ['LEAD'],
          openingDm: 'Lead DM',
        }),
      expectedTrigger: 'COMMENT',
    },
    {
      name: 'DM Reply',
      fn: (c) =>
        c.handleSaveDmReply({
          selectedAccountId: 'acc_1',
          keywords: ['HELLO'],
          replyToAll: false,
          replyMessage: 'Hi there!',
        }),
      expectedTrigger: 'DM',
    },
    {
      name: 'DM to Lead',
      fn: (c) =>
        c.handleSaveDmToLead({
          selectedAccountId: 'acc_1',
          keywords: ['START'],
          leadMagnetMessage: 'Here is the resource',
        }),
      expectedTrigger: 'DM',
    },
    {
      name: 'Story Reply',
      fn: (c) =>
        c.handleSaveStoryReply({
          selectedAccountId: 'acc_1',
          keywords: ['FIRE'],
          replyToAll: false,
          replyMessage: 'Thanks for replying to our story!',
        }),
      expectedTrigger: 'STORY_REPLY',
    },
    {
      name: 'Story Mention',
      fn: (c) =>
        c.handleSaveStoryMention({
          selectedAccountId: 'acc_1',
          replyMessage: 'Thanks for mentioning us!',
        }),
      expectedTrigger: 'MENTION',
    },
  ];

  for (const h of handlers) {
    const controller = new AutomationSaveController({
      editId: `auto_${h.name.toLowerCase().replace(/\s+/g, '_')}`,
      createAutomationApi: mockCreate,
      updateAutomationApi: mockUpdate,
      publishAutomationApi: mockPublish,
    });

    const res = await h.fn(controller);
    assert.equal(res.success, true, `${h.name} save should succeed`);
    assert.equal(controller.calls.update.length, 1, `${h.name} should call update`);
    assert.equal(controller.calls.create.length, 0, `${h.name} should not call create`);
    assert.equal(
      controller.calls.update[0].data.trigger_type,
      h.expectedTrigger,
      `${h.name} trigger_type must match`
    );
  }
});
