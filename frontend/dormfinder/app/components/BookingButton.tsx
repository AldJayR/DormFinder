import { Link } from 'react-router';

export default function BookingButton({ dormId }: { dormId: number }) {
  return (
    <Link
      to={`/book/${dormId}`}
      className="w-full inline-flex justify-center items-center bg-blue-600 text-white 
                 py-2.5 px-5 rounded-md shadow-sm hover:bg-blue-700 focus:outline-none 
                 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors 
                 duration-200 text-base font-medium"
      aria-label={`Book dorm with ID ${dormId}`}
    >
      Book Now
    </Link>
  );
}
