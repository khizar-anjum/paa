// flowglad.ts
import { FlowgladServer } from '@flowglad/nextjs/server'

// For hackathon demo, use a simple configuration
export const flowgladServer = new FlowgladServer({
  getRequestingCustomer: async () => {
    // Return demo user for hackathon
    return { 
      externalId: 'demo-user',
      name: 'Demo User',
      email: 'demo@example.com' 
    }
  }
})