import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchWeather() {
      try {
        // Replace with your backend endpoint and coordinates
        const res = await axios.get('/api/weather?lat=2.93&lon=-75.28');
        setWeather(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchWeather();
  }, []);

  if (loading) return <div>Loading...</div>;
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Weather in Neiva</h1>
      <pre>{JSON.stringify(weather, null, 2)}</pre>
    </div>
  );
}
