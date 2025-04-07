import os
from openai import OpenAI

# Updated to use standard OpenAI API with GPT-4o (since Gemini integration is having issues)
# This is a temporary fallback to ensure functionality

def generate_blog_post(playlist_name, songs_df, spotify_link=None):
    """
    Generate a formatted blog post using AI with consistent structure and style
    """
    # Use standard OpenAI client with GPT-4o
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Clean playlist name for display
    clean_name = playlist_name.split('Wedding Cocktail Hour')[0].strip()

    # Group songs into sections (4-5 songs per section)
    total_songs = len(songs_df)
    songs_per_section = min(5, max(3, total_songs // 4))

    # Prepare song sections
    sections = []
    for i in range(0, total_songs, songs_per_section):
        section_songs = songs_df.iloc[i:i + songs_per_section]
        songs_list = section_songs.apply(
            lambda x: f"- [{x['Song']} – {x['Artist']}]({x['YouTube_Link']})" 
            if x['YouTube_Link'] else f"- {x['Song']} – {x['Artist']}",
            axis=1
        ).tolist()
        sections.append("\n".join(songs_list))

    sections_text = "\n\n".join(f"Section {i+1}:\n{songs}" for i, songs in enumerate(sections))

    prompt = f"""
    Create a wedding DJ blog post for the playlist "{clean_name}" following this exact structure:

    1. Format:
    - Main title: Use the playlist name
    - Subtitle: "Your Perfect Soundtrack for Love, Laughter, and Celebration"
    - Introduction: Engaging opening about the playlist's mood and purpose
    - 4-5 themed sections, each with:
        * Descriptive title that captures the section's mood
        * Paragraph explaining why these songs work well together
        * Listed songs with links
    - Conclusion: Why this playlist works for weddings
    - Call to action with Spotify link

    2. Style Guidelines:
    - Conversational and warm tone
    - Focus on creating atmosphere and emotional moments
    - Blend practical details with romantic storytelling
    - Keep each section concise but meaningful
    - Use Markdown formatting

    3. Available Songs:
    {sections_text}

    4. Additional Details:
    Spotify Playlist Link: {spotify_link if spotify_link else '[Insert Spotify Playlist Link]'}

    Generate a unique blog post that follows this structure but varies the content and descriptions creatively while maintaining the wedding DJ expert voice.
    """

    try:
        # Debug API key (only showing if it exists, not the actual value)
        if client.api_key:
            print(f"OpenAI API Key exists: True (length: {len(client.api_key)})")
        else:
            print("OpenAI API Key does not exist")
            raise Exception("OpenAI API key not found in environment variables. Please check the OPENAI_API_KEY secret.")
            
        # Using the standard OpenAI GPT-4o model for better reliability
        # gpt-4o is the newest OpenAI model released after knowledge cutoff
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the latest OpenAI model
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert wedding DJ blog writer who understands 
                    both music and the emotional significance of wedding moments. Create content 
                    that is both professional and personally engaging."""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        
        # Return the generated content
        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"Error generating blog post: {str(e)}")