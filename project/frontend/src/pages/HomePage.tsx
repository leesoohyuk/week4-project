import React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronUp } from 'lucide-react';
import SearchBar from '../components/SearchBar';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [showChart, setShowChart] = useState(false);

  // 임시 인기차트 데이터
  const popularSongs = [
    { rank: 1, title: '곡 제목', artist: '아티스트명', thumbnail: '' },
    { rank: 2, title: '곡 제목', artist: '아티스트명', thumbnail: '' },
    { rank: 3, title: '곡 제목', artist: '아티스트명', thumbnail: '' },
    { rank: 4, title: '곡 제목', artist: '아티스트명', thumbnail: '' },
  ];

  const handleSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  const handleSongClick = (song: any) => {
    // 실제 구현에서는 videoId를 사용
    navigate(`/song/sample-video-id`);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4">
      <div className="text-center mb-12 w-full max-w-2xl">
        <h1 className="text-6xl font-bold text-black mb-[80px]">AutoChord</h1> 
        <div className="w-full h-px bg-gray-300 mx-auto mb-[50px]"></div> 
        
        <div className="w-full">
          <SearchBar 
            onSearch={handleSearch}
            placeholder="어떤 노래를 연주할까요?"
            className="w-full"
          />
        </div>
        
        {/* 인기차트 토글 버튼 */}
        <div className="mt-8 w-full">
          <button
            onClick={() => setShowChart(!showChart)}
            className="flex items-center justify-center gap-2 mx-auto px-6 py-3 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors duration-200"
          >
            <span className="font-medium">인기차트</span>
            {showChart ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>

        {/* 인기차트 섹션 */}
        <div className={`w-full max-w-6xl mx-auto mt-6 transition-all duration-300 ease-in-out overflow-hidden ${
          showChart ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}>
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {popularSongs.map((song) => (
                <div
                  key={song.rank}
                  onClick={() => handleSongClick(song)}
                  className="bg-white rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow duration-200"
                >
                  {/* 썸네일 */}
                  <div className="w-full aspect-video bg-black rounded-lg flex items-center justify-center mb-3">
                    <span className="text-white text-sm">(썸네일)</span>
                  </div>
                  
                  {/* 순위와 정보 */}
                  <div className="text-left">
                    <div className="text-lg font-bold text-black mb-1">
                      #{song.rank}
                    </div>
                    <div className="text-sm text-gray-600">
                      ({song.title})
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

/*
import React from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const handleSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4">
      <div className="text-center mb-12">
        <h1 className="text-6xl font-bold text-black mb-4">AutoChord</h1>
      </div>
      
      <div className="w-full max-w-2xl mb-8">
        <SearchBar 
          onSearch={handleSearch}
          placeholder="어떤 노래를 연주할까요?"
          className="w-full"
        />
      </div>
      
      <div className="w-full max-w-2xl h-px bg-gray-300"></div>
    </div>
  );
};

export default HomePage;

*/