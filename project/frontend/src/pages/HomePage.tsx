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