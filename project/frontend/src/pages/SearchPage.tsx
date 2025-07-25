import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ChevronUp, ChevronDown } from 'lucide-react';
import SearchBar from '../components/SearchBar';
import SongCard from '../components/SongCard';
import LoginButton from '../components/LoginButton';
import { searchSongs } from '../utils/api';
import { Song } from '../types/song';

const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(false);
  const [nextPageToken, setNextPageToken] = useState<string>('');
  const [hasMore, setHasMore] = useState(false);

  const query = searchParams.get('q') || '';

  const loadSongs = useCallback(
    async (searchQuery: string, pageToken: string = '', append: boolean = false) => {
      if (!searchQuery) return;

      setLoading(true);
      try {
        const { items, nextPageToken: token } = await searchSongs(searchQuery, pageToken);
        setSongs(prev => (append ? [...prev, ...items] : items));
        setNextPageToken(token || '');
        setHasMore(!!token);
      } catch (error) {
        console.error('Error loading songs:', error);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (query) {
      loadSongs(query);
    } else {
      setSongs([]);
      setNextPageToken('');
      setHasMore(false);
    }
  }, [query, loadSongs]);

  const handleSearch = (newQuery: string) => {
    setSearchParams({ q: newQuery });
  };

  const handleSongClick = (song: Song) => {
    navigate(`/song/${song.videoId}`);
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      loadSongs(query, nextPageToken, true);
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const scrollToBottom = () => {
    window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
  };

  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + document.documentElement.scrollTop >=
        document.documentElement.offsetHeight - 10
      ) {
        loadMore();
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loading, hasMore, nextPageToken, query, loadSongs]);

  return (
    <div className="min-h-screen bg-white">
      {/* 로그인 버튼 - 우상단 고정 */}
      <div className="fixed top-4 right-4 z-40">
        <LoginButton />
      </div>
      
      {/* Fixed search bar */}
      <div className="sticky top-0 bg-white z-50 border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="text-2xl font-bold text-black hover:text-gray-700 transition-colors duration-200 flex-shrink-0"
            >
              AutoChord
            </button>
            <div className="flex-1">
              <SearchBar onSearch={handleSearch} placeholder="어떤 노래를 연주할까요?" />
            </div>
          </div>
        </div>
      </div>

      {/* Search results */}
      <div className="max-w-4xl mx-auto p-4">
        {loading && songs.length === 0 ? (
          <div className="text-center text-gray-600 py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
            검색 중...
          </div>
        ) : songs.length === 0 && query ? (
          <div className="text-center text-gray-600 py-12">
            검색 결과가 없습니다.
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {songs.map((song, index) => (
                <SongCard
                  key={`${song.videoId}-${index}`}
                  song={song}
                  onClick={() => handleSongClick(song)}
                />
              ))}
            </div>

            {loading && songs.length > 0 && (
              <div className="text-center text-gray-600 py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto mb-2"></div>
                더 많은 결과를 불러오는 중...
              </div>
            )}

            {!hasMore && songs.length > 0 && (
              <div className="text-center text-gray-400 py-8">
                모든 검색 결과를 확인했습니다.
              </div>
            )}
          </>
        )}
      </div>

      {/* Scroll buttons */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-2 z-40">
        <button
          onClick={scrollToTop}
          className="p-3 bg-black text-white rounded-full shadow-lg hover:bg-gray-800 transition-colors duration-200"
          title="맨 위로"
        >
          <ChevronUp size={20} />
        </button>
        <button
          onClick={scrollToBottom}
          className="p-3 bg-black text-white rounded-full shadow-lg hover:bg-gray-800 transition-colors duration-200"
          title="맨 아래로"
        >
          <ChevronDown size={20} />
        </button>
      </div>
    </div>
  );
};

export default SearchPage;
