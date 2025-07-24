import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Song } from '../types/song';
import { searchSongs } from '../utils/api';

interface MusicChartProps {
  className?: string;
}

const MusicChart: React.FC<MusicChartProps> = ({ className = "" }) => {
  const navigate = useNavigate();
  const [chartSongs, setChartSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadChartSongs = async () => {
      try {
        setLoading(true);
        // 인기 음악 키워드들로 검색하여 차트 구성
        const popularQueries = [
          'official mv',
          'new kpop mv 2025',
          'latest pop mv',
          'hot mv 2025',
          '신곡 뮤직비디오',
          'kpop mv',
          'brand new mv',
          '오늘의 뮤직비디오',
          '신규 공개 mv',
          '뮤직비디오 추천'
        ];


        
        const randomQuery = popularQueries[Math.floor(Math.random() * popularQueries.length)];
        const { items } = await searchSongs(randomQuery, '');
        setChartSongs(items.slice(0, 4)); // 상위 4개만 표시
      } catch (error) {
        console.error('Error loading chart songs:', error);
        // 에러 시 빈 배열 유지
      } finally {
        setLoading(false);
      }
    };

    loadChartSongs();
  }, []);

  const handleSongClick = (song: Song) => {
    navigate(`/song/${song.videoId}`);
  };

  if (loading) {
    return (
      <div className={`bg-gray-100 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-black text-xl font-bold">인기 차트</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((index) => (
            <div key={index} className="bg-white rounded-lg overflow-hidden">
              <div className="w-full aspect-video bg-gray-200 animate-pulse flex items-center justify-center">
                <span className="text-gray-400">(썸네일)</span>
              </div>
              <div className="p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg font-bold text-black">#{index}</span>
                </div>
                <div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
                <div className="h-3 bg-gray-200 rounded animate-pulse w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-100 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-black text-xl font-bold">인기 차트</h2>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {chartSongs.map((song, index) => (
          <div
            key={song.videoId}
            onClick={() => handleSongClick(song)}
            className="bg-white rounded-lg overflow-hidden cursor-pointer hover:shadow-md transition-shadow duration-200"
          >
            {/* 썸네일 */}
            <div className="w-full aspect-video bg-gray-200 relative">
              <img
                src={song.thumbnailUrl}
                alt={song.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDMyMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMjAiIGhlaWdodD0iMTgwIiBmaWxsPSIjZjNmNGY2Ii8+Cjx0ZXh0IHg9IjE2MCIgeT0iOTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzY3NzQ4ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9IjAuM2VtIj4o7I2s64Sk7J28KTwvdGV4dD4KPHN2Zz4K';
                }}
              />
            </div>
            
            {/* 정보 */}
            <div className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg font-bold text-black">#{index + 1}</span>
              </div>
              <h3 className="text-black font-semibold text-sm mb-1 line-clamp-2 leading-tight">
                {song.title}
              </h3>
              <p className="text-gray-600 text-xs truncate">
                ({song.channelTitle})
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MusicChart;