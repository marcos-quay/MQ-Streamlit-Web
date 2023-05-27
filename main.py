import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import streamlit as st
import json

certificate = json.loads(st.secrets["textkey"])

if not firebase_admin._apps:
    cred = credentials.Certificate(certificate)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Function to generate names of videos and categories
def get_category_video_names(collection_name):
    docs = db.collection(collection_name).get()
    videos = {}

    for doc in docs:
        url = doc.to_dict()['URL']
        category = url.split('/')[-2]
        videos[category] = []

    for doc in docs:
        url = doc.to_dict()['URL']
        category = url.split('/')[-2]
        video_name = url.split('/')[-1].split('.')[0]
        videos[category].append(video_name)

    return videos

# Function to update the "coaches" field of a video document
def update_coaches(video_name, coaches):
    doc_ref = db.collection("videos").document(video_name)
    doc_ref.update({"coaches": coaches})

# write a function to reset the coaches field of all the documents in the collection
def reset_coaches():
    docs = db.collection("videos").stream()
    for doc in docs:
        doc.reference.update({"coaches": []})

def main():
    st.title("Video Coaches Editor")

    available_coaches = {
        "Group 1": ["coach1@gmail.com", "coach2@gmail.com", "coach3@gmail.com"],
        "Group 2": ["coach3@gmail.com", "coach4@gmail.com", "coach5@gmail.com"],
        "Group 3": ["coach1@gmail.com", "coach4@gmail.com", "coach6@gmail.com"],
    }

    all_coaches = sorted(list(
        set([coach for coaches in available_coaches.values() for coach in coaches])))

    videos = get_category_video_names("videos")

    selected_sport = st.selectbox("Select Sport", list(videos.keys()))

    # Radio buttons for videos
    video_name = st.radio("Select Video", videos[selected_sport])

    st.write(f"You selected: {video_name}")

    selected_group = st.selectbox("Select Coach Group", list(available_coaches.keys()))

    selected_coaches = available_coaches[selected_group]

    # Multi-select dropdown for coaches
    edited_coaches = st.multiselect("Select Coaches",
                                    options=all_coaches,
                                    default=selected_coaches)

    # Display selected coaches
    st.write(f"Selected Coaches: {edited_coaches}")

    # Update button
    if st.button("Update Coaches"):
        if video_name and edited_coaches:
            # update_coaches(video_name, selected_coaches)
            update_coaches(video_name, edited_coaches)
            st.success(
                f"Coaches for video '{video_name}' updated successfully!")
        else:
            st.warning(
                "Please enter both video name and select at least one coach.")
            
    if st.button("Reset Coaches"):
        reset_coaches()
        st.success("Coaches reset successfully!")


if __name__ == "__main__":
    main()
