import React from 'react';
import UrlScanner from './components/UrlScanner';

const App = () => (
  <div className="min-h-screen bg-gray-900 text-white p-5">
    <h1 className="text-4xl font-bold text-center mb-8">🛡️ Phishing Detection Dashboard</h1>
    <UrlScanner />
  </div>
);

export default App;
