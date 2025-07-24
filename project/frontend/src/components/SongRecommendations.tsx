import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Song } from '../types/song';
import { searchSongs } from '../utils/api';

interface SongRecommendationsProps {
  currentSong: {
    title: string;
    channelTitle: string;
    videoId: string;
  };
  className?: string;
}

const SongRecommendations: React.FC<SongRecommendationsProps> = ({ 
  currentSong, 
  className = "" 
}) => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        setLoading(true);
        
        // 현재 곡의 아티스트나 제목을 기반으로 관련 곡 검색
        const searchQueries = [
          currentSong.channelTitle, // 같은 아티스트의 다른 곡
          `${currentSong.channelTitle} popular songs`, // 아티스트의 인기곡
          extractKeywords(currentSong.title), // 제목에서 키워드 추출
        ];

        const allRecommendations: Song[] = [];
        
        for (const query of searchQueries) {
          if (query && allRecommendations.length < 6) {
            try {
              const { items } = await searchSongs(query, '');
              // 현재 곡 제외하고 추가
              const filtered = items.filter(item => item.videoId !== currentSong.videoId);
              allRecommendations.push(...filtered);
            } catch (error) {
              console.error(`Error searching for "${query}":`, error);
            }
          }
        }

        // 중복 제거 및 최대 6개로 제한
        const uniqueRecommendations = allRecommendations
          .filter((song, index, self) => 
            index === self.findIndex(s => s.videoId === song.videoId)
          )
          .slice(0, 6);

        setRecommendations(uniqueRecommendations);
      } catch (error) {
        console.error('Error loading recommendations:', error);
      } finally {
        setLoading(false);
      }
    };

    if (currentSong) {
      loadRecommendations();
    }
  }, [currentSong]);

  const extractKeywords = (title: string): string => {
    // 제목에서 특수문자 제거하고 주요 키워드만 추출
    return title
      .replace(/[\[\](){}|"']/g, '') // 특수문자 제거
      .split(' ')
      .slice(0, 3) // 처음 3단어만
      .join(' ');
  };

  const handleSongClick = (song: Song) => {
    navigate(`/song/${song.videoId}`);
  };

  if (loading) {
    return (
      <div className={`bg-gray-100 rounded-lg p-6 ${className}`}>
        <h3 className="text-black text-lg font-semibold mb-4">추천 곡</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((index) => (
            <div key={index} className="bg-white rounded-lg overflow-hidden">
              <div className="w-full aspect-video bg-gray-200 animate-pulse"></div>
              <div className="p-3">
                <div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
                <div className="h-3 bg-gray-200 rounded animate-pulse w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className={`bg-gray-100 rounded-lg p-6 ${className}`}>
        <h3 className="text-black text-lg font-semibold mb-4">추천 곡</h3>
        <div className="text-center text-gray-500 py-8">
          추천 곡을 불러올 수 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-100 rounded-lg p-6 ${className}`}>
      <h3 className="text-black text-lg font-semibold mb-4">추천 곡</h3>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.map((song) => (
          <div
            key={song.videoId}
            onClick={() => handleSongClick(song)}
            className="bg-white rounded-lg overflow-hidden cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
          >
            {/* 썸네일 */}
            <div className="w-full aspect-video bg-gray-200 relative overflow-hidden">
              <img
                src={song.thumbnailUrl}
                alt={song.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMyMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMjAiIGhlaWdodD0iMTgwIiBmaWxsPSIjZjNmNGY2Ii8+Cjx0ZXh0IHg9IjE2MCIgeT0iOTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzY3NzQ4ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9IjAuM2VtIj4o7I2s64Sk7J28KTwvdGV4dD4KPHN2Zz4K';
                }}
              />
            </div>
            
            {/* 곡 정보 */}
            <div className="p-3">
              <h4 className="text-black font-semibold text-sm mb-1 line-clamp-2 leading-tight">
                {song.title}
              </h4>
              <p className="text-gray-600 text-xs truncate">
                {song.channelTitle}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SongRecommendations;