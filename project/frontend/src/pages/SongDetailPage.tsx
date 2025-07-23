// src/pages/SongDetailPage.tsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import YouTubePlayer from '../components/YouTubePlayer';
import ChordChart from '../components/ChordChart';
import ChordProgression from '../components/ChordProgression';
import { getSongDetail } from '../utils/api';
import { SongDetail } from '../types/song';

const SongDetailPage: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>();
  const navigate = useNavigate();
  const [songDetail, setSongDetail] = useState<SongDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!videoId) {
      setError('잘못된 요청입니다.');
      setLoading(false);
      return;
    }

    const loadSongDetail = async (id: string) => {
      setLoading(true);
      try {
        const detail = await getSongDetail(id);
        setSongDetail(detail);
      } catch (err) {
        console.error('Error loading song detail:', err);
        setError('곡 정보를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadSongDetail(videoId);
  }, [videoId]);

  const handleSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center text-gray-600">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          곡 정보를 불러오는 중...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center text-red-500">
          <p>{error}</p>
          <button
            className="mt-4 px-4 py-2 bg-gray-200 text-black rounded"
            onClick={() => navigate(-1)}
          >
            뒤로 가기
          </button>
        </div>
      </div>
    );
  }

  if (!songDetail || !videoId) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center text-gray-600">
          곡 정보를 찾을 수 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Fixed search bar */}
      <div className="sticky top-0 bg-white z-50 border-b border-gray-200 p-4">
        <div className="max-w-7xl mx-auto">
          <SearchBar
            onSearch={handleSearch}
            placeholder="paste youtube link or search song"
          />
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video player */}
          <div className="lg:col-span-2">
            <div className="bg-gray-100 rounded-lg overflow-hidden">
              <YouTubePlayer
                videoId={videoId}
                className="w-full aspect-video"
                onTimeUpdate={setCurrentTime} // YouTubePlayer가 이 prop을 지원한다고 가정
              />
            </div>

            {/* Chord progression */}
            <div className="mt-6">
              <ChordProgression
                chords={songDetail.chords}
                currentTime={currentTime}
              />
            </div>
          </div>

          {/* Song info sidebar */}
          <div className="space-y-6">
            <div className="bg-gray-100 rounded-lg p-6">
              <h2 className="text-black text-xl font-bold mb-4">곡 정보</h2>
              <div className="space-y-3 text-gray-700">
                <div>
                  <span className="text-gray-500">제목:</span>
                  <p className="font-semibold">{songDetail.title}</p>
                </div>
                <div>
                  <span className="text-gray-500">아티스트:</span>
                  <p className="font-semibold">{songDetail.channelTitle}</p>
                </div>
                <div>
                  <span className="text-gray-500">Song BPM:</span>
                  <p className="font-semibold">{songDetail.bpm}</p>
                </div>
                <div>
                  <span className="text-gray-500">Song Signature:</span>
                  <p className="font-semibold">{songDetail.signature}</p>
                </div>
                <div>
                  <span className="text-gray-500">조성:</span>
                  <p className="font-semibold">({songDetail.key})</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Chord charts */}
        <div className="mt-8">
          <h2 className="text-black text-2xl font-bold mb-6">코드 차트</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {Array.isArray(songDetail.chordCharts) && songDetail.chordCharts.length > 0 ? (
              songDetail.chordCharts.map((chord, index) => (
                <ChordChart key={index} chord={chord} />
              ))
            ) : (
              <p className="text-gray-500">코드 차트 정보가 없습니다.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SongDetailPage;
