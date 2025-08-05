/**
 * Global event system for real-time data updates
 * Allows components to subscribe to data changes and update automatically
 */

type EventCallback = () => void;

class DataUpdateEvents {
  private listeners: Map<string, EventCallback[]> = new Map();

  // Event types
  static readonly COMMITMENT_UPDATED = 'commitment:updated';
  static readonly PROFILE_UPDATED = 'profile:updated';
  static readonly CHECKIN_UPDATED = 'checkin:updated';
  static readonly PROACTIVE_MESSAGE_UPDATED = 'proactive:updated';

  /**
   * Subscribe to an event
   */
  on(event: string, callback: EventCallback): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    
    const callbacks = this.listeners.get(event)!;
    callbacks.push(callback);

    // Return unsubscribe function
    return () => {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Emit an event to all listeners
   */
  emit(event: string): void {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  /**
   * Emit multiple events at once
   */
  emitMultiple(events: string[]): void {
    events.forEach(event => this.emit(event));
  }
}

// Create singleton instance
export const dataUpdateEvents = new DataUpdateEvents();

// Export event names for convenience
export const DATA_EVENTS = {
  COMMITMENT_UPDATED: DataUpdateEvents.COMMITMENT_UPDATED,
  PROFILE_UPDATED: DataUpdateEvents.PROFILE_UPDATED,
  CHECKIN_UPDATED: DataUpdateEvents.CHECKIN_UPDATED,
  PROACTIVE_MESSAGE_UPDATED: DataUpdateEvents.PROACTIVE_MESSAGE_UPDATED,
} as const;