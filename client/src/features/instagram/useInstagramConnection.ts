// client/src/features/instagram/useInstagramConnection.ts
'use client';

import { useQuery } from '@tanstack/react-query';
import { instagramApi } from './api';
import { ConnectedInstagramAccount, InstagramConnectionState, InstagramConnectionStatusResponse } from './types';

export function useInstagramConnection() {
  const {
    data: statusData,
    isLoading: isStatusLoading,
    isError: isStatusError,
    error: statusError,
    refetch: refetchStatus,
  } = useQuery<InstagramConnectionStatusResponse>({
    queryKey: ['instagram-connection-status'],
    queryFn: () => instagramApi.getConnectionStatus(),
    staleTime: 30_000,
    retry: 2,
  });

  const {
    data: accounts = [],
    isLoading: isAccountsLoading,
    isError: isAccountsError,
    error: accountsError,
    refetch: refetchAccounts,
  } = useQuery<ConnectedInstagramAccount[]>({
    queryKey: ['instagram-accounts'],
    queryFn: () => instagramApi.listAccounts(),
    staleTime: 60_000,
    retry: 2,
    enabled: statusData?.status !== 'not_connected',
  });

  // Single source of truth state machine from backend connection-status
  let connectionState: InstagramConnectionState = 'checking';
  if (isStatusLoading) {
    connectionState = 'checking';
  } else if (isStatusError) {
    connectionState = 'temporarily_unavailable';
  } else if (statusData?.status === 'connected') {
    connectionState = 'connected';
  } else if (statusData?.status === 'token_expiring') {
    connectionState = 'token_expiring';
  } else if (statusData?.status === 'reauthorization_required') {
    connectionState = 'reauthorization_required';
  } else if (statusData?.status === 'temporarily_unavailable') {
    connectionState = 'temporarily_unavailable';
  } else if (statusData?.status === 'not_connected') {
    connectionState = 'not_connected';
  } else {
    connectionState = 'not_connected';
  }

  const primaryAccount: ConnectedInstagramAccount | null =
    (accounts && accounts.length > 0 ? accounts[0] : null) ||
    statusData?.account ||
    null;

  const isConnected = connectionState === 'connected' || connectionState === 'token_expiring';
  const isChecking = connectionState === 'checking';
  const needsReauth = connectionState === 'reauthorization_required';
  const isUnavailable = connectionState === 'temporarily_unavailable';
  const isNotConnected = connectionState === 'not_connected';

  const refetch = async () => {
    await refetchStatus();
    await refetchAccounts();
  };

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
    statusData,
    accounts: accounts.length > 0 ? accounts : (statusData?.account ? [statusData.account] : []),
    primaryAccount,
    isConnected,
    isChecking,
    needsReauth,
    isUnavailable,
    isNotConnected,
    isLoading: isStatusLoading || (isConnected && isAccountsLoading),
    isError: isStatusError,
    error: statusError || accountsError,
    refetch,
    startConnect,
  };
}

export default useInstagramConnection;
