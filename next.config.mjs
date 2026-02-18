/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'monaco-editor': 'monaco-editor/esm/vs/editor/editor.api.js',
    }
    return config
  },
}

export default nextConfig
