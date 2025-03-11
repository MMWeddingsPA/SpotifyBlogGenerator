from openai import OpenAI
import os

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

def generate_blog_post(playlist_name, songs_df, spotify_link):
    """
    Generate a formatted blog post using ChatGPT
    """
    openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Prepare song list for prompt
    songs_list = songs_df.apply(
        lambda x: f"- {x['Song']} by {x['Artist']} "
        f"(YouTube: {x['YouTube_Link']})",
        axis=1
    ).tolist()
    songs_text = "\n".join(songs_list)
    
    prompt = f"""
    Create a blog post for a wedding DJ website about the playlist '{playlist_name}'.
    Include the following elements:
    - An engaging introduction about the playlist and its mood
    - The complete song list with YouTube links
    - The Spotify playlist link: {spotify_link}
    - A conclusion about why this playlist works well for weddings
    
    Song List:
    {songs_text}
    
    Format the post in HTML with appropriate styling and structure.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional wedding DJ blog writer."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Error generating blog post: {str(e)}")
