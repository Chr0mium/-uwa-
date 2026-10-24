import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const fetchWindData = async (date) => {
  const response = await axios.get(`${API_URL}/api/wind-data`, { params: { date } });
  return response.data;
};