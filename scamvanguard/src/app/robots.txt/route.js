export async function GET() {
  const robots = `User-agent: *
Allow: /

# Priority pages for indexing
Allow: /how-it-works
Allow: /privacy
Allow: /terms

# Lower priority pages
Allow: /unsubscribe

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