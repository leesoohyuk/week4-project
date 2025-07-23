// src/components/ChordProgression.tsx

import React from 'react';
import { ChordData } from '../types/song';

interface ChordProgressionProps {
  chords?: ChordData[];  // chords가 없을 수도 있으니 optional 처리
  currentTime?: number;
}

const ChordProgression: React.FC<ChordProgressionProps> = ({ chords = [], currentTime = 0 }) => {
  // chords가 빈 배열일 때 안내 메시지 출력
  if (chords.length === 0) {
    return (
      <div className="bg-gray-100 rounded-lg p-4 text-center text-gray-500">
        Chord progression 데이터가 없습니다.
      </div>
    );
  }

  return (
    <div className="bg-gray-100 rounded-lg p-4">
      <h3 className="text-black text-lg font-semibold mb-4">Chord Progression</h3>
      
      {/* Timeline */}
      <div className="relative bg-gray-200 rounded-lg p-4 overflow-x-auto">
        <div className="flex items-center space-x-2 min-w-full">
          {chords.map((chordData, index) => {
            const isActive =
              currentTime >= chordData.timestamp &&
              currentTime < chordData.timestamp + chordData.duration;

            return (
              <div
                key={index}
                className={`flex-shrink-0 px-4 py-2 rounded-md text-center font-semibold transition-colors duration-200 ${
                  isActive
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                }`}
                style={{ minWidth: '80px' }}
              >
                {chordData.chord}
              </div>
            );
          })}
        </div>
        
        {/* Progress indicator */}
        <div className="mt-3 h-1 bg-gray-300 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-100 ease-out rounded-full"
            style={{
              width: `${Math.min(
                100,
                (currentTime /
                  ((chords[chords.length - 1]?.timestamp ?? 0) +
                    (chords[chords.length - 1]?.duration ?? 1))) *
                  100
              )}%`
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default ChordProgression;
