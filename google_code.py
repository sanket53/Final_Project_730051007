from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from langdetect import detect, DetectorFactory

# Set seed for reproducibility in language detection
DetectorFactory.seed = 0

def retrieve_comments(video_id, max_results=100, next_page_token=None):
    all_comments = []
    seen_comments = set()

    while len(all_comments) <= 4000000:
        try:
            # Set up the YouTube Data API service
            youtube = build('youtube', 'v3', developerKey='AIzaSyDRFNQKxkYhZRUES9JLiB3nPy1oJgiCC_c')

            # Request comments for the video
            request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=max_results,
                pageToken=next_page_token,
                textFormat='plainText'
            )
            response = request.execute()

            # Extract comments from response
            for comment in response['items']:
                top_comment = comment['snippet']['topLevelComment']['snippet']
                comment_text = top_comment['textDisplay']
                
                # Detect language and filter for English comments
                try:
                    if detect(comment_text) == 'en' and comment_text not in seen_comments:
                        comment_data = {
                            'commentId': comment['id'],
                            'videoId': video_id,
                            'publishedAt': top_comment['publishedAt'],
                            'updatedAt': top_comment['updatedAt'],
                            'likeCount': top_comment['likeCount'],
                            'textDisplay': top_comment['textDisplay'],
                            'totalReplyCount': comment['snippet']['totalReplyCount'],
                            'parentId': comment['snippet'].get('parentId')
                        }
                        all_comments.append(comment_data)
                        seen_comments.add(comment_text)
                        
                        # Extract replies if they exist
                        if 'replies' in comment:
                            for reply in comment['replies']['comments']:
                                reply_snippet = reply['snippet']
                                reply_data = {
                                    'commentId': reply['id'],
                                    'videoId': video_id,
                                    'publishedAt': reply_snippet['publishedAt'],
                                    'updatedAt': reply_snippet['updatedAt'],
                                    'likeCount': reply_snippet['likeCount'],
                                    'textDisplay': reply_snippet['textDisplay'],
                                    'totalReplyCount': 0,  # Replies do not have further replies in this context
                                    'parentId': reply_snippet['parentId']
                                }
                                all_comments.append(reply_data)
                                seen_comments.add(reply_snippet['textDisplay'])

                except:
                    continue  # Skip comments where language detection fails

            # Check if there are more comments available
            if 'nextPageToken' in response:
                next_page_token = response['nextPageToken']
            else:
                break  # No more comments available

        except HttpError as e:
            print(f'An HTTP error occurred: {e}')
            break

        except Exception as e:
            print(f'An error occurred: {e}')
            break

    return all_comments

# Example: Retrieve comments for a video
video_id = 'QdBZY2fkU-0'
all_comments = retrieve_comments(video_id)

# Convert the list of comments to a pandas DataFrame
df_comments = pd.DataFrame(all_comments)

# Print the number of comments retrieved
total_comments = len(df_comments)
print(f'Total comments retrieved: {total_comments}')

# Display the first few rows of the DataFrame
print(df_comments.head())

# Save the comments to a CSV file
df_comments.to_csv('GTA6_Trailer.csv', index=False)
