// src/components/SearchBar.tsx

import React, { useState } from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  className?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch, 
  placeholder = "paste youtube link or search song",
  className = ""
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleSearchClick = () => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full px-6 py-4 text-gray-600 bg-white rounded-full border-2 border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 pr-16 shadow-sm"
      />
      <button
        type="button"
        onClick={handleSearchClick}
        className="absolute right-2 top-1/2 transform -translate-y-1/2 p-3 bg-gray-800 text-white rounded-full hover:bg-gray-700 transition-colors duration-200"
      >
        <Search size={20} />
      </button>
    </form>
  );
};

export default SearchBar;
