import streamlit as st
import json
import gspread

state = st.session_state
if 'name' not in state:
    state.name = None

name_to_example_range_and_pattern = {
    'Gili': (range(21), 0),
    'Natali': (range(21), 1),
    'Uri': (range(21), 2),
    'Avinadav': (range(21, 42), 0),
    'Tal': (range(21, 42), 1),
    'Alex': (range(21, 42), 2),
    'Judy': (range(42, 63), 0),
    'Lior': (range(42, 63), 1),
}

patterns = [
    ['my', 'blip', 'human'],
    ['blip', 'human', 'my'],
    ['human', 'my', 'blip']
]

# Find samples which were not annotated (if such exists)
def find_next_sample(image_to_annotaion_tag):
    example_range, pattern_ind = name_to_example_range_and_pattern[state.name]
    pattern = patterns[pattern_ind]
    for i in example_range:
        source = pattern[i % 3]
        state.source = source
        image_id = state.data[source][i][0]
        if image_id not in image_to_annotaion_tag or source not in image_to_annotaion_tag[image_id]:
            return state.data[source][i]
    return None

def run_with_name():
    st.subheader('Instructions')
    st.markdown('You will be presented with images and corresponding descriptions, and will need to answer questions about the descriptions.')

    st.subheader('Example')
    st.image('images/example.jpg', width=350)
    
    st.markdown('1. Does the description describe something that is not in the image? (yes/no)')
    st.markdown('Description example: "A cat and a dog playing with a shoe"')
    st.markdown('Answer: Yes')

    st.markdown('2. Does the description use an incorrect word to describe one of the objects/activities in the image? (yes/no)')
    st.markdown('Description example: "A cat playing with a hat"')
    st.markdown('Answer: Yes')

    st.markdown('3. On a scale of 1 to 5, how creative is the description, 1 being not creative and highly expected and 5 being highly creative.')
    st.markdown('Description example: "Cat playing with shoe"')
    st.markdown('Answer: 1')
    st.markdown('Description example: "A small kitten, so joyful that even a shoe is considered a toy"')
    st.markdown('Answer: 5')

    st.markdown('4. On a scale of 1 to 5, how simple is the language of the description, 1 being very simple and understandable for non-experts and 5 being highly complex with expertise in English needed to understand the description.')
    st.markdown('Description example: "Cat playing with an old shoe"')
    st.markdown('Answer: 1')
    st.markdown('Description example: "A blithe cat, toying with an antique footgear"')
    st.markdown('Answer: 5')

    st.markdown('5. On a scale of 1 to 5, how complete is the description in describing the image, 1 being very incomplete with many components of the image missing in the description and 5 being complete with each detail of the image being described.')
    st.markdown('Description example: "A cat"')
    st.markdown('Answer: 1')
    st.markdown('Description example: "A cat laying on grass and playing with a shoe, while something that is out of the picture making a shadow on the top right"')
    st.markdown('Answer: 5')

    st.markdown('6. On a scale of 1 to 5, how detailed is the description in describing the properties (such as color, model, shape etc.) of the main objects in the image, 1 being not detailed at all (just naming the objects) and 5 being highly detailed (mentioning many properties).')
    st.markdown('Description example: "A cat playing with a shoe"')
    st.markdown('Answer: 1')
    st.markdown('Description example: "A gray-colored young house cat playing with a brown and old-looking shoe"')
    st.markdown('Answer: 5')

    st.markdown('7. On a scale of 1 to 5, how much does the description describe things that are not explicitly in the image but might be reasonably inferred from the image (such as relation between people in the image, activities that are commonly performed before/after what is in the image etc.), 1 being not at all (the description describes only what is explicit in the image) and 5 being highly descriptive of implicit information.')
    st.markdown('Description example: "A cat playing with a shoe"')
    st.markdown('Answer: 1')
    st.markdown('Description example: "A joyful cat playing with a shoe that someone gave it"')
    st.markdown('Answer: 5')

    st.markdown('8. On a scale of 1 to 5, how much does the description use subjective adjectives to describe objects?')
    st.markdown('Description example: "A cat playing with a shoe"')
    st.markdown('Answer: 1')
    st.markdown('Description example: "A beautiful cat playing with an old looking shoe"')
    st.markdown('Answer: 5')

    st.markdown('9. How many objects are mentioned in the description? If the description uses numeral expressions, consider it as a mention of the numeral value of the expression (e.g., “five dogs and two cats” should be considered as 7 objects mentioned, not 2), and include cases where the description mistakenly mentions objects not in the image (if the description mentions 3 dogs but there are only 2 in the image, count it as 3).')
    st.markdown('Description example: "A cat playing with a shoe"')
    st.markdown('Answer: 2')
    st.markdown('Description example: "Two cats playing with a shoe"')
    st.markdown('Answer: 3')

    st.markdown('10. On a scale of 1 to 5, how would you rate the overall quality of the description? I.e., is it a good description of the image?.')
    st.markdown('Description example: "A dog eating a cake."')
    st.markdown('Answer: 1')

    st.markdown('# Annotation')

    # First, we need a utility function to check which annotations we have for each image;
    # we'll use it later to find unannoated images
    # This function assumes that state.ws is the google sheet worksheet which is already initialized
    def create_image_to_annotation_tag():
        rows = state.ws.get_all_values()
        res = {}
        for row in rows:
            image_id = int(row[0])
            if image_id not in res:
                res[image_id] = []
            res[image_id].append(row[1])
        return res

    # Each new time someone enters the app, the state is re initialized. So we need to reload the worksheet and data
    if 'ws' not in state:
        # Reload the worksheet
        # 1. First, credentials. To reproduce follow the instructions in https://docs.gspread.org/en/latest/oauth2.html,
        # in the "For Bots: Using Service Account" section
        credentials = {
            "type": "service_account",
            "project_id": "interactive-image-captioning",
            "private_key_id": "19b5cacdac12193a25c31cd0f4ff1efff3a73db3",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCnxrGMKYq5Xf96\njibp3QgVGyLc1ASwowbaKlkS5ex6o7ywvrzibCU5j+vgaKwM4qRDN7SkeT/2sLtl\ne2YW6jm67XkiekmNpveRxYXWX3hkksSEWNeAFb0/v7e1UXEbvGvI5q2I/KrxrHBc\ncVFQkrZ6iuWBR3KqErUSGxnJJGXNHTTy8Hb9FY6plF7bMKbTPShe3QaYrDjRLIKI\nRAxYkSwVxMsIpA2nmguSqcIU7K4jnq8vQw0aihSV27d9Q1oJAfodb8CQARP56O9o\nk+8bDh4xZQ6PrdFRXV7UVSXZqqnxTDZGPYA1oHq4f5vzW8jEANM0LBclXwHzkNNg\n2jUKs73vAgMBAAECggEAEhYoY7zCuLL6bKLQbRun2Gahfn7YtpYMkg5IpfHlaV8n\nY0JcqGgSJz9tpTaDfawdGyXxMl3j2Fs7CHiiC8xaRt181ouqTDv4ql1JzU9jciwk\nRUQyjxtI2It5aXGLKPtJ/1Fm2cKrRvxY7I5GvtHiHBnHHgWuxcjYfkgvonBrDQ5w\n+EQsH+mziOKEVu+aqCSQOTUyHzHRglpxogQ6FZZvzO3tvUgUmpxSIUFtCBZN/Clg\n1yIaQAQ7lOajI96+aH24xIgXJ1cDoWtoc+89RjYs5xlK5GoXTCbGfZwE04tWwKfD\nRD+pbEn420S55Zolhu+vzEBpcrQ1MVe0mAgxSl5sSQKBgQDqBt01UeQUCiDPwTm9\n26LAqYJ9n61bTWWQotWwihivy0OMnYXQL/Up6wzDuHKeAlbxIbBbxECigKCx5n7d\nqRO5xFWYLE+SdhBMziv+5ACCoZaBVsUKyU51S66xk/Ln7ANzaQDpq7281mpbFpBZ\n+4PnLFHDsHyPsZgUpBWhNHCLYwKBgQC3h2jLCEmF1Z7skjr5WsUvcZ2FhCPV73gZ\nHzseZR3iUL9A+8ZNUC/aGNPOgzMmCQagyvmomaFUeWBFFyb2XoyNcmY58qJcW8Tb\nAjGv4bQaaRCJLLLeSval1TuCT6Pj79CAC+ju9CYGWCbSQvB/Ffyfpkz7+y8M/02S\nyzu+GlJ3BQKBgAgicPH3hLwFlhpilwU4azHTMov3TulLiWo7nr3iLvV9VT3AA/S2\nlgj8+JadBK7lWexLxXuLGMwNOIi2gFZoGB1u66K8d4+ZtvtUd0cG2dWwlDCuuW6k\njKubE9lsURcqpvwN/FAi/hdgRJYh9KaMDYutiLIKomnEPIsLIQ1Xa0oNAoGAWAy8\n9/uH2o+8aV9Wr98ejz6BBld5IeB7zAGxyUlV5wg6WaDxaJI6Ava6V2+WkH7wESCQ\nWpUqU27QAxWyeayu3gWuicqgnpLghPougGVWlP0nE8jAH+nzH2iH3mL7DBY3/9a2\n8D1uKMkOBv5ah34y7x1H/fRqhF/QBcc/aFsUiUkCgYB7oXSmILlRXaSKDfn88wOd\ndFmd9bpv/VnFMDigIF2mW4OelyfH3TzlcXmEaVxo3N99J5qVxJSsu+i9cfxh33xr\nnaTcUrNgTvptKGm9a6FWEx/miThTrtlGDnv4uTcrzVz0lpgt55a8k4UBAX1+TcIt\nDHpwYtH3hVFP5iOGd0YD9Q==\n-----END PRIVATE KEY-----\n",
            "client_email": "newuriid@interactive-image-captioning.iam.gserviceaccount.com",
            "client_id": "112001972845336169370",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/newuriid%40interactive-image-captioning.iam.gserviceaccount.com"
        }
        gc = gspread.service_account_from_dict(credentials)
        # 2. Load the sheet
        sh = gc.open("annotation_pilot2")
        # 3. Open the specific worksheet
        state.ws = sh.worksheet('Sheet1')
        state.current_sample = None

        # Load the data needs to be annotated
        with open('my_data.json', 'r') as fp:
            my_data = json.load(fp)
        with open('blip_data.json', 'r') as fp:
            blip_data = json.load(fp)
        with open('human_data.json', 'r') as fp:
            human_data = json.load(fp)
        state.data = {'my': my_data, 'blip': blip_data, 'human': human_data}

        image_to_annotaion_tag = create_image_to_annotation_tag()
        next_sample = find_next_sample(image_to_annotaion_tag)
        if next_sample is not None:
            state.current_sample = next_sample

    # Next, this is the function that will be called whenever a user finish an annotation, that is, presses the "next" button
    def annotate():
        image_id = state.current_sample[0]

        # Update the google sheet
        # 1. Find in which row we need to put the new annotations
        next_row_ind = len(state.ws.col_values(1)) + 1
        # 2. Update the sheet
        state.ws.update('A' + str(next_row_ind), str(image_id))
        state.ws.update('B' + str(next_row_ind), state.source)
        cols = ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
        for i in range(len(cols)):
            if i in state.res:
                state.ws.update(cols[i] + str(next_row_ind), str(state.res[i]))
            elif i in [2, 3, 4, 5, 6, 7, 9]:
                state.ws.update(cols[i] + str(next_row_ind), '3')

        state.res = {}

        # Search for samples which were not annotated again
        image_to_annotaion_tag = create_image_to_annotation_tag()
        next_sample = find_next_sample(image_to_annotaion_tag)
        if next_sample is not None:
            state.current_sample = next_sample
        else:
            state.current_sample = None

    # If we have un annotated samples, present to the user. Otherwise, state that everything is annotated
    if state.current_sample is not None:
        sample = state.current_sample
        if 'res' not in state:
            state.res = {}

        image_name = 'images/COCO_val2014_' + str(sample[0]).zfill(12) + '.jpg'
        st.image(image_name, width=350)
        st.markdown('*Description*: ' + sample[1])

        st.markdown('1. Does the description describe something that is not in the image?')
        if st.button(label='Yes', key='question_1_yes_button'):
            state.res[0] = 'yes'
        if st.button(label='No', key='question_1_no_button'):
            state.res[0] = 'no'

        st.markdown('2. Does the description use an incorrect word to describe one of the objects/activities in the image?')
        if st.button(label='Yes', key='question_2_yes_button'):
            state.res[1] = 'yes'
        if st.button(label='No', key='question_2_no_button'):
            state.res[1] = 'no'

        def record_question_3():
            state.res[2]=state.question_3_slider

        st.markdown('3. On a scale of 1 to 5, how creative is the description, 1 being not creative and highly expected and 5 being highly creative.')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_3, key='question_3_slider')

        def record_question_4():
            state.res[3]=state.question_4_slider

        st.markdown('4. On a scale of 1 to 5, how simple is the language of the description, 1 being very simple and understandable for non-experts and 5 being highly complex with expertise in English needed to understand the description.')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_4, key='question_4_slider')

        def record_question_5():
            state.res[4]=state.question_5_slider

        st.markdown('5. On a scale of 1 to 5, how complete is the description in describing the image, 1 being very incomplete with many components of the image missing in the description and 5 being complete with each detail of the image being described.')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_5, key='question_5_slider')

        def record_question_6():
            state.res[5]=state.question_6_slider

        st.markdown('6. On a scale of 1 to 5, how detailed is the description in describing the properties (such as color, model, shape etc.) of the main objects in the image, 1 being not detailed at all (just naming the objects) and 5 being highly detailed (mentioning many properties).')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_6, key='question_6_slider')

        def record_question_7():
            state.res[6]=state.question_7_slider

        st.markdown('7. On a scale of 1 to 5, how much does the description describe things that are not explicitly in the image but might be reasonably inferred from the image (such as relation between people in the image, activities that are commonly performed before/after what is in the image etc.), 1 being not at all (the description describes only what is explicit in the image) and 5 being highly descriptive of implicit information.')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_7, key='question_7_slider')

        def record_question_8():
            state.res[7]=state.question_8_slider

        st.markdown('8. On a scale of 1 to 5, how much does the description use subjective adjectives to describe objects?')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_8, key='question_8_slider')

        def record_question_9():
            state.res[8]=state.question_9_text_input

        st.markdown('9. How many objects are mentioned in the description? If the description uses numeral expressions, consider it as a mention of the numeral value of the expression (e.g., “five dogs and two cats” should be considered as 7 objects mentioned, not 2), and include cases where the description mistakenly mentions objects not in the image (if the description mentions 3 dogs but there are only 2 in the image, count it as 3).')
        value = ''
        if 8 in state.res:
            value = state.res[8]
        st.text_input(label='', on_change=record_question_9, key='question_9_text_input', value=value)

        def record_question_10():
            state.res[9]=state.question_10_slider

        st.markdown('10. On a scale of 1 to 5, how would you rate the overall quality of the description? I.e., is it a good description of the image?.')
        st.slider(label='', min_value=1, max_value=5, value=3, on_change=record_question_10, key='question_10_slider')

        st.button(label='Submit and go to next image', on_click=annotate)
        st.markdown('[Back to Top](#annotation)')
    else:
        st.info("Everything annotated.")

def put_name():
    state.name = state.name_text_box

if state.name is None:
    st.header('Interactive image descriptioning annotation')
    st.markdown('Please enter your first name in English:')
    st.text_input(label='**Name:**', on_change=put_name, key='name_text_box')
else:
    run_with_name()
