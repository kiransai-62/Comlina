// client/src/features/instagram/useInstagramConnection.ts
'use client';

import { useQuery } from '@tanstack/react-query';
import { instagramApi } from './api';
import { ConnectedInstagramAccount, InstagramConnectionState } from './types';

export function useInstagramConnection() {
  const {
    data: accounts = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<ConnectedInstagramAccount[]>({
    queryKey: ['instagram-accounts'],
    queryFn: () => instagramApi.listAccounts(),
    staleTime: 60_000, // cache for 1 minute to prevent constant re-fetching across routes
    retry: 2,
  });

  const primaryAccount = accounts && accounts.length > 0 ? accounts[0] : null;

  // Single source of truth state machine
  let connectionState: InstagramConnectionState = 'checking';

  if (isLoading) {
    connectionState = 'checking';
  } else if (isError) {
    connectionState = 'error';
  } else if (!accounts || accounts.length === 0) {
    connectionState = 'disconnected';
  } else if (
    primaryAccount &&
    (primaryAccount.status === 'REAUTHORIZATION_REQUIRED' ||
      primaryAccount.status === 'EXPIRED' ||
      primaryAccount.is_active === false ||
      primaryAccount.isActive === false)
  ) {
    connectionState = 'reauthorization_required';
  } else {
    connectionState = 'connected';
  }

  const startConnect = async () => {
    try {
      const redirectUri =
        typeof window !== 'undefined'
          ? `${window.location.origin}/connect/instagram`
          : undefined;
      const res = await instagramApi.getConnectUrl(redirectUri);
      if (res?.authorization_url) {
        window.location.href = res.authorization_url;
      } else {
        throw new Error('No authorization URL returned from server.');
      }
    } catch (err: any) {
      console.error('Failed to start Instagram connection:', err);
      alert(`Could not start Instagram connection: ${err.message || err}`);
    }
  };

  return {
    connectionState,
    accounts,
    primaryAccount,
    isConnected: connectionState === 'connected',
    isChecking: connectionState === 'checking',
    needsReauth: connectionState === 'reauthorization_required',
    isLoading,
    isError,
    error,
    refetch,
    startConnect,
  };
}

export default useInstagramConnection;
