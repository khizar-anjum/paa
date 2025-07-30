import { useEffect, useCallback } from 'react';
import { dataUpdateEvents } from '@/lib/events/dataUpdateEvents';

/**
 * Custom hook to automatically refresh data when update events are emitted
 * 
 * @param events - Array of event names to listen for
 * @param refreshCallback - Function to call when any of the events are emitted
 * @param dependencies - Additional dependencies for the refresh callback
 */
export function useDataRefresh(
  events: string[],
  refreshCallback: () => void | Promise<void>,
  dependencies: any[] = []
) {
  // Don't memoize the callback if no dependencies are provided
  // This allows the callback to always use the latest closure
  const memoizedRefresh = dependencies.length > 0 
    ? useCallback(refreshCallback, dependencies)
    : refreshCallback;

  useEffect(() => {
    // Subscribe to all specified events
    const unsubscribes = events.map(event => 
      dataUpdateEvents.on(event, memoizedRefresh)
    );

    // Cleanup subscriptions on unmount
    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
    };
  }, [events, memoizedRefresh]);
}

/**
 * Hook for periodic polling with event-based refresh
 * Combines regular polling with instant updates from events
 */
export function usePollingWithEvents(
  events: string[],
  refreshCallback: () => void | Promise<void>,
  pollingInterval: number = 30000, // Default 30 seconds
  dependencies: any[] = []
) {
  const memoizedRefresh = useCallback(refreshCallback, dependencies);

  // Use event-based refresh
  useDataRefresh(events, memoizedRefresh, dependencies);

  // Also add polling
  useEffect(() => {
    if (pollingInterval <= 0) return;

    const interval = setInterval(() => {
      memoizedRefresh();
    }, pollingInterval);

    return () => clearInterval(interval);
  }, [pollingInterval, memoizedRefresh]);
}