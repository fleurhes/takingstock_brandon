#!/usr/bin/env python
# coding: utf-8

# In[9]:


import numpy as np
import pandas as pd
import cv2
import mediapipe as mp
import face_recognition_models
import dlib
import os
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates
from time import time
import matplotlib.pyplot as plt
import imutils
from imutils import face_utils
import face_recognition
import shutil
from sys import platform
from pathlib import Path


# In[27]:


#set home location
home = str(Path.home())

# platform specific file folder (mac for michael, win for satyam)
if platform == "darwin":
    # OS X
    folder="Documents/projects-active/facemap_production/images1674272442.9258912"
elif platform == "win32":
    # Windows...
    folder="foobar"

folder = os.path.join(home,folder)


# In[11]:


face_recognition_model = face_recognition_models.face_recognition_model_location()
face_encoder = dlib.face_recognition_model_v1(face_recognition_model)


# In[12]:


landmark_points_68 = [162,234,93,58,172,136,149,148,152,377,378,365,397,288,323,454,389,71,63,105,66,107,336,
                  296,334,293,301,168,197,5,4,75,97,2,326,305,33,160,158,133,153,144,362,385,387,263,373,
                  380,61,39,37,0,267,269,291,405,314,17,84,181,78,82,13,312,308,317,14,87]
    
landmark_points_5_1 = [ 2, #bottom of nose tip
                     362, #left eye towards centre
                     263, #left eye away from centre
                     33,  #right eye away from centre
                     133 #right eye towards centre 
                    ]
landmark_points_5_2 = [ 2, #bottom of nose tip
                     263, #left eye away from centre
                     362, #left eye towards centre
                     133, #right eye towards centre 
                     33  #right eye away from centre
                    ]

landmark_points_5_3 = [ 263, #left eye away from centre
                       362, #left eye towards centre
                       33,  #right eye away from centre
                       133, #right eye towards centre
                        2 #bottom of nose tip 
                    ]


# In[13]:


mp_drawing = mp.solutions.drawing_utils

mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.7)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,min_detection_confidence=0.5)


# ### MP + Dlib utils
# 

# In[14]:


def dlib_detection(image, hog_face_detector, display = True):

    height, width, _ = image.shape
    output_image = image.copy()
    imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    start = time()
    results = hog_face_detector(imgRGB, 0)
    end = time()

    for bbox in results:
        x1 = bbox.left()
        y1 = bbox.top()
        x2 = bbox.right()
        y2 = bbox.bottom()
        cv2.rectangle(output_image, pt1=(x1, y1), pt2=(x2, y2), color=(0, 255, 0), thickness=width//200)  

    if display:
        cv2.putText(output_image, text='Time taken: '+str(round(end - start, 2))+' Seconds.', org=(10, height//10),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=width//700, color=(0,0,255), thickness=width//500)
        plt.figure(figsize=[15,15])
        plt.subplot(121);plt.imshow(image[:,:,::-1]);plt.title("Original Image");plt.axis('off');
        plt.subplot(122);plt.imshow(output_image[:,:,::-1]);plt.title("Output");plt.axis('off');

    else:
        return output_image, results
    
def mp_detection(face_detection,image, display = True):
    height, width, _ = image.shape
    output_image =  image.copy()
    start = time()
    results = face_detection.process( image[:,:,::-1])
    end = time()
    bbox_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255),thickness=30)
    keypoint_drawing_spec=mp_drawing.DrawingSpec(color=(255, 0, 0),thickness=50,circle_radius=1)
    if results.detections:
        for face_no, face in enumerate(results.detections):
            #mp_drawing.draw_detection(image=output_image, detection=face,bbox_drawing_spec=bbox_drawing_spec,keypoint_drawing_spec=keypoint_drawing_spec)
            mp_drawing.draw_detection(image=output_image, detection=face,bbox_drawing_spec=bbox_drawing_spec)
    if display:
        cv2.putText(output_image, text='Time taken: '+str(round(end - start, 2))+' Seconds.', org=(10, height//10),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=width//700, color=(0,0,255), thickness=width//500)
        plt.figure(figsize=[15,15])
        plt.subplot(121);plt.imshow( image[:,:,::-1]);plt.title("Original Image");plt.axis('off');
        plt.subplot(122);plt.imshow(output_image[:,:,::-1]);plt.title("Output");plt.axis('off');

    else:
        return output_image, results
    
def mp_landmark(face_mesh,image, display = True):
    height, width, _ = image.shape
    output_image =  image.copy()
    start = time()
    results = face_mesh.process( image[:,:,::-1])
    end = time()
    if results.multi_face_landmarks:
        for facial_landmarks in results.multi_face_landmarks:
            for i in landmark_points_5_3:                    ######### CORRECTION: landmark_points_5_3 is the correct one for sure
                pt1 = facial_landmarks.landmark[i]
                x = int(pt1.x * width)
                y = int(pt1.y * height)
                cv2.circle(output_image, (x, y), 30, (0, 255, 0), -1)
    if display:
        cv2.putText(output_image, text='Time taken: '+str(round(end - start, 2))+' Seconds.', org=(10, height//10),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=width//700, color=(0,0,255), thickness=width//500)
        plt.figure(figsize=[15,15])
        plt.subplot(121);plt.imshow( image[:,:,::-1]);plt.title("Original Image");plt.axis('off');
        plt.subplot(122);plt.imshow(output_image[:,:,::-1]);plt.title("Output");plt.axis('off');
    else:
        return output_image, results
    
def dlib_landmark(hog_face_detector,image, display = True):
    height, width, _ = image.shape
    predictor = dlib.shape_predictor("shape_predictor_5_face_landmarks.dat")
    gray = cv2.cvtColor(sample_img, cv2.COLOR_BGR2GRAY)
    output_image = sample_img.copy()
    # detect faces in the grayscale image
    start = time()
    results = hog_face_detector(gray, 1)
    end = time()
    # loop over the face detections
    for (i, rect) in enumerate(results):
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        j=0
        for (x, y) in shape:
            j+=1
            cv2.circle(output_image, (x, y), 30, (0, 0, 255), -1)
            cv2.putText(output_image,str(j), (x, y),fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=width//1000, color=(0,0,0), thickness=width//500)
            
    if display:
        cv2.putText(output_image, text='Time taken: '+str(round(end - start, 2))+' Seconds.', org=(10, height//10),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=width//700, color=(0,0,255), thickness=width//500)
        plt.figure(figsize=[15,15])
        plt.subplot(121);plt.imshow( image[:,:,::-1]);plt.title("Original Image");plt.axis('off');
        plt.subplot(122);plt.imshow(output_image[:,:,::-1]);plt.title("Output");plt.axis('off');
    else:
        return output_image, results
    
def landmark_pt_list(mesh_results,width,height):
        ## function for return 5 landmarks in a dlib usable datatype

    if mesh_results.multi_face_landmarks:
        for i,face_landmarks in enumerate(mesh_results.multi_face_landmarks): 
            if i==0:
                raw_landmark_set = []
                for index in landmark_points_5_3:                       ######### CORRECTION: landmark_points_5_3 is the correct one for sure
                    x = int(face_landmarks.landmark[index].x * width)
                    y = int(face_landmarks.landmark[index].y * height)
                    landmark_point=dlib.point([x,y])
                    raw_landmark_set.append(landmark_point)
                all_points=dlib.points(raw_landmark_set)
#         return dlib.points([{
#             "nose_tip": [raw_landmark_set[0]],
#             "left_eye": raw_landmark_set[1:3],
#             "right_eye": raw_landmark_set[3:],
#             }])
        return all_points

def mp_bounding_rect(detection_results,width,height):
        #function for returning the bounding box in a dlib usable datatype

    if detection_results.detections:
        for i,detection in enumerate(detection_results.detections):
            if i==0:
                # bbox data
                bbox = detection.location_data.relative_bounding_box
                xy_min = _normalized_to_pixel_coordinates(bbox.xmin, bbox.ymin, height,width)
                xy_max = _normalized_to_pixel_coordinates(bbox.xmin + bbox.width, bbox.ymin + bbox.height,height,width)
                if xy_min is None or xy_max is None:return
                else:
                    xmin,ymin =xy_min
                    xmax,ymax = xy_max
                    rectangle= dlib.rectangle(left=xmin, top=ymax, right=xmax, bottom=ymin)
                    return rectangle
                
def ret_encoding(filepath,num_jitters=1):
        ##function for returning the encodings

    image_input = cv2.imread(filepath)
    image_input = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
    #image_input =face_recognition.load_image_file(filepath)
    height,width=image_input.shape[:-1]           ######## CORRECTION : height and width interchanged
    
    mesh_results = face_mesh.process(image_input)            #### mediapipe facial landmarks
    all_points=  landmark_pt_list(mesh_results,width,height) 
    
    detection_results = face_detection.process(image_input) ######mediapipe face detection
    b_box=mp_bounding_rect(detection_results,width,height)

#     _,detection_results=dlib_detection(image_input, hog_face_detector, display = False) ## dlib face detection
#     b_box=detection_results[0]
    
    if (all_points is None) or (b_box is None):return 
    raw_landmark_set=dlib.full_object_detection(b_box,all_points)
    encodings=face_encoder.compute_face_descriptor(image_input, raw_landmark_set, num_jitters)
    return encodings


# ### Linear sorting

# In[15]:


def get_img_list(folder):
    img_list=[]
    for file in os.listdir(folder):
        if not file.startswith('.') and os.path.isfile(os.path.join(folder, file)):
            filepath = os.path.join(folder, file)
            filepath=filepath.replace('\\' , '/')
            img_list.append(file)
    return img_list        
    print("got image list")
    
def save_sorted(folder, image, counter, dist):
    sorted_name = "linear_sort_"+str(counter)+"_"+str(round(dist, 2))+".jpg"
    sortfolder="sorted2"
    newfolder = os.path.join(folder,sortfolder)
    print(newfolder)
    old_name=os.path.join(folder,image)
    new_name=os.path.join(newfolder,sorted_name)
    print(old_name)
    print(new_name)
    if not os.path.exists(newfolder):
        os.makedirs(newfolder)
    shutil.copy(old_name, new_name)
    print('saved, ',sorted_name)


# In[16]:


#get distance beetween encodings

def get_d(enc1, enc2):
    enc1=np.array(enc1)
    enc2=np.array(enc2)
    d=np.linalg.norm(enc1 - enc2, axis=0)
    return d


# ### dataframe creation and sorting

# In[17]:


def encode_list_df(folder, img_list):
#     enc_dict={}
    csv_name="face_encodings.csv"
    col1="file_name"
    col2="encoding"
    curr=0
    total = len(img_list)

    # encodings column list for splitting
    col_list=[]
    for i in range(128):
        col_list.append(col2+str(i))

    #initializing the dataframe
    image_data=pd.DataFrame(columns=[col1, col2])

    
    for img in img_list:
        if curr%10==0:print(curr,"/",total)
        curr+=1
        filepath = os.path.join(folder,img)        
        filepath=filepath.replace('\\' , '/')  ## cv2 accepts files with "/" instead of "\"
        encodings=ret_encoding(filepath)
        if encodings is not None:              ## checking if a face is found
            
            data=pd.DataFrame({col1:img,col2:[np.array(encodings)]})
            image_data = pd.concat([image_data,data],ignore_index=True)  

    #splitting the encodings column
    output_data = pd.DataFrame(image_data[col2].to_list(), columns=col_list)
    #adding the filename column and then puting it first
    output_data[[col1]]=pd.DataFrame(image_data[col1].tolist(),index=image_data.index)
    clms = output_data.columns.tolist()
    clms = clms[-1:] + clms[:-1]
    output_data=output_data[clms]
    # saving without index
    output_data.to_csv(csv_name, index=False)
    df = pd.read_csv(csv_name)
    
    return output_data


# In[18]:


def get_closest_df(folder, start_img, df_enc):
    if start_img == "median":
        enc1 = df_enc.median().to_list()
#         print("in median")
    else:
#         enc1 = get 2-129 from df via stimg key
        enc1 = df_enc.loc[start_img].to_list()
        df_enc=df_enc.drop(start_img)
#         print("in new img",len(df_enc.index))
    
#     img_list.remove(start_img)
#     enc1=enc_dict[start_img]
    
    dist=[]
    dist_dict={}
    for index, row in df_enc.iterrows():
#         print(row['c1'], row['c2'])
#     for img in img_list:
        enc2 = row
        if (enc1 is not None) and (enc2 is not None):
            d = get_d(enc1, enc2)
            dist.append(d)
            dist_dict[d]=index
    dist.sort()
#     print(len(dist))
    return dist[0], dist_dict[dist[0]], df_enc


# In[19]:


# test if new and old make a face
def is_face(image):
    # For static images:
    # I think this list is not used
    IMAGE_FILES = []
    with mp_face_detection.FaceDetection(model_selection=1, 
                                        min_detection_confidence=0.6
                                        ) as face_detection:
        # image = cv2.imread(file)
        # Convert the BGR image to RGB and process it with MediaPipe Face Detection.
#         detection_results = face_detection.process(image)

        results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # Draw face detections of each face.
        if not results.detections:
            is_face = False
        else:
            is_face = True
        # annotated_image = image.copy()
        # for detection in results.detections:
        #     is_face = True
        #     print('Nose tip:')
        #     print(mp_face_detection.get_key_point(
        #       detection, mp_face_detection.FaceKeyPoint.NOSE_TIP))
        #     mp_drawing.draw_detection(annotated_image, detection)
        # cv2.imwrite('/tmp/annotated_image' + str(idx) + '.png', annotated_image)

        return is_face


# In[20]:


# test if new and old make a face
def test_pair(last_file, new_file):
    try:
        img = cv2.imread(new_file)
        height, width, layers = img.shape
        size = (width, height)
        print('loaded img 1')
        
        last_img = cv2.imread(new_file)
        last_height, last_width, last_layers = last_img.shape
        last_size = (last_width, last_height)
        print('loaded img 2')
        
        # test to see if this is actually an face, to get rid of blank ones/bad ones
        if is_face(img):
            print('new file is face')
            # if not the first image
#             if i>0:
            # blend this image with the last image
            blend = cv2.addWeighted(img, 0.5, last_img, 0.5, 0.0)
            print('blended faces')
            blended_face = is_face(blend)
            print('is_face ',blended_face)
            # if blended image has a detectable face, append the img
            if blended_face:
#                     img_array.append(img)
                print('is a face! adding it')
                return True
            else:
                print('skipping this one')
                return False
            # for the first one, just add the image
            # this may need to be refactored in case the first one is bad?
#             else:
#                 print('this is maybe the first round?')
#                 img_array.append(img)
        else:
            print('new_file is not face: ',new_file)
            return False

#         i+=1

    except:
        print('failed:',new_file)
        return False


# In[28]:


img_list = get_img_list(folder)
# start_img = img_list[1]
start_img = "median"

# enc_dict = encode_list(folder, img_list)
df_enc = encode_list_df(folder, img_list)

df_enc.set_index('file_name', inplace=True)

# print(df_enc.median().to_list())

#with lists/dicts
# dist=0
# for i in range(len(img_list)-1):
#     save_sorted(folder, start_img, i, dist)
#     dist, start_img = get_closest(folder, start_img,img_list, enc_dict)
    
#     print(dist)
#     print (start_img)
    
#     if dist > .37: 
#         continue


#with df
dist=0
print(len(df_enc.index))

for i in range(len(df_enc.index)-2):
    dist, start_img, df_enc = get_closest_df(folder, start_img,df_enc)
#     print(folder, start_img, i, dist)
    save_sorted(folder, start_img, i, dist)
    print(i)
    print(len(df_enc.index))
    print(dist)
    print (start_img)

# this maybe isn't working right?        
#     if dist > .37: 
#         break
        

# I don't know why, but this isn't working
# for i in range(len(df_enc.index)-2):
#     dist, start_img, df_enc = get_closest_df(folder, start_img,df_enc)
# #     print(folder, start_img, i, dist)
#     save_sorted(folder, start_img, i, dist)

#     if i>0:
#         #test blend
# #         last_file = os.path.join(folder,)
#         blend_is_face = (test_pair(os.path.join(folder,last_img), os.path.join(folder,start_img)))
#         print('blend_is_face ',blend_is_face)
#         if blend_is_face:
# #         print(test_pair(last_img,start_img))
#             save_sorted(folder, start_img, i, dist)
#             last_img = start_img
# #         else:
# #             start_img = last_img
            
#     print(i)
#     print(len(df_enc.index))
#     print(dist)
#     print (start_img)
    
#     if dist > .37: 
#         break

       

    


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:



