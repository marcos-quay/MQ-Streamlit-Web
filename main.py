import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
from google.cloud import storage
import streamlit as st
import plotly.express as px
import json
import pandas as pd
import random
import re

certificate = json.loads(st.secrets["GCP_CERTIFICATE"])

if not firebase_admin._apps:
    cred = credentials.Certificate(certificate)
    firebase_admin.initialize_app(cred)

db = firestore.client()
storage_client = storage.Client(project='mq-video-app')

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
    all_coaches = [name.strip().title() for name in all_coaches]
    emails = [email.strip().lower() for email in emails]

    return all_coaches, emails

# Function to update the "coaches" field of a video document


def update_coaches(video_name, coaches):
    if type(video_name) == list:
        for video in video_name:
            doc_ref = db.collection("videos").document(video)
            doc_ref.update({"coaches": coaches})
    else:
        doc_ref = db.collection("videos").document(video_name)
        doc_ref.update({"coaches": coaches})

# write a function to reset the coaches field of all the documents in the collection


def reset_coaches():
    docs = db.collection("videos").get()
    for doc in docs:
        doc.reference.update({"coaches": []})


def create_pie_chart():
    docs = db.collection("videos").get()
    pie_chart_data = {}  # {video_name: coaches_count}

    for doc in docs:
        doc_dict = doc.to_dict()
        if doc_dict['coaches']:
            url = doc_dict['URL']
            video_name = url.split('/')[-1].split('.')[0]
            pie_chart_data[video_name] = len(doc_dict['coaches'])

    fig = px.pie(values=list(pie_chart_data.values()),
                 names=list(pie_chart_data.keys()))
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(uniformtext_minsize=16, uniformtext_mode='hide')

    return fig


def add_to_firebase(blobs, bucket_name="mq-videos", collection_name="videos"):
    count_new = 0
    count_old = 0

    for blob in blobs:
        video_url = f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
        video_name = blob.name.split('/')[-1].split('.')[0]

        # Add the video to Firebase if it doesn't already exist
        doc_ref = db.collection(collection_name).document(video_name)
        doc = doc_ref.get()

        if not doc.exists:
            doc_ref.set({
                "URL": video_url,
                "coaches": []
            })
            count_new += 1

            st.write(f"Added video {video_name} to Firebase collection")
        else:
            count_old += 1

    st.write(f"Added {count_new} new videos to Firebase collection")
    st.write(f"{count_old} videos already existed in Firebase collection")


def generate_password(user_name):
    name = user_name.split(' ')[0]
    password = name.capitalize() + str(int(random.random()*1000))
    if len(password) < 6:
        password = password + '0'*(6-len(password))
    return password

# Function to create a user in Firebase Authentication


def create_user(name, email, password):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name.title(),
        )
    except Exception as e:
        st.error(f"Error creating user: {e} \t for email: {email}")

    return user


def check_emails(email_addresses):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    correct_emails = 0

    for idx, email in enumerate(email_addresses):
        if (re.fullmatch(regex, email.strip())):
            correct_emails += 1
            continue
        else:
            st.warning(f"Invalid Email: {email}")

    if correct_emails == len(email_addresses):
        return True

    return False


def delete_user(emails):
    for email in emails:
        try:
            user = auth.get_user_by_email(email)
            auth.delete_user(user.uid)
            st.success(f"Deleted user with email: {email}")
        except Exception as e:
            st.error(f"Error deleting user: {e} \t for email: {email}")


def main():
    st.title("Video Coaches Editor")

    all_coaches, emails = get_coaches_names()
    all_email_name_dict = dict(zip(emails, all_coaches))
    all_name_email_dict = dict(zip(all_coaches, emails))

    grouped_coaches = {
        "Random Group 1": all_coaches[:len(all_coaches)//3],
        "Random Group 2": all_coaches[len(all_coaches)//3:2*len(all_coaches)//3],
        "Random Group 3": all_coaches[2*len(all_coaches)//3:]
    }

    videos = get_category_video_names("videos")

    with st.sidebar:
        selected = st.radio("Select Option", [
                            "Assign Videos", "Add New Videos", "Add New Coaches", "Delete Coaches"])

    if selected == "Assign Videos":
        st.markdown(
            "**You can select multiple videos at a time from the same sport**")
        selected_sport = st.selectbox("Select Sport", list(videos.keys()))

        video_name = st.multiselect("Select Video", videos[selected_sport])
        st.write(video_name)

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

        st.header("Video - Coaches Distribution")
        fig = create_pie_chart()
        st.plotly_chart(fig, use_container_width=True)

    elif selected == "Add New Videos":
        st.markdown("""Upload new videos to Google Cloud: [Upload Videos](https://console.cloud.google.com/storage/browser/mq-videos/MQ-Videos-All)

**Note:**
1. Videos cannot have the same name
2. Upload videos to the correct folder
3. If folder doesn't exist, create a new folder with the name of the sport
4. Once the videos are uploaded, click on the "Add to Firebase" button below. \
This will add the videos to the Firebase collection. \
Without this step, the videos won't be visible in the app.
                    
This will only add new videos, old videos will not be affected.

To check if the videos have been added to Firebase, go to the \
[Firebase console](https://console.firebase.google.com/u/0/project/mq-video-app/firestore/data/~2Fvideos~2F) \
and check if the videos are visible there. 

All access is given to Raahil's email (raahil@marcosquay.com)                

For any issues, contact Arihant: [Call](tel:+918433567777) | [WhatsApp](https://wa.me/918433567777) 
""")
        bucket_name = 'mq-videos'
        bucket = storage_client.bucket(bucket_name)
        collection_name = 'videos'
        blobs = storage_client.list_blobs(bucket_name)

        if st.button("Add to Firebase"):
            add_to_firebase(blobs, bucket_name, collection_name)

    elif selected == "Add New Coaches":
        existing_coaches_df = pd.read_excel("coach_details.xlsx")
        st.markdown(f"""**Note:**
1. Upload an excel or csv file with the following columns: `Name`, `Email`. \
Column names are not case sensitive (i.e. `name` and `Name` are both valid).

Example: """)

        st.dataframe(existing_coaches_df.head())

        st.markdown("""
2. Excel can contain previous coaches as well. Only new coaches will be added to Firebase.
                    
3. Once the file is uploaded, click on the "Add to Firebase" button below. \
This will only add new coaches, old coaches will not be affected.
                    
4. Once added, an excel file will be available for download. \
This file will contain the list of all coaches in Firebase with their emails and passwords. \
Make sure to save this file. This file will not be available after you close the app.
""")

        uploaded_file = st.file_uploader(
            "Upload Coach Details File", type=["xlsx", "csv"])

        # Validate the uploaded file
        if uploaded_file:
            if uploaded_file.name.split('.')[-1] == 'xlsx':
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)

            df.columns = df.columns.str.lower()
            if 'name' in df.columns and 'email' in df.columns:
                st.success("File uploaded successfully!")
                uploaded_names = df['name'].tolist()
                uploaded_names = [name.strip().title()
                                  for name in uploaded_names]
                uploaded_emails = df['email'].tolist()
                uploaded_emails = [email.strip().lower()
                                   for email in uploaded_emails]
                uploaded_email_name_dict = dict(
                    zip(uploaded_emails, uploaded_names))
            else:
                st.error(
                    "Please upload a file with the columns 'Name' and 'Email'.")

            if st.button("Add to Firebase"):
                all_coaches, emails = get_coaches_names()
                new_coaches_emails = sorted(
                    list(set(uploaded_emails) - set(emails)))
                new_coaches_names = [uploaded_email_name_dict[x]
                                     for x in new_coaches_emails]

                if len(new_coaches_emails) == 0:
                    st.warning("No new coaches to add!")
                else:
                    if not check_emails(new_coaches_emails):
                        st.error(
                            "Please correct the emails and upload the file again.")
                    else:
                        st.success("All emails are valid!")
                        passwords = []
                        for name, email in zip(new_coaches_names, new_coaches_emails):
                            password = generate_password(name)
                            passwords.append(password)
                            create_user(name, email, password)

                        user_details = pd.DataFrame(
                            {
                                'name': new_coaches_names,
                                'email': new_coaches_emails,
                                'password': passwords
                            }
                        )
                        st.success(
                            f"Added {len(new_coaches_emails)} new coaches to Firebase")
                        st.download_button(label="Download Coach Login Details", data=user_details.to_csv(
                            index=False), file_name='coach_logins.csv', mime='text/csv')

    elif selected == "Delete Coaches":
        coaches_delete_names = st.multiselect(
            label="Select coaches to be deleted", options=all_coaches)
        coaches_delete_emails = [all_name_email_dict[x]
                                 for x in coaches_delete_names]
        st.write(coaches_delete_names)

        if st.button("Delete Coaches"):
            delete_user(coaches_delete_emails)
            all_coaches, emails = get_coaches_names()
            all_email_name_dict = dict(zip(emails, all_coaches))
            all_name_email_dict = dict(zip(all_coaches, emails))


if __name__ == "__main__":
    main()
