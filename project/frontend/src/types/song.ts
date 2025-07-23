export interface Song {
  videoId: string;
  title: string;
  channelTitle: string;
  thumbnailUrl: string;
  bpm?: number;
  signature?: string;
  key?: string;
}

export interface ChordData {
  chord: string;
  timestamp: number;
  duration: number;
}

export interface ChordChart {
  chord: string;
  frets: number[];
  fingers: number[];
}

export interface SongDetail extends Song {
  chords: ChordData[];
  chordCharts: ChordChart[];
}