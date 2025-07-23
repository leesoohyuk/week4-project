// src/components/SongCard.tsx

import React from 'react';
import { Song } from '../types/song';

interface SongCardProps {
  song: Song;
  onClick: (song: Song) => void;
}

const SongCard: React.FC<SongCardProps> = ({ song, onClick }) => {
  return (
    <div 
      onClick={() => onClick(song)}
      className="flex bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:bg-gray-200 transition-colors duration-200 mb-4"
    >
      {/* 썸네일 영역 */}
      <div className="w-48 h-32 bg-gray-200 flex items-center justify-center">
        <img 
          src={song.thumbnailUrl} 
          alt={song.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src =
              'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyIiBoZWlnaHQ9IjEwOCIgdmlld0JveD0iMCAwIDE5MiAxMDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxOTIiIGhlaWdodD0iMTA4IiBmaWxsPSIjZjNmNGY2Ii8+Cjx0ZXh0IHg9Ijk2IiB5PSI1NCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjc3NDhkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPuuMgOuPnOy5hCDsl4bsnYw8L3RleHQ+Cjwvc3ZnPgo=';
          }}
        />
      </div>

      {/* 정보 영역 */}
      <div className="flex-1 p-4">
        <h3 className="text-black font-semibold text-lg mb-1">{song.title}</h3>
        <p className="text-gray-600 text-sm mb-3">{song.channelTitle}</p>
        <div className="flex items-center text-gray-700 text-sm space-x-4">
          <span>BPM: {song.bpm || Math.floor(Math.random() * 60) + 80}</span>
          <span>/</span>
          <span>Signature: {song.signature || '4/4'}</span>
          <span>/</span>
          <span>Key: {song.key || 'C Major'}</span>
        </div>
      </div>
    </div>
  );
};

export default SongCard;
