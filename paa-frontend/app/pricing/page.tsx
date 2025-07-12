// /pricing/page.tsx
import { PricingTable } from '@flowglad/nextjs'

export default function Pricing() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            Choose Your Plan
          </h2>
          <p className="mt-4 text-xl text-gray-600">
            Unlock the full potential of your Personal AI Assistant
          </p>
        </div>
        
        <div className="mt-12">
          <PricingTable />
        </div>
      </div>
    </div>
  )
}