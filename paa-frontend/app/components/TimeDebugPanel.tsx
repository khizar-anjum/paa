'use client';

import { useState, useEffect } from 'react';
import { debugApi, TimeStatus, SchedulerStatus } from '@/lib/api/debug';
import { toast } from 'sonner';

export default function TimeDebugPanel() {
  const [timeStatus, setTimeStatus] = useState<TimeStatus | null>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [multiplier, setMultiplier] = useState(600);

  const refreshStatus = async () => {
    try {
      const response = await debugApi.getTimeStatus();
      if (response.success) {
        setTimeStatus(response.time_service);
        setSchedulerStatus(response.fake_scheduler);
        // Sync local multiplier with backend
        if (response.time_service.time_multiplier) {
          setMultiplier(response.time_service.time_multiplier);
        }
      }
    } catch (error) {
      console.error('Failed to fetch time status:', error);
    }
  };

  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const handleStartFakeTime = async () => {
    setLoading(true);
    try {
      const response = await debugApi.startFakeTime(multiplier);
      if (response.success) {
        toast.success(response.message);
        await refreshStatus();
      } else {
        toast.error('Failed to start fake time');
      }
    } catch (error) {
      toast.error('Error starting fake time');
    }
    setLoading(false);
  };

  const handleStopFakeTime = async () => {
    setLoading(true);
    try {
      const response = await debugApi.stopFakeTime();
      if (response.success) {
        toast.success(response.message);
        await refreshStatus();
      } else {
        toast.error('Failed to stop fake time');
      }
    } catch (error) {
      toast.error('Error stopping fake time');
    }
    setLoading(false);
  };

  const handleSetMultiplier = async () => {
    setLoading(true);
    try {
      console.log(`Setting multiplier to ${multiplier}`);
      const response = await debugApi.setTimeMultiplier(multiplier);
      console.log('Set multiplier response:', response);
      if (response.success) {
        toast.success(response.message);
        await refreshStatus();
      } else {
        console.error('Failed to set multiplier:', response);
        toast.error(`Failed to set multiplier: ${response.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error setting multiplier:', error);
      toast.error(`Error setting multiplier: ${error}`);
    }
    setLoading(false);
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="fixed top-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
      <div className="p-3">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600"
        >
          🕐 Time Debug
          <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>

        {timeStatus && (
          <div className="mt-2">
            <div className={`flex items-center gap-2 text-xs ${timeStatus.using_fake_time ? 'text-orange-600' : 'text-green-600'}`}>
              <div className={`w-2 h-2 rounded-full ${timeStatus.using_fake_time ? 'bg-orange-500' : 'bg-green-500'}`}></div>
              {timeStatus.using_fake_time ? 'FAKE TIME ACTIVE' : 'Real Time'}
            </div>
            
            {timeStatus.using_fake_time && (
              <div className="text-xs text-gray-600 mt-1">
                {timeStatus.fake_minutes_per_real_second}x speed
              </div>
            )}
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200 p-3 w-80">
          <div className="space-y-3">
            {/* Current Time Display */}
            {timeStatus && (
              <div className="text-xs space-y-1">
                <div><strong>Current Time:</strong> {formatTime(timeStatus.current_time)}</div>
                <div><strong>Real Time:</strong> {formatTime(timeStatus.real_time)}</div>
                {timeStatus.using_fake_time && (
                  <>
                    <div><strong>Multiplier:</strong> {timeStatus.time_multiplier}x</div>
                    <div><strong>Fake Minutes/Second:</strong> {timeStatus.fake_minutes_per_real_second}</div>
                    {timeStatus.fake_elapsed_time && (
                      <div><strong>Fake Time Elapsed:</strong> {timeStatus.fake_elapsed_time.toFixed(1)} minutes</div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Controls */}
            <div className="space-y-2">
              <div className="flex gap-2 items-center">
                <input
                  type="number"
                  value={multiplier}
                  onChange={(e) => setMultiplier(Number(e.target.value))}
                  className="px-2 py-1 text-xs border rounded w-20"
                  min="1"
                  max="216000"
                />
                <span className="text-xs text-gray-600">fake sec/real sec</span>
              </div>
              <div className="text-xs text-gray-500">
                = {(multiplier / 60).toFixed(1)} fake min/real sec
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={handleStartFakeTime}
                  disabled={loading || timeStatus?.using_fake_time}
                  className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Start Fake
                </button>
                
                <button
                  onClick={handleStopFakeTime}
                  disabled={loading || !timeStatus?.using_fake_time}
                  className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Stop Fake
                </button>
              </div>

              {timeStatus?.using_fake_time && (
                <button
                  onClick={handleSetMultiplier}
                  disabled={loading}
                  className="w-full px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
                >
                  Update Multiplier
                </button>
              )}
            </div>

            {/* Scheduler Status */}
            {schedulerStatus && (
              <div className="text-xs border-t pt-2">
                <div className="font-medium mb-1">Fake Scheduler:</div>
                <div className={`flex items-center gap-1 ${schedulerStatus.running ? 'text-green-600' : 'text-red-600'}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${schedulerStatus.running ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  {schedulerStatus.running ? 'Running' : 'Stopped'}
                </div>
                <div className="mt-1 text-gray-600">
                  Jobs: {schedulerStatus.jobs.length}
                </div>
              </div>
            )}

            {/* Quick Presets */}
            <div className="text-xs border-t pt-2">
              <div className="font-medium mb-1">Quick Presets (fake min/real sec):</div>
              <div className="grid grid-cols-4 gap-1">
                <button
                  onClick={() => setMultiplier(60)}
                  className="px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
                >
                  1m/s
                </button>
                <button
                  onClick={() => setMultiplier(600)}
                  className="px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
                >
                  10m/s
                </button>
                <button
                  onClick={() => setMultiplier(3600)}
                  className="px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
                >
                  60m/s
                </button>
                <button
                  onClick={() => setMultiplier(6000)}
                  className="px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
                >
                  100m/s
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}