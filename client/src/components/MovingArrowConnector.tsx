import React from 'react';
import { ArrowRight } from 'lucide-react';

interface MovingArrowConnectorProps {
  className?: string;
  arrowSize?: number;
  trackWidth?: number;
}

/**
 * Animated moving arrow connector between Instagram and Comlina logos.
 * Features:
 * - Marching dashed track (Instagram -> Comlina data flow)
 * - Traveling glowing sync pulse
 * - Moving / gliding arrowhead with smooth translation & color transition
 */
export function MovingArrowConnector({
  className = '',
  arrowSize = 15,
  trackWidth = 34,
}: MovingArrowConnectorProps) {
  return (
    <div 
      className={`flex items-center gap-1 select-none text-[#9E9E96] ${className}`}
      aria-hidden="true"
    >
      {/* Animated Flowing Dashed Track */}
      <div 
        className="relative flex items-center h-4 overflow-hidden"
        style={{ width: `${trackWidth}px` }}
      >
        <svg
          width={trackWidth}
          height={16}
          viewBox={`0 0 ${trackWidth} 16`}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full overflow-visible"
        >
          {/* Animated Marching Dashed Line */}
          <line
            x1="2"
            y1="8"
            x2={trackWidth - 2}
            y2="8"
            stroke="#D1D5DB"
            strokeWidth="2"
            strokeDasharray="4 3"
            strokeLinecap="round"
            className="animate-dash-flow"
          />

          {/* Glowing Green Data Packet / Sync Pulse */}
          <circle
            cx="2"
            cy="8"
            r="2"
            className="fill-[#15803D] animate-pulse-travel"
          />
        </svg>
      </div>

      {/* Moving Arrow Head */}
      <div className="animate-arrow-glide flex items-center shrink-0">
        <ArrowRight size={arrowSize} strokeWidth={2.2} />
      </div>
    </div>
  );
}

export default MovingArrowConnector;
