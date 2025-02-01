import { createFileRoute } from '@tanstack/react-router'
import { BookingWizard } from '@/components/booking/Wizard'
import { redirect } from 'react-router'

export const Route = createFileRoute('/_protected/booking/$dormId')({
  component: () => (
    <SecureBookingLayout>
      <BookingWizard />
    </SecureBookingLayout>
  ),
  beforeLoad: ({ context }) => {
    if (!context.auth.isVerified) {
      throw redirect({ to: '/verify' })
    }
  }
})