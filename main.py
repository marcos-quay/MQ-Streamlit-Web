import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
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

    videos = dict(sorted(videos.items()))
    videos = {k: sorted(v) for k, v in videos.items()}
    return videos

# Function to get all the coaches names from firebase auth
def get_coaches_names():
    safe_uids = [
        'V5sJwczRcUf2SEmmNKsTJ4V2JA72',  # Shivam
        'm8UvYx0hEOVnowVjypvfaQHwTjf2',  # Arihant
        'XrU7QDoN9WYJUpJ36snjc7NBIih1'  # Aagam
    ]

    users = auth.list_users().iterate_all()
    all_coaches = []
    emails = []

    for user in users:
        if user.uid in safe_uids:
            continue

        all_coaches.append(user.display_name)
        emails.append(user.email)

    # sort both lists by all_coaches
    all_coaches, emails = zip(*sorted(zip(all_coaches, emails)))

    return all_coaches, emails

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

    all_coaches, emails = get_coaches_names()

    grouped_coaches = {
        "Random Group 1": all_coaches[:len(all_coaches)//3],
        "Random Group 2": all_coaches[len(all_coaches)//3:2*len(all_coaches)//3],
        "Random Group 3": all_coaches[2*len(all_coaches)//3:]
    }

    videos = get_category_video_names("videos")

    selected_sport = st.selectbox("Select Sport", list(videos.keys()))

    # Radio buttons for videos
    video_name = st.radio("Select Video", videos[selected_sport])

    st.header(f"You selected: {video_name}")

    selected_group = st.selectbox(
        "Select Coach Group", list(grouped_coaches.keys()))

    selected_coaches = grouped_coaches[selected_group]

    # Multi-select dropdown for coaches
    edited_coaches_names = st.multiselect("Select Coaches",
                                          options=all_coaches,
                                          default=selected_coaches)

    edited_coaches_emails = []
    for coach in edited_coaches_names:
        edited_coaches_emails.append(emails[all_coaches.index(coach)])

    # Display selected coaches
    st.header("Selected Coaches:")
    col1, col2 = st.columns(2)
    for idx, coach_name in enumerate(edited_coaches_names):
        if idx % 2 == 0:
            with col1:
                st.markdown(f"**{idx+1}. {coach_name}**")
        else:
            with col2:
                st.markdown(f"**{idx+1}. {coach_name}**")

    # Update button
    if st.button("Update Coaches"):
        if video_name and edited_coaches_emails:
            update_coaches(video_name, edited_coaches_emails)
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
