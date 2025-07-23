// src/components/ChordChart.tsx

import React from 'react';
import { ChordChart as ChordChartType } from '../types/song';

interface ChordChartProps {
  chord: ChordChartType;
}

const ChordChart: React.FC<ChordChartProps> = ({ chord }) => {
  const strings = ['E', 'A', 'D', 'G', 'B', 'E'];

  // 0: open, -1: mute, >0: fret
  const playedFrets = chord.frets.filter(f => f > 0);
  const maxFret = Math.max(...playedFrets) || 3;
  const minFret = Math.min(...playedFrets) || 1;
  const fretRange = Math.max(3, maxFret - minFret + 1);

  return (
    <div className="flex flex-col items-center p-4 bg-white border border-gray-300 rounded-xl shadow-sm">
      {/* 코드 이름 */}
      <h3 className="text-black font-bold text-lg mb-2">{chord.chord}</h3>

      {/* 스트링 위 o, x 마크 */}
      <div className="flex justify-between w-24 mb-2">
        {chord.frets.map((fret, index) => (
          <span key={index} className="text-black text-sm font-mono">
            {fret === 0 ? 'o' : fret === -1 ? 'x' : ''}
          </span>
        ))}
      </div>

      {/* 프렛보드 */}
      <div className="relative">
        <svg width="96" height="120" viewBox="0 0 96 120">
          {/* 프렛 라인 */}
          {Array.from({ length: fretRange + 1 }).map((_, fretIndex) => (
            <line
              key={fretIndex}
              x1="8"
              y1={8 + fretIndex * 20}
              x2="88"
              y2={8 + fretIndex * 20}
              stroke="#bbb"
              strokeWidth={fretIndex === 0 ? "3" : "1"}
            />
          ))}

          {/* 줄 */}
          {Array.from({ length: 6 }).map((_, stringIndex) => (
            <line
              key={stringIndex}
              x1={8 + stringIndex * 16}
              y1="8"
              x2={8 + stringIndex * 16}
              y2={8 + fretRange * 20}
              stroke="#bbb"
              strokeWidth="1"
            />
          ))}

          {/* 손가락 위치 */}
          {chord.frets.map((fret, stringIndex) => {
            if (fret > 0 && fret <= maxFret) {
              const fretPos = fret - minFret + 1;
              return (
                <circle
                  key={stringIndex}
                  cx={8 + stringIndex * 16}
                  cy={8 + (fretPos - 0.5) * 20}
                  r="6"
                  fill="#222"
                  stroke="#fff"
                  strokeWidth="1.5"
                />
              );
            }
            return null;
          })}

          {/* 프렛 번호 (minFret > 1일 때만) */}
          {minFret > 1 && (
            <text
              x="2"
              y={8 + 10}
              fill="#666"
              fontSize="10"
              textAnchor="middle"
            >
              {minFret}
            </text>
          )}
        </svg>
      </div>
    </div>
  );
};

export default ChordChart;
