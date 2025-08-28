import fetch from "node-fetch";

export async function handler(event, context) {
  try {
    const query = event.queryStringParameters.query || "relaxing music";

    // Example using YouTube Search API (RapidAPI / YouTube Data API)
    const apiKey = process.env.YOUTUBE_API_KEY; // store in Netlify env vars
    const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q=${encodeURIComponent(
      query
    )}&key=${apiKey}`;

    const response = await fetch(url);
    const data = await response.json();

    // Map response to useful info
    const songs = data.items.map((item) => ({
      title: item.snippet.title,
      url: `https://www.youtube.com/watch?v=${item.id.videoId}`,
    }));

    return {
      statusCode: 200,
      body: JSON.stringify({ songs }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message }),
    };
  }
}
