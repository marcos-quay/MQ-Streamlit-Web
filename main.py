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

# Function to update the "Coaches" field of a video document
def update_coaches(video_name, coaches):
    doc_ref = db.collection("VIdeonew").document(video_name)
    doc_ref.update({"Coaches": coaches})

# Streamlit web page


def main():
    st.title("Video Coaches Editor")

    available_coaches = {
        "Group 1": ["coach1@gmail.com", "coach2@gmail.com", "coach3@gmail.com"],
        "Group 2": ["coach3@gmail.com", "coach4@gmail.com", "coach5@gmail.com"],
        "Group 3": ["coach1@gmail.com", "coach4@gmail.com", "coach6@gmail.com"],
    }

    all_coaches = sorted(list(
        set([coach for coaches in available_coaches.values() for coach in coaches])))

    videos = {
        "Cricket": ["Cricket Video 1", "Cricket Video 2", "Cricket Video 3"],
        "Football": ["Football Video 1", "Football Video 2", "Football Video 3"],
        "Hockey": ["Hockey Video 1", "Hockey Video 2", "Hockey Video 3"],
        "Basketball": ["Basketball Video 1", "Basketball Video 2", "Basketball Video 3"],
    }

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

    # Edit group of coaches
    # if st.button("Edit Group"):
    #     available_coaches[selected_group] = edited_coaches
    #     st.success(f"Group '{selected_group}' edited successfully!")

    # Display selected coaches
    st.write(f"Selected Coaches: {edited_coaches}")

    # Update button
    if st.button("Update Coaches"):
        if video_name and edited_coaches:
            # update_coaches(video_name, selected_coaches)
            update_coaches('Video1', edited_coaches)
            st.success(
                f"Coaches for video '{video_name}' updated successfully!")
        else:
            st.warning(
                "Please enter both video name and select at least one coach.")


if __name__ == "__main__":
    main()
