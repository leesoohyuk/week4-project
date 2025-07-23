import React, { useEffect, useRef } from 'react';

interface YouTubePlayerProps {
  videoId: string;
  className?: string;
}

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

const YouTubePlayer: React.FC<YouTubePlayerProps> = ({ videoId, className = "" }) => {
  const playerRef = useRef<HTMLDivElement>(null);
  const playerInstanceRef = useRef<any>(null);

  useEffect(() => {
    // Load YouTube iframe API script only if not already loaded
    if (!window.YT) {
      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(script);
    }

    // Initialize the player instance
    const initializePlayer = () => {
      if (playerRef.current && window.YT && window.YT.Player) {
        if (playerInstanceRef.current) {
          playerInstanceRef.current.destroy();
        }
        playerInstanceRef.current = new window.YT.Player(playerRef.current, {
          width: '100%',
          height: '100%',
          videoId: videoId,
          playerVars: {
            playsinline: 1,
            rel: 0,
            modestbranding: 1
          }
        });
      }
    };

    if (window.YT && window.YT.Player) {
      initializePlayer();
    } else {
      window.onYouTubeIframeAPIReady = initializePlayer;
    }

    // Cleanup on unmount
    return () => {
      if (playerInstanceRef.current) {
        playerInstanceRef.current.destroy();
      }
    };
  }, [videoId]);

  return (
    <div className={`relative ${className}`}>
      <div 
        ref={playerRef}
        className="w-full h-full bg-gray-200 flex items-center justify-center text-gray-600"
      >
        유튜브 영상 플레이어
      </div>
    </div>
  );
};

export default YouTubePlayer;
