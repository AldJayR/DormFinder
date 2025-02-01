import { Link } from 'react-router';
import type { Dorm } from '~/types';
import BookingButton from './BookingButton';

export default function DormCard({ dorm }: { dorm: Dorm }) {
  return (
    <div className="border rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300 bg-white">
      <img
        src={dorm.thumbnail}
        alt={`${dorm.name} thumbnail`}
        className="w-full h-48 object-cover"
        loading="lazy"
        style={{ aspectRatio: '16 / 9' }}
      />

      <div className="p-4 space-y-3">
        {/* Dorm Name */}
        <h3 className="text-xl font-semibold text-gray-900">
          <Link
            to={`/dorms/${dorm.id}`}
            className="hover:text-blue-600 transition-colors duration-200"
          >
            {dorm.name}
          </Link>
        </h3>

        <div className="flex justify-between items-center">
          <span className="text-lg font-bold text-green-600">₱{dorm.monthlyRate}/mo</span>
          <span className="text-sm text-gray-600">{dorm.distanceFromSchool} mins walk</span>
        </div>

        <div className="mt-2">
          <BookingButton dormId={dorm.id} />
        </div>
      </div>
    </div>
  );
}