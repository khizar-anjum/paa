/** @type {import('next').NextConfig} */

// Check if we're building for mobile
const isMobileBuild = process.env.BUILD_TARGET === 'mobile';

const webConfig = {
  // Existing web configuration (unchanged)
};

const mobileConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  // Mobile-specific environment variables
  env: {
    NEXT_PUBLIC_IS_MOBILE_BUILD: 'true',
    NEXT_PUBLIC_MOBILE_API_URL: process.env.NEXT_PUBLIC_MOBILE_API_URL || 'http://192.168.1.216:8000'
  }
};

module.exports = isMobileBuild ? mobileConfig : webConfig;