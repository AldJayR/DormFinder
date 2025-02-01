export type Dorm = {
  id: number;
  name: string;
  monthlyRate: number;
  distanceFromSchool: number;
  thumbnail: string;
  amenities: string[];
};

export type DormFilters = {
  maxPrice: number;
  maxDistance: number;
  amenities: string[];
};

export type BookingCreate = {
  dormId: number;
  startDate: string;
  endDate: string;
};
