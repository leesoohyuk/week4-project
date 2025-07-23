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
        className="w-full px-6 py-4 text-gray-800 bg-white rounded-full border-2 border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 pr-14"
      />
      <button
        type="button"
        onClick={handleSearchClick}
        className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
      >
        <Search size={24} />
      </button>
    </form>
  );
};

export default SearchBar;
