// Robots.txt for search engines
export async function GET() {
  const robots = `User-agent: *
Allow: /

# Block admin or private paths if you have any
# Disallow: /admin/
# Disallow: /api/

# Crawl-delay for respectful crawling
Crawl-delay: 1

# Sitemap location
Sitemap: https://scamvanguard.com/sitemap.xml`;

  return new Response(robots, {
    headers: {
      'Content-Type': 'text/plain',
    },
  });
}