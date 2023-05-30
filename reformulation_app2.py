import streamlit as st
import random
import json
from collections import defaultdict
import gspread
import time

# First, we need a utility function to count how many annotations we have for each image;
# we'll use it later to find unannoated images
# This function assumes that state.ws is the google sheet worksheet which is already initialized
def create_image_to_sources():
    image_id_list = state.ws.col_values(2)[1:]
    source_list = state.ws.col_values(3)[1:]
    res = defaultdict(list)
    for i in range(len(image_id_list)):
        image_id = int(image_id_list[i])
        source = source_list[i]
        res[image_id].append(source)
    return res

# Initalize
state = st.session_state

# Each new time someone enters the app, the state is re initialized. So we need to reload the worksheet and data
if 'ws' not in state:
    # Reload the worksheet
    # 1. First, credentials. To reproduce follow the instructions in https://docs.gspread.org/en/latest/oauth2.html,
    # in the "For Bots: Using Service Account" section
    credentials = {'type': 'service_account', 'project_id': 'interactive-image-captioning', 'private_key_id': '12035110982ce28b4c91e02e3c314fb7ba7009af', 'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC9uve5nFEq/ATM\nBIWH8ds1h/xNFC4eqcWYWkFgKr8Nb/BYJOnB4EAwxDe0QCJNGrEEouHNHJWG7W/2\n4OYjtCUdI0d9qxZx9hpIggA5O+aiBHf1iHZTVQlhZic3U/Dut92ryAauovQtbk43\nW7dTo/LhDeWjpsvwSnqBVzZ1tGLxLhVt/4mRECO0/auxYyv+Dq+caZa5IzQ5b4uz\nlKwp1cwrNeOHVPbuZ5DWhadyI/KDplenKXs1+fr91/ZIQEkWaxjcV8Zl6qDFTuQq\nhSVqS53X8hjUcrzRxqjrYEdNk/bGcT0naLLV0HSWoNXnDyw984IU86Nw4zag0nXT\ni34YXjPXAgMBAAECggEAA6imAyWMJjjSTL4SwZ1gj3a2hKxbt4/HZLX6RkyK2Vp8\n+SnxTfSW1XvMngZc8gjDNQZUCMM10oGGQ/y0D6/ZIBTmJOucAFDW8MxPlHCe3iWR\n6fCHzq3SuBMfHl0GVQ938eEbb2ku03OTSFQCwEYbZ3h4QQoTDRW/xydXOPzN1y8F\ngkTccQGGty2OZ8fSUKTZZbMYRYVrQulhJr/DZZtudhstZMLoT97NokX0DJ6PL/dT\n+Pn+cnkK1ri+fo2CIY38Rf7UXfDsURlzGJVmbIqTQJT97ekelW4r37NJ4kqypzvj\nFiZPIqUskx/ILTp2ZhWg+5P2wtAKvyFQD8L4mW5mMQKBgQDr8UOh7+HSo0irLBCF\nrF4dxZybpEO+P/t/grJbt7GfHmReuzVQtScYOliI/1YuImJJNO1bAcZCkKkYST0e\nTmGZnzbcooojLcnY1rbQ8zoKE7JRvPcFnacmuPDevkYGEzsGMjR56BPbi5FkxIB+\n3Ezuckl+VlKh4B4DQbut4FptiQKBgQDN3AFVkzkGfeDpLpfYo25cKCFPppByapEA\nPNo0w1rdfXGF9CI+cFYyo9BslIUZYmmdKltRTr7W/UaYLAcdlBMitWFxxmd69Dtz\nmm9Eqlce8/fTLoFxLF5AoRt0QBGvD4Ru55N/tviPBYfndrFa1Cm29UWwoSDYaJ1y\nrHWsLU2eXwKBgQDS5IUycutjzqV+stVV1lsNu3ufNvWCUUhokhcAmjH+6ziF4Eno\niPOX2VcXpTuP4xX9H3zlMrHW/9zVI2mo9CCTItfz4Kkehqf71Pf1zuJa7X4fR4t5\nDpDAsOBECMkoVvoUML3tFT7ip17fNjEws5NkMu10Ko6TuHK7MH8kDPxnGQKBgD0N\nzAOCV35aZRMjc3uX9Qo2CLMj1mFow7qLUbgmXFOmeb3dyy4ziQ0Z0p3xaow9yM8J\nGe5CaY0/rulA3ZdjLE2198GTs2se9mbx3aBC2PXgK5chithy7T1Dyu2udtAxzPhL\njE5riMp6PHVkmXMzy29szQ92qlQkqtWw2nGHOicHAoGBAMNPgiAhkfdMoidINmHZ\n4R3IqNVmMWCVhZj/wyy+eHAL1Oj0ZjLMTIKJHiHHxV3D0/irVOKZOMY2bJvk7QgA\nlLPR6hQZHAaMSc17AhpG8/qEp6gSRJKHGfXvJgPgtpn2Hl0c+BhLndWfAHFpJjOt\nKBjtLr/KH18j3C9ZexhuSxMC\n-----END PRIVATE KEY-----\n', 'client_email': 'interactive-image-captioning@interactive-image-captioning.iam.gserviceaccount.com', 'client_id': '116699025089117232662', 'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token', 'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs', 'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/interactive-image-captioning%40interactive-image-captioning.iam.gserviceaccount.com'}
    gc = gspread.service_account_from_dict(credentials)
    # 2. Load the sheet
    sh = gc.open("annotation_pilot")
    # 3. Open the specific worksheet
    state.ws = sh.worksheet('Sheet1')

    # Load the data needs to be annotated
    blip_data_file_name = 'reformulation_data/blip_coco_val.json'
    with open(blip_data_file_name, 'r') as fp:
        blip_data = json.load(fp)
        for i in range(len(blip_data)):
            blip_data[i]['source'] = 'blip'
    mplug_data_file_name = 'reformulation_data/mplug_coco_val.json'
    with open(mplug_data_file_name, 'r') as fp:
        mplug_data = json.load(fp)
        for i in range(len(mplug_data)):
            mplug_data[i]['source'] = 'mplug'
    clipcap_data_file_name = 'reformulation_data/clipcap_coco_val.json'
    with open(clipcap_data_file_name, 'r') as fp:
        clipcap_data = json.load(fp)
        for i in range(len(clipcap_data)):
            clipcap_data[i]['source'] = 'clipcap'
    all_data = blip_data + mplug_data + clipcap_data
    with open('reformulation_data/current_image_ids.json', 'r') as fp:
        current_image_ids = json.load(fp)
    current_image_ids_dict = {x: True for x in current_image_ids}
    state.data = [x for x in all_data if x['image_id'] in current_image_ids_dict]

    # Find samples which were not annotated (if such exists)
    image_to_sources = create_image_to_sources()
    state.unvisited_samples = [x for x in state.data if x['source'] not in image_to_sources[x['image_id']]]
    if len(state.unvisited_samples) > 0:
        state.current_sample = random.choice(state.unvisited_samples)

    # Initalization of other state arguments
    state.cur_page = 0

def next_page():
    state.cur_page += 1

def record_name():
    if len(state.first_name_box) == 0:
        st.markdown('**First name empty**')
    elif len(state.last_name_box) == 0:
        st.markdown('**Last name empty**')
    else:
        state.first_name = state.first_name_box
        state.last_name = state.last_name_box
        next_page()

def hello_page():
    st.header('Interactive image captioning annotation')
    st.markdown('Hello! Please enter your name')
    st.text_input('First name', key='first_name_box')
    st.text_input('Last name', key='last_name_box')

    st.button('Next', key='next_button0', on_click=record_name)

def examples_page():
    st.subheader('Instructions')
    st.markdown('In this task, you will be presented with images together with a textual image description. Your task is to reformulate the description so that (a) it is as similar as possible to the original and (b) all errors from the original descriptions are fixed (if any errors exist). If the original descriptions is too bad to fix, please write a completely new description.')
    st.markdown('Please press the buttons below and watch the examples before you start.')

    st.subheader('Examples')
    if 'buttons_pressed' not in state:
        state.buttons_pressed = []
        for _ in range(5):
            state.buttons_pressed.append(False)
    if st.button('See example 1: original description using an incorrect word', key='example_button1'):
        st.image('reformulation_images/examples/COCO_train2014_000000000025.jpg', width=350)
        st.markdown('**Original description:** An elephant eating from a tree top')
        st.markdown('**Reformulation:** A giraffe eating from a tree top')
        st.markdown('------------------')
        state.buttons_pressed[0] = True
    if st.button("See example 2: original description missing information", key='example_button2'):
        st.image('reformulation_images/examples/COCO_train2014_000000010948.jpg', width=350)
        st.markdown('**Original description:** A man and a woman')
        st.markdown('**Reformulation:** A man and a woman playing a video game')
        st.markdown('------------------')
        state.buttons_pressed[1] = True
    if st.button("See example 3: original description hallucinating", key='example_button3'):
        st.image('reformulation_images/examples/COCO_train2014_000000348204.jpg', width=350)
        st.markdown('**Original description:** Two sheep and a cow standing on a dirt road')
        st.markdown('**Reformulation:** Two sheep standing on a dirt road')
        st.markdown('------------------')
        state.buttons_pressed[2] = True
    if st.button("See example 4: original description is not fluent", key='example_button4'):
        st.image('reformulation_images/examples/COCO_train2014_000000528275.jpg', width=350)
        st.markdown('**Original description:** Several horses is grazing in the meadow')
        st.markdown('**Reformulation:** Several horses are grazing in the meadow')
        st.markdown('------------------')
        state.buttons_pressed[3] = True
    if st.button("See example 5: original description is too bad to fix", key='example_button5'):
        st.image('reformulation_images/examples/COCO_train2014_000000010728.jpg', width=350)
        st.markdown('**Original description:** A tennis player hitting the ball with a racket')
        st.markdown('**Reformulation:** A pizza sitting on a plate on a wooden table')
        state.buttons_pressed[4] = True

    all_true = True
    for pressed in state.buttons_pressed:
        if not pressed:
            all_true = False
    if all_true:
        st.button('Next page', key='next_button1', on_click=next_page)

def instruction_page():
    st.markdown('The image and description will be displayed on the screen, as follows: (this is just an example)')

    with st.expander("See example"):
        st.image('reformulation_images/examples/COCO_train2014_000000000025.jpg', width=350)
        caption = 'An elephant eating from a tree top'
        st.markdown('**Original description:** ' + caption)
        st.text_input('**Reformulation:**', value=caption, key='reformulation_box_demo')

    st.markdown('You are requested to edit the text in the **Reformulation** box and press enter once you finish.')

    st.button('Next', key='next_button2', on_click=next_page)

def notes_page():
    st.markdown('Some important notes:')
    st.markdown('1. The examples we showed you are not the only cases where the description needs to be reformulated. You might want to reformulate other cases as well, and the descision is yours to make.')
    st.markdown('2. If you finished or taking a break, please don\'t leave the application open; close it, and when you want to continue simply log in again.')

    st.button('Let\'s start!', key='start_button', on_click=next_page)

def annotation_page():
    # Next, this is the function that will be called whenever a user finish an annotation, that is, presses enter
    # in the annotation text box
    def annotate():
        annotation_time = time.time() - t
        reformulation = state.reformulation_box
        image_id = state.current_sample['image_id']

        # Update the google sheet
        # 1. Find in which row we need to put the new annotations
        next_row_ind = len(state.ws.col_values(1)) + 1
        # 2. Update the sheet
        state.ws.update('A' + str(next_row_ind), 'val')
        state.ws.update('B' + str(next_row_ind), str(image_id))
        state.ws.update('C' + str(next_row_ind), str(state.current_sample['source']))
        state.ws.update('D' + str(next_row_ind), state.current_sample['caption'])
        state.ws.update('E' + str(next_row_ind), reformulation)
        state.ws.update('F' + str(next_row_ind), str(annotation_time))
        state.ws.update('G' + str(next_row_ind), state.first_name + ' ' + state.last_name)

        state.action_history = []

        # Search for samples which were not annotated again
        image_to_sources = create_image_to_sources()
        state.unvisited_samples = [x for x in state.data if x['source'] not in image_to_sources[x['image_id']]]
        if len(state.unvisited_samples) > 0:
            state.current_sample = random.choice(state.unvisited_samples)

    # If we have un annotated samples, present to the user. Otherwise, state that everything is annotated
    if len(state.unvisited_samples) > 0:
        sample = state.current_sample

        image_name = 'reformulation_images/COCO_val2014_' + str(sample['image_id']).zfill(12) + '.jpg'
        st.image(image_name, width=350)
        st.markdown('**Original description:** ' + sample['caption'])
        st.text_input('**Reformulation:**', value=sample['caption'], key='reformulation_box', on_change=annotate)
        t = time.time()
    else:
        st.info("Everything annotated.")

if state.cur_page == 0:
    hello_page()
elif state.cur_page == 1:
    examples_page()
elif state.cur_page == 2:
    instruction_page()
elif state.cur_page == 3:
    notes_page()
elif state.cur_page == 4:
    annotation_page()
