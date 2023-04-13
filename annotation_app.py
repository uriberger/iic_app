import streamlit as st
import random
import json
import pandas as pd
from collections import defaultdict

st.header('Interactive image captioning annotation')
st.subheader('Instructions')
st.markdown('Given the following images and a caption generated by an AI model, generate a "reformulation" of the caption by writing a similar caption in which the errors from the original caption (if such exists), are fixed. If the model generated caption is too bad to fix, write a new caption.')

st.subheader('Examples')
st.image('http://images.cocodataset.org/train2017/000000000025.jpg', width=350)
st.markdown('**Model generated caption:** An elephant eating from a tree top')
st.markdown('**Reformulation:** A giraffe eating from a tree top')
st.markdown('------------------')
st.image('http://images.cocodataset.org/train2017/000000010948.jpg', width=350)
st.markdown('**Model generated caption:** A boy playing a card game')
st.markdown('**Reformulation:** A man and a woman playing a video game')
st.markdown('------------------')
st.image('http://images.cocodataset.org/train2017/000000010728.jpg', width=350)
st.markdown('**Model generated caption:** A tennis player hitting the ball with a racket **[Caption too bad to fix]**')
st.markdown('**Reformulation:** A pizza sitting on a plate on a wooden table')

st.subheader('Annotation')

# Option 1: with a local file
# data_file_name = 'data_example.json'
# with open(data_file_name, 'r') as fp:
#     data = json.load(fp)

# reformulation = 'a'
# not_visited_inds = [i for i in range(len(data)) if len(data[i]['reformulations']) == 0]
# st.markdown('DEBUG ' + str(len(reformulation)))
# st.markdown('DEBUG ' + str(len(not_visited_inds)))
# while len(reformulation) > 0 and len(not_visited_inds) > 0:
#     reformulation = ''
#     sample_ind = random.sample(not_visited_inds, 1)[0]
#     sample = data[sample_ind]
#     url_prefix = 'http://images.cocodataset.org/'
#     url_prefix += sample['split'] + '2017/'
#     image_url = url_prefix + str(sample['image_id']).zfill(12) + '.jpg'
#     st.image(image_url, width=350)
#     st.markdown('**Model generated caption:** ' + sample['caption'])
#     reformulation = st.text_input(label='**Reformulation:**')

#     if len(reformulation) > 0:
#         st.markdown('DEBUG HERE')
#         data[sample_ind]['reformulations'].append(reformulation)
#         json_obj = json.dumps(data)
#         with open(data_file_name, 'w') as fp:
#             fp.write(json_obj)

# Option 2: with google sheets
# def load_data(sheets_url):
#     csv_url = sheets_url.replace("edit?usp=sharing", "gviz/tq?tqx=out:csv&sheet=Sheet1")
#     return pd.read_csv(csv_url)

# def create_image_to_count():
#     df = load_data(st.secrets["public_gsheets_url"])
#     image_id_list = df['image_id'].tolist()
#     res = defaultdict(int)
#     for image_id in image_id_list:
#         res[image_id] += 1
#     return res

# st.markdown('DEBUG ' + str(create_image_to_count()))

# df = pd.concat((df, pd.DataFrame({'split': ['train'], 'image_id': ['6666'], 'reformulation': ['A dog']})))

# Option 3: with streamlit state
state = st.session_state

if "annotations" not in state:
    data_file_name = 'data_example.json'
    with open(data_file_name, 'r') as fp:
        data = json.load(fp)

    state.annotations = {}
    state.samples = data
    state.current_sample = state.samples[0]

def annotate():
    reformulation = state.ref_text_box
    st.markdown('DEBUG in annotate with ' + reformulation)
    image_id = state.current_sample['image_id']
    if image_id not in state.annotations:
        state.annotations[image_id] = []
    state.annotations[image_id].append(reformulation)
    state.samples.remove(state.current_sample)
    if len(state.samples) > 0:
        state.current_sample = state.samples[0]

if len(state.samples) > 0:
    sample = state.current_sample

    url_prefix = 'http://images.cocodataset.org/'
    url_prefix += sample['split'] + '2017/'
    image_url = url_prefix + str(sample['image_id']).zfill(12) + '.jpg'
    st.image(image_url, width=350)
    st.markdown('**Model generated caption:** ' + sample['caption'])
    st.text_input(label='**Reformulation:**', on_change=annotate, key='ref_text_box')

else:
    st.info("Everything annotated.")

st.info(f"Annotated: {len(state.annotations)}, Remaining: {len(state.samples)}")

st.download_button(
    "Download annotations as CSV",
    "\n".join([f"{k}\t{v}" for k, v in state.annotations.items()]),
    file_name="export.csv",
)
