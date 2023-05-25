import streamlit as st
import random
import json
from collections import defaultdict
import gspread

# First, we need a utility function to count how many annotations we have for each image;
# we'll use it later to find unannoated images
# This function assumes that state.ws is the google sheet worksheet which is already initialized
def create_image_to_count():
    image_id_list = state.ws.col_values(2)[1:]
    res = defaultdict(int)
    for image_id in image_id_list:
        res[int(image_id)] += 1
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
    data_file_name = 'data_example.json'
    with open(data_file_name, 'r') as fp:
        state.data = json.load(fp)

    # Find samples which were not annotated (if such exists)
    image_to_count = create_image_to_count()
    state.unvisited_samples = [x for x in state.data if image_to_count[x['image_id']] == 0]
    if len(state.unvisited_samples) > 0:
        state.current_sample = random.choice(state.unvisited_samples)

    # Initalization of other state arguments
    state.cur_page = 0
    state.caption_parts = None
    state.token_selected = None
    state.action_history = []

def get_lengths(word_list):
    word_spaces = [len(x) for x in word_list]
    accumulated_length = 0
    res = [[]]
    for space_len in word_spaces:
        if accumulated_length + space_len > 24:
            res.append([])
            accumulated_length = 0
        res[-1].append(space_len)
        accumulated_length += space_len
    return res

def next_page():
    state.cur_page += 1
    state.token_selected = None

def click_func(click_ind):
    state.token_selected = click_ind

def examples_page():
    st.header('Interactive image captioning annotation')
    st.subheader('Instructions')
    st.markdown('In this task, you will be presented with images together with a textual image description. Your task is to reformulate the description so that it (a) is as similar as possible to the original and (b) all errors from the original descriptions are fixed (if any errors exist). If the original descriptions is too bad to fix, please write a completely new description.')

    st.subheader('Examples')
    #st.image('http://images.cocodataset.org/train2017/000000000025.jpg', width=350)
    st.image('reformulation_images/COCO_train2014_000000000025.jpg', width=350)
    st.markdown('**Original description:** An elephant eating from a tree top')
    st.markdown('**Reformulation:** A giraffe eating from a tree top')
    st.markdown('------------------')
    # st.image('http://images.cocodataset.org/train2017/000000010948.jpg', width=350)
    st.image('reformulation_images/COCO_train2014_000000010948.jpg', width=350)
    st.markdown('**Original description:** A boy playing a card game')
    st.markdown('**Reformulation:** A man and a woman playing a video game')
    st.markdown('------------------')
    # st.image('http://images.cocodataset.org/train2017/000000010728.jpg', width=350)
    st.image('reformulation_images/COCO_train2014_000000010728.jpg', width=350)
    st.markdown('**Original description:** A tennis player hitting the ball with a racket **[Description too bad to fix]**')
    st.markdown('**Reformulation:** A pizza sitting on a plate on a wooden table')

    st.button('Next', key='next_button1', on_click=next_page)

def instruction_page1():
    st.markdown('The image and description will be displayed on the screen, as follows: (this is just an example)')

    with st.expander("See example"):
        st.image('reformulation_images/COCO_train2014_000000000025.jpg', width=350)
        caption = 'An elephant eating from a tree top'
        st.markdown('**Original description:** ' + caption)
        st.markdown('**Reformulation:**')
        caption_parts = caption.split()
        length_lists = get_lengths(caption_parts)
        cur_start = 0
        for length_list in length_lists:
            cols = st.columns([x for x in length_list])
            for i in range(cur_start, cur_start + len(length_list)):
                with cols[i - cur_start]:
                    st.button(caption_parts[i], key='token' + str(i), use_container_width=True)
            cur_start += len(length_list)

        st.markdown('------------------')

        st.text_input('Rewrite description', key='rewrite_caption')

        st.button(':blue[Finished]', key='finished')

    st.button('Next', key='next_button2', on_click=next_page)

def instruction_page2():
    # I have no idea why, but if I move from the first page to the second with the expander
    # open, the expander on the second page is open, and if I add the following line (which
    # doesn't seem to be related in any way) it solves the problem
    st.markdown('')

    st.markdown('Below the image and the description you can see the "Reformulation" section, where you see all the words of the description. If you click one of the words you will see all possible actions for this word. Try clicking one of the words in the following example:')
    with st.expander("See example"):
        st.image('reformulation_images/COCO_train2014_000000000025.jpg', width=350)
        caption = 'An elephant eating from a tree top'
        st.markdown('**Original description:** ' + 'caption')
        st.markdown('**Reformulation:**')
        caption_parts = caption.split()
        length_lists = get_lengths(caption_parts)
        cur_start = 0
        for length_list in length_lists:
            cols = st.columns([x for x in length_list])
            for i in range(cur_start, cur_start + len(length_list)):
                with cols[i - cur_start]:
                    st.button(caption_parts[i], key='token' + str(i), on_click=click_func, kwargs={'click_ind': i}, use_container_width=True)
            cur_start += len(length_list)

        st.markdown('------------------')
        if state.token_selected is not None:
            st.button(':blue[Remove word]', key='remove')
            st.text_input('Insert before', key='insert_before')
            st.text_input('Insert after', key='insert_after')
            st.text_input('Replace word', key='update_token')

        st.text_input('Rewrite description', key='rewrite_caption')

        st.button(':blue[Finished]', key='finished')

    st.markdown('As you can see in the example, after selecting a word you can remove it, add a new word before it, add a new word after it or replace it with another word.')
    
    st.button('Next', key='next_button3', on_click=next_page)

def instruction_page3():
    st.markdown('If the description is too bad to fix and you want to write your own description from scratch, use the "Rewrite description" box:')
    with st.expander("See example"):
        st.image('reformulation_images/COCO_train2014_000000000025.jpg', width=350)
        caption = 'An elephant eating from a tree top'
        st.markdown('**Original description:** ' + 'caption')
        st.markdown('**Reformulation:**')
        caption_parts = caption.split()
        length_lists = get_lengths(caption_parts)
        cur_start = 0
        for length_list in length_lists:
            cols = st.columns([x for x in length_list])
            for i in range(cur_start, cur_start + len(length_list)):
                with cols[i - cur_start]:
                    st.button(caption_parts[i], key='token' + str(i), on_click=click_func, kwargs={'click_ind': i}, use_container_width=True)
            cur_start += len(length_list)

        st.markdown('------------------')

        st.text_input(':red[Rewrite description]', key='rewrite_caption')

        st.button(':blue[Finished]', key='finished')
    st.markdown('Please use the "Rewrite description" box only when the description is too bad to fix. In all other cases reformulate the description by adding, removing or replacing words.')
    
    st.button('Next', key='next_button4', on_click=next_page)

def instruction_page4():
    # I have no idea why, but if I move from the third page to the fourth with the expander
    # open, the expander on the second page is open, and if I add the following line (which
    # doesn't seem to be related in any way) it solves the problem
    st.markdown('')

    st.markdown('When you finish reformulating, click the Finished button. The next image and description will then be presented to you.')
    with st.expander("See example"):
        st.image('reformulation_images/COCO_train2014_000000000025.jpg', width=350)
        caption = 'An elephant eating from a tree top'
        st.markdown('**Original description:** ' + 'caption')
        st.markdown('**Reformulation:**')
        caption_parts = caption.split()
        length_lists = get_lengths(caption_parts)
        cur_start = 0
        for length_list in length_lists:
            cols = st.columns([x for x in length_list])
            for i in range(cur_start, cur_start + len(length_list)):
                with cols[i - cur_start]:
                    st.button(caption_parts[i], key='token' + str(i), on_click=click_func, kwargs={'click_ind': i}, use_container_width=True)
            cur_start += len(length_list)

        st.markdown('------------------')

        st.text_input(':Rewrite description', key='rewrite_caption')

        st.button(':red[Finished]', key='finished')

    st.button('Let\'s start!', key='start_button', on_click=next_page)

def annotation_page():
    # Next, this is the function that will be called whenever a user finish an annotation, that is, presses enter
    # in the annotation text box
    def annotate():
        reformulation = ' '.join(state.caption_parts)
        image_id = state.current_sample['image_id']

        # Update the google sheet
        # 1. Find in which row we need to put the new annotations
        next_row_ind = len(state.ws.col_values(1)) + 1
        # 2. Update the sheet
        state.ws.update('A' + str(next_row_ind), 'train')
        state.ws.update('B' + str(next_row_ind), str(image_id))
        state.ws.update('C' + str(next_row_ind), state.current_sample['caption'])
        state.ws.update('D' + str(next_row_ind), reformulation)
        state.ws.update('E' + str(next_row_ind), ','.join(state.action_history))

        state.action_history = []

        # Search for samples which were not annotated again
        image_to_count = create_image_to_count()
        state.unvisited_samples = [x for x in state.data if image_to_count[x['image_id']] == 0]
        if len(state.unvisited_samples) > 0:
            state.current_sample = random.choice(state.unvisited_samples)
            state.caption_parts = state.current_sample['caption'].split()

    # If we have un annotated samples, present to the user. Otherwise, state that everything is annotated
    if len(state.unvisited_samples) > 0:
        sample = state.current_sample

        image_name = 'reformulation_images/COCO_train2014_' + str(sample['image_id']).zfill(12) + '.jpg'
        st.image(image_name, width=350)
        st.markdown('**Original description:** ' + sample['caption'])
        st.markdown('**Reformulation:**')
        if state.caption_parts is None:
            state.caption_parts = sample['caption'].split()

        def remove_token():
            state.caption_parts = [state.caption_parts[i] for i in range(len(state.caption_parts)) if i != state.token_selected]
            state.action_history.append('[remove] ' + str(state.token_selected))
            state.token_selected = None

        def add_token_before():
            state.caption_parts.insert(state.token_selected, state.insert_before)
            state.action_history.append('[add in ' + str(state.token_selected) + '] ' + state.insert_before)
            state.token_selected = None

        def add_token_after():
            state.caption_parts.insert(state.token_selected + 1, state.insert_after)
            state.action_history.append('[add in ' + str(state.token_selected + 1) + '] ' + state.insert_after)
            state.token_selected = None

        def update_token():
            state.caption_parts[state.token_selected] = state.update_token
            state.action_history.append('[replace ' + str(state.token_selected) + '] ' + state.update_token)
            state.token_selected = None

        def rewrite_caption():
            state.caption_parts = state.rewrite_caption.split()
            state.action_history.append('[rewrite description] ' + state.rewrite_caption)
            state.rewrite_caption = ''

        length_lists = get_lengths(state.caption_parts)
        cur_start = 0
        for length_list in length_lists:
            if len(length_list) > 0:
                cols = st.columns([x for x in length_list])
                for i in range(cur_start, cur_start + len(length_list)):
                    with cols[i - cur_start]:
                        st.button(state.caption_parts[i], on_click=click_func, kwargs={'click_ind': i}, key='token' + str(i), use_container_width=True)
                cur_start += len(length_list)

        st.markdown('------------------')
        if state.token_selected is not None:
            st.button(':blue[Remove word]', key='remove', on_click=remove_token)
            st.text_input('Insert before', key='insert_before', on_change=add_token_before)
            st.text_input('Insert after', key='insert_after', on_change=add_token_after)
            st.text_input('Replace word', key='update_token', on_change=update_token)

        st.text_input('Rewrite description', key='rewrite_caption', on_change=rewrite_caption)

        st.button(':blue[Finished]', key='finished', on_click=annotate)
    else:
        st.info("Everything annotated.")

if state.cur_page == 0:
    examples_page()
elif state.cur_page == 1:
    instruction_page1()
elif state.cur_page == 2:
    instruction_page2()
elif state.cur_page == 3:
    instruction_page3()
elif state.cur_page == 4:
    instruction_page4()
elif state.cur_page == 5:
    annotation_page()
