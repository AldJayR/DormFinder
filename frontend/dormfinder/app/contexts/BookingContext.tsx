import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';

type Booking = {
  id: string;
  dormId: string;
  startDate: string;
  endDate: string;
  status: 'pending' | 'confirmed' | 'cancelled';
};

type BookingContextType = {
  bookings: Booking[];
  currentBooking: Booking | null;
  loading: boolean;
  error: string | null;
  createBooking: (dormId: string, dates: { start: Date; end: Date }) => Promise<void>;
  cancelBooking: (bookingId: string) => Promise<void>;
  fetchBookings: (page?: number, limit?: number) => Promise<void>;
};

const BookingContext = createContext<BookingContextType>(null!);

export function BookingProvider({ children }: { children: React.ReactNode }) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [currentBooking, setCurrentBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { secureFetch } = useAuth();

  // Automatically clear error messages after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Fetch bookings with pagination
  const fetchBookings = useCallback(async (page = 1, limit = 10) => {
    setLoading(true);
    setError(null);
    try {
      const response = await secureFetch(`/api/bookings/?page=${page}&limit=${limit}`);
      if (!response.ok) throw new Error('Failed to fetch bookings');
      const data = await response.json();
      setBookings(prev => [...prev, ...data.results]); // Append new bookings
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch bookings');
    } finally {
      setLoading(false);
    }
  }, [secureFetch]);

  // Create a booking with optimistic updates
  const createBooking = useCallback(async (dormId: string, dates: { start: Date; end: Date }) => {
    // Validate dates
    if (dates.start >= dates.end) {
      setError('Start date must be before end date');
      return;
    }

    // Optimistic update
    const optimisticBooking: Booking = {
      id: 'temp-id', // Temporary ID
      dormId,
      startDate: dates.start.toISOString(),
      endDate: dates.end.toISOString(),
      status: 'pending',
    };

    setBookings(prev => [...prev, optimisticBooking]);
    setCurrentBooking(optimisticBooking);

    try {
      const response = await secureFetch('/api/bookings/', {
        method: 'POST',
        body: JSON.stringify({
          dorm: dormId,
          start_date: dates.start.toISOString(),
          end_date: dates.end.toISOString(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Booking failed');
      }

      const booking = await response.json();
      setBookings(prev => prev.map(b => (b.id === 'temp-id' ? booking : b))); // Replace optimistic booking
      setCurrentBooking(booking);
    } catch (err) {
      setBookings(prev => prev.filter(b => b.id !== 'temp-id')); // Revert optimistic update
      setError(err instanceof Error ? err.message : 'Booking failed');
    }
  }, [secureFetch]);

  // Cancel a booking
  const cancelBooking = useCallback(async (bookingId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await secureFetch(`/api/bookings/${bookingId}/`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Cancellation failed');

      setBookings(prev => prev.filter(b => b.id !== bookingId));
      setCurrentBooking(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cancellation failed');
    } finally {
      setLoading(false);
    }
  }, [secureFetch]);

  const value = {
    bookings,
    currentBooking,
    loading,
    error,
    createBooking,
    cancelBooking,
    fetchBookings,
  };

  return (
    <BookingContext.Provider value={value}>
      {children}
    </BookingContext.Provider>
  );
}

export const useBooking = () => {
  const context = useContext(BookingContext);
  if (!context) throw new Error('useBooking must be used within BookingProvider');
  return context;
};