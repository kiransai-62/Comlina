// client/src/features/pwa/types.ts

export type PwaPromptState = 
  | 'IDLE'                // Not shown yet or waiting for timer/eligibility
  | 'DEFAULT'             // State 1: Active prompt with actions
  | 'INSTALLING'          // State 2: Native prompt invoked, waiting for response
  | 'ACCEPTED'            // State 3: Installation accepted/confirmed
  | 'DISMISSED'           // State 4: User clicked "Maybe later" or close
  | 'MANUAL_INSTRUCTIONS' // State 5: iOS or manual step-by-step instructions
  | 'ALREADY_INSTALLED'   // State 6: App is running in standalone mode
  | 'UNAVAILABLE';        // State 7: Installation is not supported on this browser

export type PwaPlatform = 'chromium' | 'ios' | 'other';

export interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

export interface PwaConfig {
  /**
   * Number of days to suppress the prompt after the user dismisses it.
   * Default: 7 days.
   */
  cooldownDays?: number;

  /**
   * Number of seconds of active use before showing the prompt.
   * Default: 30 seconds.
   */
  delaySeconds?: number;

  /**
   * Prefix for storage keys.
   */
  storagePrefix?: string;

  /**
   * If true, bypasses the delay timer (useful for testing or manual triggers).
   */
  immediate?: boolean;
}
